"""
基线模型测试脚本
使用简单的统计方法作为对照组，评估 LSTM 模型的真实效果
"""

import json
import pymysql
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta
import pickle

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class BaselineModels:
    """基线模型集合"""
    
    def __init__(self, data):
        """
        初始化基线模型
        
        Args:
            data: DataFrame，包含历史数据
        """
        self.data = data
        self.target_column = 'close_price'
    
    def persistence_model(self, test_data):
        """
        持久性模型（Naive Forecast）
        预测值 = 上一时刻的真实值
        这是最简单的基线
        """
        predictions = []
        for i in range(len(test_data)):
            if i == 0:
                # 第一个预测使用训练集最后一个值
                pred = test_data[self.target_column].iloc[0]
            else:
                # 使用前一个真实值
                pred = test_data[self.target_column].iloc[i-1]
            predictions.append(pred)
        return np.array(predictions)
    
    def moving_average_model(self, test_data, window=5):
        """
        移动平均模型
        预测值 = 过去 N 个时刻的平均值
        """
        predictions = []
        all_data = pd.concat([self.data[self.target_column], test_data[self.target_column]], ignore_index=True)
        
        for i in range(len(self.data), len(all_data)):
            if i < window:
                pred = all_data[:i].mean()
            else:
                pred = all_data[i-window:i].mean()
            predictions.append(pred)
        
        return np.array(predictions)
    
    def linear_trend_model(self, test_data):
        """
        线性趋势模型
        使用训练集最后 60 个点拟合线性趋势
        """
        from sklearn.linear_model import LinearRegression
        
        # 使用更多历史数据（60个点）
        window = min(60, len(self.data))
        last_data = self.data[self.target_column].iloc[-window:].values
        X_train = np.arange(window).reshape(-1, 1)
        y_train = last_data
        
        # 拟合线性模型
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 预测
        predictions = []
        base_value = last_data[-1]  # 最后一个真实值
        
        for i in range(len(test_data)):
            X_test = np.array([[window + i]])
            pred = model.predict(X_test)[0]
            
            # 限制预测值的变化幅度，避免线性外推过于激进
            # 每步最多变化5%
            max_change = base_value * 0.05
            if abs(pred - base_value) > max_change:
                pred = base_value + np.sign(pred - base_value) * max_change
            
            predictions.append(pred)
            # 更新基准值（使用平滑策略）
            if i > 0:
                base_value = 0.7 * predictions[-1] + 0.3 * base_value
        
        return np.array(predictions)
    
    def exponential_smoothing_model(self, test_data, alpha=0.3):
        """
        指数平滑模型
        预测值 = alpha * 上一真实值 + (1-alpha) * 上一预测值
        """
        predictions = []
        # 初始预测值为训练集最后一个值（更合理）
        last_pred = self.data[self.target_column].iloc[-1]
        
        for i in range(len(test_data)):
            if i == 0:
                pred = last_pred
            else:
                # 指数平滑
                pred = alpha * test_data[self.target_column].iloc[i-1] + (1 - alpha) * last_pred
            predictions.append(pred)
            last_pred = pred
        
        return np.array(predictions)
    
    def seasonal_naive_model(self, test_data, season_length=24):
        """
        季节性朴素模型
        预测值 = 上一个季节同期的值
        适用于有周期性的数据（如每日24小时周期）
        """
        predictions = []
        all_data = pd.concat([self.data[self.target_column], test_data[self.target_column]], ignore_index=True)
        
        for i in range(len(self.data), len(all_data)):
            # 使用一个季节前的值
            if i >= season_length:
                pred = all_data.iloc[i - season_length]
            else:
                pred = all_data.iloc[0]  # 如果不够一个季节，使用第一个值
            predictions.append(pred)
        
        return np.array(predictions)


