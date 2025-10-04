"""
Web可视化数据准备脚本
从数据库提取真实K线数据并运行模型获取预测数据，生成用于网页展示的JSON数据
"""

import numpy as np
import pandas as pd
import json
import pickle
import os
import sys
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import pymysql

# 添加父目录到路径以导入模型
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LSTMModel(nn.Module):
    """LSTM模型（与训练脚本相同的定义）"""

    def __init__(self, input_size, hidden_sizes, dropout_rate=0.2):
        super(LSTMModel, self).__init__()

        self.hidden_sizes = hidden_sizes
        self.num_layers = len(hidden_sizes)

        # 创建LSTM层
        self.lstm_layers = nn.ModuleList()

        # 第一层LSTM
        self.lstm_layers.append(
            nn.LSTM(input_size, hidden_sizes[0], batch_first=True)
        )

        # 后续LSTM层
        for i in range(1, len(hidden_sizes)):
            self.lstm_layers.append(
                nn.LSTM(hidden_sizes[i-1], hidden_sizes[i], batch_first=True)
            )

        # Dropout层
        self.dropout = nn.Dropout(dropout_rate)

        # 输出层
        self.fc = nn.Linear(hidden_sizes[-1], 1)

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)

        # 通过LSTM层
        for i, lstm in enumerate(self.lstm_layers):
            x, _ = lstm(x)
            if i < len(self.lstm_layers) - 1:
                # 对中间层应用dropout
                x = self.dropout(x)

        # 取最后一个时间步的输出
        x = x[:, -1, :]

        # 应用最后的dropout
        x = self.dropout(x)

        # 全连接层
        out = self.fc(x)

        return out


