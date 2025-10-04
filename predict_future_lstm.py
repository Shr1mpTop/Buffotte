"""
LSTM模型未来预测脚本 (PyTorch版本)
使用训练好的模型预测未来的股价走势
"""

import numpy as np
import pandas as pd
import json
import pickle
import os
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import pymysql
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'


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


class LSTMFuturePredictor:
    """LSTM未来预测器"""

    def __init__(self, config_path='lstm_config.json', model_dir='models'):
        """初始化预测器"""
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.db_type = self.config.get('db_type', 'mysql')
        self.db_config_file = self.config.get('db_config_file', 'config.json')
        self.table_name = self.config.get('table_name', 'kline_data_hour')
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

    def load_latest_data(self, hours_back=200):
        """加载最新的数据用于预测"""
        print(f"正在加载最新的 {hours_back} 小时数据...")

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
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

        # 构建查询 - 获取最新的数据
        columns = ['timestamp'] + self.feature_columns
        if self.target_column not in columns:
            columns.append(self.target_column)

        query = f"SELECT {', '.join(columns)} FROM {self.table_name} ORDER BY timestamp DESC LIMIT {hours_back}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # 转换时间戳并排序
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('timestamp').set_index('timestamp')

        # 删除包含NaN的行
        df.dropna(inplace=True)

        print(f"加载了 {len(df)} 条最新记录")
        print(f"时间范围: {df.index.min()} 到 {df.index.max()}")

        return df

    def prepare_prediction_sequence(self, df):
        """准备用于预测的最新序列"""
        print("正在准备预测序列...")

        # 提取特征
        X_data = df[self.feature_columns].values

        # 标准化
        X_scaled = self.scaler_X.transform(X_data)

        # 取最新的sequence_length个数据点
        if len(X_scaled) < self.sequence_length:
            raise ValueError(f"数据不足：需要至少 {self.sequence_length} 个数据点，但只有 {len(X_scaled)} 个")

        latest_sequence = X_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)

        print(f"使用最新的 {self.sequence_length} 个数据点进行预测")

        return latest_sequence, df.index[-1]

    def predict_future(self, latest_sequence, last_timestamp, prediction_hours=24):
        """预测未来多个小时的数据"""
        print(f"正在预测未来 {prediction_hours} 小时的数据...")

        predictions = []
        prediction_timestamps = []

        current_sequence = latest_sequence.copy()

        for hour in range(prediction_hours):
            # 进行预测
            X_tensor = torch.FloatTensor(current_sequence).to(self.device)

            with torch.no_grad():
                y_pred_scaled = self.model(X_tensor)
                y_pred_scaled = y_pred_scaled.cpu().numpy()

            # 反标准化预测值
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled)[0][0]

            # 计算下一个时间戳
            next_timestamp = last_timestamp + timedelta(hours=hour+1)

            predictions.append(y_pred)
            prediction_timestamps.append(next_timestamp)

            # 为下一次预测更新序列
            # 注意：这里简化处理，使用预测值作为下一个输入的一部分
            # 在实际应用中，可能需要更复杂的特征工程
            if hour < prediction_hours - 1:
                # 创建新的特征向量（简化版）
                new_features = current_sequence[0, -1, :].copy()  # 复制最后一个时间步的特征

                # 更新close_price（假设其他特征保持不变）
                close_price_idx = self.feature_columns.index(self.target_column)
                new_features[close_price_idx] = y_pred_scaled[0][0]  # 使用标准化后的预测值

                # 将新特征添加到序列末尾，并移除最旧的
                new_sequence = np.roll(current_sequence[0], -1, axis=0)
                new_sequence[-1] = new_features
                current_sequence = new_sequence.reshape(1, self.sequence_length, -1)

            if (hour + 1) % 6 == 0:
                print(f"已预测 {hour + 1}/{prediction_hours} 小时")

        return prediction_timestamps, predictions

    def plot_predictions(self, historical_df, pred_timestamps, predictions, save_path=None):
        """绘制预测结果"""
        fig, ax = plt.subplots(figsize=(16, 8))

        # 绘制历史数据
        ax.plot(historical_df.index, historical_df[self.target_column],
                label='Historical Data', color='blue', linewidth=2, alpha=0.7)

        # 绘制预测数据
        ax.plot(pred_timestamps, predictions,
                label='Future Predictions', color='red', linewidth=2, linestyle='--', alpha=0.8)

        # 添加预测开始点的标记
        last_historical_time = historical_df.index[-1]
        last_historical_price = historical_df[self.target_column].iloc[-1]
        ax.scatter(last_historical_time, last_historical_price,
                  color='green', s=100, zorder=5, label='Prediction Start Point')

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.set_title('LSTM Future Price Prediction', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)

        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # 添加预测信息文本框
        info_text = f"""
        Prediction Info:
        • Historical data: {len(historical_df)} hours
        • Prediction horizon: {len(predictions)} hours
        • Model: LSTM ({len(self.model.hidden_sizes)} layers)
        • Prediction start: {last_historical_time.strftime('%Y-%m-%d %H:%M')}
        """

        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()

        if save_path is None:
            output_dir = 'predictions'
            os.makedirs(output_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(output_dir, f'future_predictions_{timestamp_str}.png')

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n预测图表已保存到: {save_path}")

        plt.show()

        return fig

    def save_predictions(self, historical_df, pred_timestamps, predictions):
        """保存预测结果"""
        output_dir = 'predictions'
        os.makedirs(output_dir, exist_ok=True)

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存预测结果
        pred_df = pd.DataFrame({
            'timestamp': pred_timestamps,
            'predicted_price': predictions
        })

        csv_path = os.path.join(output_dir, f'future_predictions_{timestamp_str}.csv')
        pred_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"预测结果已保存到: {csv_path}")

        # 保存历史数据和预测的组合
        combined_df = pd.DataFrame({
            'timestamp': list(historical_df.index) + pred_timestamps,
            'price': list(historical_df[self.target_column]) + predictions,
            'type': ['historical'] * len(historical_df) + ['predicted'] * len(predictions)
        })

        combined_csv_path = os.path.join(output_dir, f'combined_predictions_{timestamp_str}.csv')
        combined_df.to_csv(combined_csv_path, index=False, encoding='utf-8-sig')
        print(f"历史+预测数据已保存到: {combined_csv_path}")

        return pred_df

    def predict(self, prediction_hours=24, historical_hours=168):
        """执行未来预测"""
        print("="*60)
        print("LSTM Future Price Prediction")
        print("="*60)

        # 加载历史数据
        historical_df = self.load_latest_data(historical_hours)

        # 准备预测序列
        latest_sequence, last_timestamp = self.prepare_prediction_sequence(historical_df)

        # 进行未来预测
        pred_timestamps, predictions = self.predict_future(
            latest_sequence, last_timestamp, prediction_hours
        )

        # 打印预测结果
        print("\n" + "="*60)
        print("Future Predictions")
        print("="*60)
        for i, (ts, pred) in enumerate(zip(pred_timestamps, predictions)):
            print(f"{ts.strftime('%Y-%m-%d %H:%M')}: ¥{pred:.2f}")
            if (i + 1) % 6 == 0:
                print()

        # 生成可视化
        print("\n生成预测图表...")
        self.plot_predictions(historical_df, pred_timestamps, predictions)

        # 保存结果
        pred_df = self.save_predictions(historical_df, pred_timestamps, predictions)

        print("\n" + "="*60)
        print("预测完成!")
        print("="*60)

        return pred_timestamps, predictions


def main():
    """主函数"""
    # 可以调整预测参数
    prediction_hours = 24  # 预测未来24小时
    historical_hours = 168  # 使用过去7天的数据作为历史

    predictor = LSTMFuturePredictor()
    timestamps, predictions = predictor.predict(
        prediction_hours=prediction_hours,
        historical_hours=historical_hours
    )


if __name__ == '__main__':
    main()