class BaselineTester:
    """基线测试器"""
    
    def __init__(self, config_file='lstm_config.json', db_config_file='config.json'):
        """初始化测试器"""
        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        with open(db_config_file, 'r', encoding='utf-8') as f:
            self.db_config = json.load(f)
        
        self.target_column = self.config.get('target_column', 'close_price')
        self.test_size = self.config.get('test_split', 0.15)
    
    def load_data(self):
        """从 MySQL 加载数据"""
        print("正在从 MySQL 加载数据...")
        
        connection = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database']
        )
        
        query = f"SELECT * FROM {self.config['table_name']} ORDER BY timestamp"
        df = pd.read_sql(query, connection)
        connection.close()
        
        print(f"加载完成：{len(df)} 条记录")
        return df
    
    def prepare_data(self, df):
        """准备训练集和测试集"""
        # 按时间排序
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 分割数据
        split_idx = int(len(df) * (1 - self.test_size))
        train_data = df[:split_idx]
        test_data = df[split_idx:]
        
        print(f"\n数据分割：")
        print(f"训练集：{len(train_data)} 条（{split_idx/len(df)*100:.1f}%）")
        print(f"测试集：{len(test_data)} 条（{len(test_data)/len(df)*100:.1f}%）")
        
        return train_data, test_data
    
    def calculate_metrics(self, y_true, y_pred, model_name):
        """计算评估指标"""
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # 计算 MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # 计算方向准确率（涨跌预测准确率）
        if len(y_true) > 1:
            true_direction = np.sign(np.diff(y_true))
            pred_direction = np.sign(np.diff(y_pred))
            direction_accuracy = np.mean(true_direction == pred_direction) * 100
        else:
            direction_accuracy = 0
        
        return {
            'model': model_name,
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'MAPE': mape,
            'Direction_Accuracy': direction_accuracy
        }
    
    def load_lstm_predictions(self):
        """加载 LSTM 模型的预测结果"""
        try:
            # 加载保存的预测结果
            with open('models/training_history.json', 'r') as f:
                history = json.load(f)
            
            # 加载测试集预测（如果有的话）
            # 这里我们需要重新运行 LSTM 在测试集上
            print("正在加载 LSTM 模型进行测试集预测...")
            
            import torch
            import torch.nn as nn
            
            # 定义模型结构（与训练时相同）
            class LSTMModel(nn.Module):
                def __init__(self, input_size, hidden_sizes, output_size, dropout_rate=0.2):
                    super(LSTMModel, self).__init__()
                    self.hidden_sizes = hidden_sizes
                    self.num_layers = len(hidden_sizes)
                    
                    self.lstm_layers = nn.ModuleList()
                    self.dropout_layers = nn.ModuleList()
                    
                    for i, hidden_size in enumerate(hidden_sizes):
                        input_dim = input_size if i == 0 else hidden_sizes[i-1]
                        self.lstm_layers.append(
                            nn.LSTM(input_dim, hidden_size, batch_first=True)
                        )
                        if i < len(hidden_sizes) - 1:
                            self.dropout_layers.append(nn.Dropout(dropout_rate))
                    
                    self.fc = nn.Linear(hidden_sizes[-1], output_size)
                
                def forward(self, x):
                    for i, lstm_layer in enumerate(self.lstm_layers):
                        x, _ = lstm_layer(x)
                        if i < len(self.dropout_layers):
                            x = self.dropout_layers[i](x)
                    
                    out = self.fc(x[:, -1, :])
                    return out
            
            # 加载模型
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # 加载 scaler
            with open('models/scalers.pkl', 'rb') as f:
                scalers = pickle.load(f)
            
            scaler_X = scalers['scaler_X']
            scaler_y = scalers['scaler_y']
            
            # 加载数据
            df = self.load_data()
            train_data, test_data = self.prepare_data(df)
            
            # 准备特征
            feature_columns = [col for col in self.config.get('feature_columns', []) 
                             if col in df.columns]
            
            X_test = test_data[feature_columns].values
            y_test = test_data[self.target_column].values
            
            # 标准化
            X_test_scaled = scaler_X.transform(X_test)
            
            # 创建序列
            sequence_length = self.config.get('sequence_length', 60)
            X_sequences = []
            y_sequences = []
            
            for i in range(sequence_length, len(X_test_scaled)):
                X_sequences.append(X_test_scaled[i-sequence_length:i])
                y_sequences.append(y_test[i])
            
            X_sequences = np.array(X_sequences)
            y_sequences = np.array(y_sequences)
            
            # 加载模型权重
            input_size = len(feature_columns)
            hidden_sizes = self.config.get('lstm_units', [128, 64])
            
            model = LSTMModel(input_size, hidden_sizes, 1, 
                            self.config.get('dropout_rate', 0.2))
            model.load_state_dict(torch.load('models/lstm_model_final.pth', 
                                            map_location=device))
            model.to(device)
            model.eval()
            
            # 预测
            X_tensor = torch.FloatTensor(X_sequences).to(device)
            with torch.no_grad():
                predictions_scaled = model(X_tensor).cpu().numpy()
            
            # 反标准化
            predictions = scaler_y.inverse_transform(predictions_scaled)
            
            return predictions.flatten(), y_sequences
            
        except Exception as e:
            print(f"加载 LSTM 预测失败：{e}")
            return None, None
    
    def run_baseline_tests(self):
        """运行所有基线模型测试"""
        print("=" * 60)
        print("基线模型测试")
        print("=" * 60)
        
        # 加载数据
        df = self.load_data()
        train_data, test_data = self.prepare_data(df)
        
        # 初始化基线模型
        baseline = BaselineModels(train_data)
        
        # 真实值
        y_true = test_data[self.target_column].values
        
        # 测试所有基线模型
        results = []
        predictions_dict = {}
        
        print("\n正在测试基线模型...")
        
        # 1. 持久性模型
        print("\n1. 持久性模型（Persistence）...")
        try:
            pred = baseline.persistence_model(test_data)
            predictions_dict['Persistence'] = pred
            metrics = self.calculate_metrics(y_true, pred, 'Persistence')
            results.append(metrics)
            print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 2. 移动平均模型
        for window in [5, 10, 20]:
            print(f"\n2. 移动平均模型（MA-{window}）...")
            try:
                pred = baseline.moving_average_model(test_data, window)
                predictions_dict[f'MA-{window}'] = pred
                metrics = self.calculate_metrics(y_true, pred, f'MA-{window}')
                results.append(metrics)
                print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
            except Exception as e:
                print(f"   ❌ 失败: {e}")
        
        # 3. 线性趋势模型
        print("\n3. 线性趋势模型（Linear Trend）...")
        try:
            pred = baseline.linear_trend_model(test_data)
            predictions_dict['Linear Trend'] = pred
            metrics = self.calculate_metrics(y_true, pred, 'Linear Trend')
            results.append(metrics)
            print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 4. 指数平滑模型
        for alpha in [0.1, 0.3, 0.5]:
            print(f"\n4. 指数平滑模型（EMA-{alpha}）...")
            try:
                pred = baseline.exponential_smoothing_model(test_data, alpha)
                predictions_dict[f'EMA-{alpha}'] = pred
                metrics = self.calculate_metrics(y_true, pred, f'EMA-{alpha}')
                results.append(metrics)
                print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
            except Exception as e:
                print(f"   ❌ 失败: {e}")
        
        # 5. 季节性朴素模型
        print("\n5. 季节性朴素模型（Seasonal Naive）...")
        try:
            pred = baseline.seasonal_naive_model(test_data, season_length=24)
            predictions_dict['Seasonal-24h'] = pred
            metrics = self.calculate_metrics(y_true, pred, 'Seasonal-24h')
            results.append(metrics)
            print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 6. LSTM 模型
        print("\n6. LSTM 模型...")
        try:
            lstm_pred, lstm_y_true = self.load_lstm_predictions()
            if lstm_pred is not None:
                predictions_dict['LSTM'] = lstm_pred
                # 注意：LSTM 的测试集可能因序列长度而略短
                metrics = self.calculate_metrics(lstm_y_true, lstm_pred, 'LSTM')
                results.append(metrics)
                print(f"   ✅ RMSE: {metrics['RMSE']:.4f}, MAE: {metrics['MAE']:.4f}")
                print(f"   注意：LSTM 测试集长度为 {len(lstm_pred)}（因序列窗口而减少）")
            else:
                print("   ⚠️  未找到训练好的 LSTM 模型")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 打印结果对比表
        self.print_results_table(results)
        
        # 可视化对比
        self.visualize_comparison(y_true, predictions_dict, test_data)
        
        # 保存结果
        self.save_results(results)
        
        return results, predictions_dict
    
    def print_results_table(self, results):
        """打印结果对比表"""
        print("\n" + "=" * 100)
        print("模型性能对比表")
        print("=" * 100)
        print(f"{'模型':<20} {'MSE':<12} {'RMSE':<12} {'MAE':<12} {'R²':<10} {'MAPE(%)':<12} {'方向准确率(%)':<15}")
        print("-" * 100)
        
        for result in results:
            print(f"{result['model']:<20} "
                  f"{result['MSE']:<12.6f} "
                  f"{result['RMSE']:<12.6f} "
                  f"{result['MAE']:<12.6f} "
                  f"{result['R2']:<10.4f} "
                  f"{result['MAPE']:<12.2f} "
                  f"{result['Direction_Accuracy']:<15.2f}")
        
        print("=" * 100)
        
        # 找出最佳模型
        best_by_rmse = min(results, key=lambda x: x['RMSE'])
        best_by_direction = max(results, key=lambda x: x['Direction_Accuracy'])
        
        print(f"\n✨ 最佳 RMSE：{best_by_rmse['model']} ({best_by_rmse['RMSE']:.6f})")
        print(f"✨ 最佳方向准确率：{best_by_direction['model']} ({best_by_direction['Direction_Accuracy']:.2f}%)")
    
    def visualize_comparison(self, y_true, predictions_dict, test_data):
        """可视化所有模型的预测对比"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # 准备时间轴
        timestamps = test_data['timestamp'].values[:len(y_true)]
        
        # 1. 所有模型预测对比
        ax = axes[0, 0]
        ax.plot(timestamps, y_true, label='真实值', color='black', linewidth=2, alpha=0.7)
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        for i, (name, pred) in enumerate(predictions_dict.items()):
            # 调整长度（LSTM 可能更短）
            pred_len = min(len(pred), len(y_true))
            ax.plot(timestamps[:pred_len], pred[:pred_len], 
                   label=name, alpha=0.6, linewidth=1, color=colors[i % len(colors)])
        
        ax.set_xlabel('时间')
        ax.set_ylabel('价格')
        ax.set_title('所有模型预测对比')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # 2. 误差对比（箱线图）
        ax = axes[0, 1]
        errors_dict = {}
        for name, pred in predictions_dict.items():
            pred_len = min(len(pred), len(y_true))
            errors = np.abs(y_true[:pred_len] - pred[:pred_len])
            errors_dict[name] = errors
        
        ax.boxplot(errors_dict.values(), labels=errors_dict.keys())
        ax.set_ylabel('绝对误差')
        ax.set_title('模型误差分布对比')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        
        # 3. 累积误差对比
        ax = axes[1, 0]
        for name, pred in predictions_dict.items():
            pred_len = min(len(pred), len(y_true))
            errors = np.abs(y_true[:pred_len] - pred[:pred_len])
            cumulative_errors = np.cumsum(errors)
            ax.plot(range(pred_len), cumulative_errors, label=name, alpha=0.7)
        
        ax.set_xlabel('预测步数')
        ax.set_ylabel('累积绝对误差')
        ax.set_title('累积误差对比')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # 4. 性能指标雷达图
        ax = axes[1, 1]
        # 这里简化为柱状图
        models = list(predictions_dict.keys())
        rmse_values = []
        mae_values = []
        
        for name, pred in predictions_dict.items():
            pred_len = min(len(pred), len(y_true))
            rmse = np.sqrt(mean_squared_error(y_true[:pred_len], pred[:pred_len]))
            mae = mean_absolute_error(y_true[:pred_len], pred[:pred_len])
            rmse_values.append(rmse)
            mae_values.append(mae)
        
        x = np.arange(len(models))
        width = 0.35
        
        ax.bar(x - width/2, rmse_values, width, label='RMSE', alpha=0.7)
        ax.bar(x + width/2, mae_values, width, label='MAE', alpha=0.7)
        
        ax.set_ylabel('误差值')
        ax.set_title('RMSE vs MAE 对比')
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('baseline_comparison.png', dpi=300, bbox_inches='tight')
        print("\n✅ 对比图表已保存：baseline_comparison.png")
        plt.show()
    
    def save_results(self, results):
        """保存结果到文件"""
        df = pd.DataFrame(results)
        df.to_csv('baseline_results.csv', index=False, encoding='utf-8-sig')
        print("\n✅ 结果已保存：baseline_results.csv")


if __name__ == '__main__':
    print("=" * 60)
    print("LSTM 模型基线测试")
    print("对比简单统计模型，评估 LSTM 的真实效果")
    print("=" * 60)
    
    tester = BaselineTester()
    results, predictions = tester.run_baseline_tests()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