class WebDataGenerator:
    """Web可视化数据生成器"""

    def __init__(self, config_path='../lstm_config.json', model_dir='../models'):
        """初始化数据生成器"""
        # 获取脚本所在目录和父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        
        # 确保配置文件路径正确
        if not os.path.isabs(config_path):
            config_path = os.path.join(parent_dir, config_path.lstrip('../'))
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.db_type = self.config.get('db_type', 'mysql')
        db_config_file = self.config.get('db_config_file', 'config.json')
        
        # 确保数据库配置文件路径正确
        if not os.path.isabs(db_config_file):
            self.db_config_file = os.path.join(parent_dir, db_config_file)
        else:
            self.db_config_file = db_config_file
            
        self.table_name = self.config.get('table_name', 'kline_data_hour')
        
        # 确保模型目录路径正确
        if not os.path.isabs(model_dir):
            self.model_dir = os.path.join(parent_dir, model_dir.lstrip('../'))
        else:
            self.model_dir = model_dir

        # 加载数据库配置
        if self.db_type == 'mysql':
            with open(self.db_config_file, 'r', encoding='utf-8') as f:
                self.db_config = json.load(f)

        # 设置设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")

        # 加载模型
        model_path = os.path.join(model_dir, 'lstm_model_final.pth')
        if not os.path.exists(model_path):
            model_path = os.path.join(model_dir, 'lstm_best_model.pth')

        print(f"正在加载模型: {model_path}")
        checkpoint = torch.load(model_path, map_location=self.device)

        # 从检查点获取配置
        model_config = checkpoint['config']
        input_size = model_config['input_size']
        hidden_sizes = model_config['hidden_sizes']
        dropout_rate = model_config['dropout_rate']

        # 重建模型
        self.model = LSTMModel(input_size, hidden_sizes, dropout_rate)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()

        # 加载缩放器和配置
        scaler_path = os.path.join(model_dir, 'scalers.pkl')
        print(f"正在加载缩放器: {scaler_path}")
        with open(scaler_path, 'rb') as f:
            scaler_data = pickle.load(f)
            self.scaler_X = scaler_data['scaler_X']
            self.scaler_y = scaler_data['scaler_y']
            self.feature_columns = scaler_data['feature_columns']
            self.target_column = scaler_data['target_column']
            self.sequence_length = scaler_data['sequence_length']

        print("模型和缩放器加载完成!")

    def load_data(self, days_back=30):
        """加载指定天数的历史数据"""
        print(f"Loading data for the last {days_back} days...")

        if self.db_type == 'mysql':
            conn = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset=self.db_config['charset']
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        # 首先查询表结构来确定字段名
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {self.table_name}")
        columns_info = cursor.fetchall()
        available_columns = [col[0] for col in columns_info]
        cursor.close()
        
        print(f"Available columns: {available_columns}")
        
        # 确定K线数据字段名（兼容不同的命名方式）
        kline_mapping = {
            'open': 'open_price' if 'open_price' in available_columns else 'open',
            'high': 'high_price' if 'high_price' in available_columns else 'high', 
            'low': 'low_price' if 'low_price' in available_columns else 'low',
            'close': 'close_price' if 'close_price' in available_columns else 'close',
            'volume': 'volume' if 'volume' in available_columns else 'turnover'
        }
        
        # 构建查询字段列表
        feature_columns = ['timestamp'] + self.feature_columns
        query_columns = set(feature_columns)
        
        # 添加K线字段（使用AS来统一命名）
        kline_select_parts = []
        for standard_name, actual_name in kline_mapping.items():
            if actual_name in available_columns:
                if standard_name != actual_name:
                    kline_select_parts.append(f"{actual_name} AS {standard_name}")
                else:
                    kline_select_parts.append(standard_name)
                query_columns.discard(actual_name)  # 避免重复
        
        # 合并所有字段
        select_parts = list(query_columns) + kline_select_parts
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        start_timestamp = int(start_time.timestamp())
        
        query = f"""
        SELECT {', '.join(select_parts)} 
        FROM {self.table_name} 
        WHERE timestamp >= {start_timestamp}
        ORDER BY timestamp ASC
        """
        
        print(f"Query: {query}")
        df = pd.read_sql_query(query, conn)
        conn.close()

        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # 删除包含NaN的行
        df.dropna(inplace=True)

        print(f"Loaded {len(df)} records")
        print(f"Time range: {df.index.min()} to {df.index.max()}")

        return df

    def generate_predictions(self, df):
        """为数据生成预测结果"""
        print("Generating predictions for all data points...")

        # 创建特征列名映射（处理重命名后的字段）
        feature_columns_mapped = []
        for col in self.feature_columns:
            if col == 'open_price' and 'open' in df.columns:
                feature_columns_mapped.append('open')
            elif col == 'high_price' and 'high' in df.columns:
                feature_columns_mapped.append('high')
            elif col == 'low_price' and 'low' in df.columns:
                feature_columns_mapped.append('low')
            elif col == 'close_price' and 'close' in df.columns:
                feature_columns_mapped.append('close')
            elif col in df.columns:
                feature_columns_mapped.append(col)
            else:
                print(f"Warning: Feature column '{col}' not found in dataframe")
        
        print(f"Using feature columns: {feature_columns_mapped}")
        print(f"Available columns in df: {list(df.columns)}")
        
        # 提取特征和目标
        X_data = df[feature_columns_mapped].values
        
        # 处理目标列名
        target_column_mapped = self.target_column
        if self.target_column == 'close_price' and 'close' in df.columns:
            target_column_mapped = 'close'
        elif self.target_column not in df.columns:
            print(f"Warning: Target column '{self.target_column}' not found, available columns: {list(df.columns)}")
            # 尝试找到合适的目标列
            if 'close' in df.columns:
                target_column_mapped = 'close'
            elif 'close_price' in df.columns:
                target_column_mapped = 'close_price'
        
        y_data = df[target_column_mapped].values.reshape(-1, 1)

        # 标准化
        X_scaled = self.scaler_X.transform(X_data)
        y_scaled = self.scaler_y.transform(y_data)

        # 创建序列数据和预测
        predictions = []
        valid_indices = []

        for i in range(len(X_scaled) - self.sequence_length + 1):
            X_seq = X_scaled[i:i+self.sequence_length]
            valid_indices.append(i + self.sequence_length - 1)

            # 预测
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_seq).unsqueeze(0).to(self.device)
                y_pred_scaled = self.model(X_tensor)
                y_pred_scaled = y_pred_scaled.cpu().numpy().flatten()[0]

                # 反标准化
                y_pred = self.scaler_y.inverse_transform([[y_pred_scaled]])[0][0]
                predictions.append(y_pred)

        print(f"Generated {len(predictions)} predictions")
        return predictions, valid_indices

    def create_kline_data(self, df, predictions, valid_indices):
        """创建K线图所需的数据格式"""
        print("Creating K-line data structure...")

        # 确定目标列名
        target_column_mapped = self.target_column
        if self.target_column == 'close_price' and 'close' in df.columns:
            target_column_mapped = 'close'
        elif self.target_column not in df.columns:
            if 'close' in df.columns:
                target_column_mapped = 'close'
            elif 'close_price' in df.columns:
                target_column_mapped = 'close_price'

        # 真实K线数据
        real_kline = []
        for idx, row in df.iterrows():
            # 获取OHLC数据，如果没有则使用目标列的值作为默认值
            close_price = float(row[target_column_mapped])
            open_price = float(row.get('open', close_price))
            high_price = float(row.get('high', close_price))
            low_price = float(row.get('low', close_price))
            volume = float(row.get('volume', 0))
            
            real_kline.append({
                'timestamp': int(idx.timestamp() * 1000),  # 转换为毫秒时间戳（JS格式）
                'datetime': idx.strftime('%Y-%m-%d %H:%M:%S'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })

        pred_kline = []
        for i, (pred_price, data_idx) in enumerate(zip(predictions, valid_indices)):
            timestamp = df.index[data_idx]
            real_close = df.iloc[data_idx][target_column_mapped]

            # 确定开盘价：首条使用真实收盘作为衔接，后续使用上一次预测的收盘
            if i == 0:
                pred_open = real_close
            else:
                # use previous predicted close to avoid anchoring to real future values
                pred_open = pred_kline[-1]['close']

            price_diff = pred_price - pred_open
            pred_high = max(pred_open, pred_price) + abs(price_diff) * 0.1
            pred_low = min(pred_open, pred_price) - abs(price_diff) * 0.1

            pred_kline.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(pred_open),
                'high': float(pred_high),
                'low': float(pred_low),
                'close': float(pred_price),
                'volume': float(df.iloc[data_idx].get('volume', 0)),
                'error': float(pred_price - real_close),
                'error_pct': float((pred_price - real_close) / real_close * 100)
            })

        return real_kline, pred_kline

    def calculate_error_statistics(self, df, predictions, valid_indices):
        """计算预测误差统计"""
        print("Calculating error statistics...")

        # 确定目标列名
        target_column_mapped = self.target_column
        if self.target_column == 'close_price' and 'close' in df.columns:
            target_column_mapped = 'close'
        elif self.target_column not in df.columns:
            if 'close' in df.columns:
                target_column_mapped = 'close'
            elif 'close_price' in df.columns:
                target_column_mapped = 'close_price'

        errors = []
        for pred_price, data_idx in zip(predictions, valid_indices):
            real_price = df.iloc[data_idx][target_column_mapped]
            error = pred_price - real_price
            error_pct = (error / real_price) * 100
            
            timestamp = df.index[data_idx]
            errors.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'real_price': float(real_price),
                'pred_price': float(pred_price),
                'error': float(error),
                'error_pct': float(error_pct),
                'abs_error': float(abs(error)),
                'abs_error_pct': float(abs(error_pct))
            })

        # 计算统计指标
        error_values = [e['error'] for e in errors]
        error_pct_values = [e['error_pct'] for e in errors]
        abs_error_values = [e['abs_error'] for e in errors]
        abs_error_pct_values = [e['abs_error_pct'] for e in errors]

        statistics = {
            'total_predictions': len(errors),
            'mae': float(np.mean(abs_error_values)),
            'mse': float(np.mean([e**2 for e in error_values])),
            'rmse': float(np.sqrt(np.mean([e**2 for e in error_values]))),
            'mape': float(np.mean(abs_error_pct_values)),
            'mean_error': float(np.mean(error_values)),
            'std_error': float(np.std(error_values)),
            'min_error': float(np.min(error_values)),
            'max_error': float(np.max(error_values)),
            'median_error': float(np.median(error_values)),
            'direction_accuracy': float(self.calculate_direction_accuracy(df, predictions, valid_indices))
        }

        return errors, statistics

    def calculate_direction_accuracy(self, df, predictions, valid_indices):
        """计算方向预测准确率"""
        if len(predictions) < 2:
            return 0.0

        # 确定目标列名
        target_column_mapped = self.target_column
        if self.target_column == 'close_price' and 'close' in df.columns:
            target_column_mapped = 'close'
        elif self.target_column not in df.columns:
            if 'close' in df.columns:
                target_column_mapped = 'close'
            elif 'close_price' in df.columns:
                target_column_mapped = 'close_price'

        correct_directions = 0
        total_directions = 0

        for i in range(1, len(predictions)):
            current_idx = valid_indices[i]
            prev_idx = valid_indices[i-1]
            
            # 真实价格变化方向
            real_current = df.iloc[current_idx][target_column_mapped]
            real_prev = df.iloc[prev_idx][target_column_mapped]
            real_direction = 1 if real_current > real_prev else -1

            # 预测价格变化方向
            pred_current = predictions[i]
            pred_prev = predictions[i-1]
            pred_direction = 1 if pred_current > pred_prev else -1

            if real_direction == pred_direction:
                correct_directions += 1
            total_directions += 1

        return (correct_directions / total_directions) * 100 if total_directions > 0 else 0.0

    def generate_web_data(self, days_back=30, output_dir='data'):
        """生成完整的Web可视化数据"""
        print("="*60)
        print("Web Visualization Data Generation")
        print("="*60)

        # 加载数据
        df = self.load_data(days_back)

        # 生成预测
        predictions, valid_indices = self.generate_predictions(df)

        # 创建K线数据
        real_kline, pred_kline = self.create_kline_data(df, predictions, valid_indices)

        # 计算误差统计
        errors, statistics = self.calculate_error_statistics(df, predictions, valid_indices)

        # 准备输出数据
        web_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period_days': days_back,
                'total_records': len(df),
                'total_predictions': len(predictions),
                'sequence_length': self.sequence_length,
                'target_column': self.target_column,
                'feature_columns': self.feature_columns
            },
            'real_kline': real_kline,
            'predicted_kline': pred_kline,
            'errors': errors,
            'statistics': statistics
        }

        # 保存数据
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存完整数据
        full_data_path = os.path.join(output_dir, 'kline_comparison_data.json')
        with open(full_data_path, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, indent=2, ensure_ascii=False)
        print(f"Full data saved to: {full_data_path}")

        # 保存简化数据（用于快速加载）
        simplified_data = {
            'metadata': web_data['metadata'],
            'real_kline': real_kline[-1000:],  # 只保留最近1000条
            'predicted_kline': pred_kline[-1000:],
            'statistics': statistics
        }
        
        simplified_path = os.path.join(output_dir, 'kline_simplified_data.json')
        with open(simplified_path, 'w', encoding='utf-8') as f:
            json.dump(simplified_data, f, indent=2, ensure_ascii=False)
        print(f"Simplified data saved to: {simplified_path}")

        # 打印统计信息
        print("\n" + "="*60)
        print("Data Generation Summary")
        print("="*60)
        print(f"Data period: {df.index.min()} to {df.index.max()}")
        print(f"Total records: {len(df)}")
        print(f"Total predictions: {len(predictions)}")
        print(f"MAE: {statistics['mae']:.6f}")
        print(f"RMSE: {statistics['rmse']:.6f}")
        print(f"MAPE: {statistics['mape']:.2f}%")
        print(f"Direction Accuracy: {statistics['direction_accuracy']:.2f}%")
        print("="*60)

        return web_data


def main():
    """主函数"""
    generator = WebDataGenerator()
    
    # 生成最近30天的数据
    web_data = generator.generate_web_data(days_back=30)
    
    print("\nWeb visualization data generation completed!")
    print("Use the generated JSON files in your web interface.")


if __name__ == '__main__':
    main()