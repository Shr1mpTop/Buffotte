"""
LSTM模型评估脚本 (PyTorch版本)
评估训练好的模型在测试集上的性能，并生成可视化结果
"""

import numpy as np
import pandas as pd
import json
import pickle
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import torch
import torch.nn as nn
import pymysql

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


class LSTMEvaluator:
    """LSTM模型评估器"""

    def __init__(self, config_path='lstm_config.json', model_dir='models'):
        """初始化评估器"""
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

    def load_test_data(self):
        """加载测试数据（与训练时相同的预处理）"""
        print("Loading test data...")

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

        # 构建查询
        columns = ['timestamp'] + self.feature_columns
        if self.target_column not in columns:
            columns.append(self.target_column)

        query = f"SELECT {', '.join(columns)} FROM {self.table_name} ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # 数据预处理：删除最早的6000条数据（与训练时相同）
        if len(df) > 13000:
            df = df.iloc[-13000:].copy()

        # 删除包含NaN的行
        df.dropna(inplace=True)

        print(f"Loaded {len(df)} test records")
        print(f"Time range: {df.index.min()} to {df.index.max()}")

        return df

    def prepare_test_sequences(self, df):
        """准备测试序列数据"""
        print("Preparing test sequences...")

        # 提取特征和目标
        X_data = df[self.feature_columns].values
        y_data = df[self.target_column].values.reshape(-1, 1)

        # 标准化
        X_scaled = self.scaler_X.transform(X_data)
        y_scaled = self.scaler_y.transform(y_data)

        # 创建序列数据
        X_sequences = []
        y_sequences = []
        timestamps = []

        for i in range(len(X_scaled) - self.sequence_length - 1 + 1):
            X_sequences.append(X_scaled[i:i+self.sequence_length])
            y_sequences.append(y_scaled[i+self.sequence_length-1])  # 预测下一个小时
            timestamps.append(df.index[i+self.sequence_length-1])

        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)

        print(f"Created {len(X_sequences)} test sequences")

        return X_sequences, y_sequences, timestamps

    def predict(self, X_sequences):
        """进行预测"""
        print("Making predictions...")

        predictions = []

        # 分批预测，避免内存溢出
        batch_size = 128
        num_batches = (len(X_sequences) + batch_size - 1) // batch_size

        with torch.no_grad():
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(X_sequences))

                X_batch = X_sequences[start_idx:end_idx]
                X_tensor = torch.FloatTensor(X_batch).to(self.device)

                y_pred_scaled = self.model(X_tensor)
                y_pred_scaled = y_pred_scaled.cpu().numpy()

                # 反标准化
                y_pred = self.scaler_y.inverse_transform(y_pred_scaled)

                predictions.extend(y_pred.flatten())

                if (i + 1) % 10 == 0:
                    print(f"Predicted {end_idx}/{len(X_sequences)} samples")

        return np.array(predictions)

    def calculate_metrics(self, y_true, y_pred):
        """计算评估指标"""
        # 反标准化真实值
        y_true_original = self.scaler_y.inverse_transform(y_true.reshape(-1, 1)).flatten()

        mse = mean_squared_error(y_true_original, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true_original, y_pred)
        r2 = r2_score(y_true_original, y_pred)

        # 计算MAPE
        mape = np.mean(np.abs((y_true_original - y_pred) / y_true_original)) * 100

        # 计算方向准确率
        true_direction = np.sign(np.diff(y_true_original))
        pred_direction = np.sign(np.diff(y_pred))
        direction_accuracy = np.mean(true_direction == pred_direction) * 100

        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R²': r2,
            'MAPE': mape,
            'Direction_Accuracy': direction_accuracy,
            'y_true': y_true_original,
            'y_pred': y_pred
        }

    def plot_results(self, timestamps, y_true, y_pred, metrics, save_path=None):
        """绘制评估结果"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('LSTM Model Evaluation Results (PyTorch)', fontsize=16, fontweight='bold')

        # 图1: 预测vs实际值对比
        ax1 = axes[0, 0]
        ax1.plot(timestamps, y_true, label='Actual', color='blue', linewidth=1.5, alpha=0.7)
        ax1.plot(timestamps, y_pred, label='Predicted', color='red', linewidth=1.5, alpha=0.7)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price')
        ax1.set_title('Predicted vs Actual Values')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # 图2: 预测误差分布
        ax2 = axes[0, 1]
        errors = y_pred - y_true
        ax2.hist(errors, bins=50, alpha=0.7, color='green', edgecolor='black')
        ax2.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax2.set_xlabel('Prediction Error')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Prediction Error Distribution')
        ax2.grid(True, alpha=0.3)

        # 图3: 误差随时间的变化
        ax3 = axes[1, 0]
        ax3.plot(timestamps, errors, color='purple', alpha=0.6)
        ax3.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Prediction Error')
        ax3.set_title('Error Over Time')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        # 图4: 性能指标
        ax4 = axes[1, 1]
        ax4.axis('off')

        metrics_text = ".2f"".2f"".2f"".4f"".2f"".2f"f"""
        LSTM Model Performance Metrics:

        MSE: {metrics['MSE']:.6f}
        RMSE: {metrics['RMSE']:.6f}
        MAE: {metrics['MAE']:.6f}
        R²: {metrics['R²']:.4f}
        MAPE: {metrics['MAPE']:.2f}%
        Direction Accuracy: {metrics['Direction_Accuracy']:.2f}%

        Sample Count: {len(y_true)}
        Time Range: {timestamps[0].strftime('%Y-%m-%d')} to {timestamps[-1].strftime('%Y-%m-%d')}
        """

        ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes,
                fontsize=12, verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()

        if save_path is None:
            output_dir = 'evaluation_results'
            os.makedirs(output_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(output_dir, f'model_evaluation_{timestamp_str}.png')

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nEvaluation chart saved to: {save_path}")

        plt.show()

        return fig

    def save_predictions(self, timestamps, y_true, y_pred, metrics):
        """保存预测结果"""
        output_dir = 'evaluation_results'
        os.makedirs(output_dir, exist_ok=True)

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存详细预测结果
        results_df = pd.DataFrame({
            'timestamp': timestamps,
            'actual_price': y_true,
            'predicted_price': y_pred,
            'error': y_pred - y_true,
            'abs_error': np.abs(y_pred - y_true)
        })

        csv_path = os.path.join(output_dir, f'predictions_detailed_{timestamp_str}.csv')
        results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Detailed predictions saved to: {csv_path}")

        # 保存评估指标（修复JSON序列化问题）
        metrics_copy = metrics.copy()
        # 将numpy数组转换为列表
        for key, value in metrics_copy.items():
            if isinstance(value, np.ndarray):
                metrics_copy[key] = value.tolist()
            elif isinstance(value, np.float64) or isinstance(value, np.float32):
                metrics_copy[key] = float(value)
            elif isinstance(value, np.int64) or isinstance(value, np.int32):
                metrics_copy[key] = int(value)

        metrics_path = os.path.join(output_dir, f'metrics_{timestamp_str}.json')
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_copy, f, indent=2, ensure_ascii=False)
        print(f"Metrics saved to: {metrics_path}")

    def evaluate(self):
        """执行完整评估"""
        print("="*60)
        print("LSTM Model Evaluation (PyTorch)")
        print("="*60)

        # 加载测试数据
        df = self.load_test_data()

        # 准备测试序列
        X_test, y_test_scaled, timestamps = self.prepare_test_sequences(df)

        # 进行预测
        y_pred = self.predict(X_test)

        # 计算评估指标
        metrics = self.calculate_metrics(y_test_scaled, y_pred)

        # 打印结果
        print("\n" + "="*60)
        print("Evaluation Results")
        print("="*60)
        print(".6f"".6f"".6f"".4f"".2f"".2f"".2f"f"""
        MSE: {metrics['MSE']:.6f}
        RMSE: {metrics['RMSE']:.6f}
        MAE: {metrics['MAE']:.6f}
        R²: {metrics['R²']:.4f}
        MAPE: {metrics['MAPE']:.2f}%
        Direction Accuracy: {metrics['Direction_Accuracy']:.2f}%

        Total Samples: {len(metrics['y_true'])}
        """)

        # 生成可视化
        print("\nGenerating evaluation charts...")
        self.plot_results(timestamps, metrics['y_true'], metrics['y_pred'], metrics)

        # 保存结果
        self.save_predictions(timestamps, metrics['y_true'], metrics['y_pred'], metrics)

        print("\n" + "="*60)
        print("Evaluation completed!")
        print("="*60)

        return metrics


def main():
    """主函数"""
    evaluator = LSTMEvaluator()
    metrics = evaluator.evaluate()


if __name__ == '__main__':
    main()