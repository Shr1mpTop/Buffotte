"""
LSTM模型训练脚本 (PyTorch版本)
用于预测股市指数走势

使用buffotte.kline_data_hour数据库中的技术指标数据
将数据分为训练集、验证集和测试集，训练LSTM模型
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pickle
import os
import pymysql


class StockDataset(Dataset):
    """股票数据集类"""
    
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMModel(nn.Module):
    """LSTM模型"""
    
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


class LSTMTrainer:
    """LSTM模型训练器"""
    
    def __init__(self, config_path='lstm_config.json'):
        """初始化训练器"""
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.db_type = self.config.get('db_type', 'mysql')
        self.db_config_file = self.config.get('db_config_file', 'config.json')
        self.table_name = self.config.get('table_name', 'kline_data_hour')
        
        # 加载数据库配置
        if self.db_type == 'mysql':
            with open(self.db_config_file, 'r', encoding='utf-8') as f:
                self.db_config = json.load(f)
        self.sequence_length = self.config.get('sequence_length', 60)
        self.prediction_horizon = self.config.get('prediction_horizon', 1)
        
        # 模型参数
        self.lstm_units = self.config.get('lstm_units', [128, 64])
        self.dropout_rate = self.config.get('dropout_rate', 0.2)
        self.batch_size = self.config.get('batch_size', 32)
        self.epochs = self.config.get('epochs', 100)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        
        # 数据集分割比例
        self.train_ratio = self.config.get('train_ratio', 0.7)
        self.val_ratio = self.config.get('val_ratio', 0.15)
        self.test_ratio = self.config.get('test_ratio', 0.15)
        
        # 特征列
        self.feature_columns = self.config.get('feature_columns', [
            'open_price', 'high_price', 'low_price', 'close_price', 'volume',
            'ma5', 'ma10', 'ma20', 'ma30',
            'ema12', 'ema26', 'macd', 'macd_signal', 'macd_hist',
            'rsi6', 'rsi12', 'rsi24',
            'k_value', 'd_value', 'j_value',
            'bollinger_upper', 'bollinger_middle', 'bollinger_lower'
        ])
        
        # 目标列
        self.target_column = self.config.get('target_column', 'close_price')
        
        # 模型保存路径
        self.model_dir = self.config.get('model_dir', 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 设置设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")
        
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
    
    def load_data(self):
        """从数据库加载数据"""
        print(f"正在从{self.db_type.upper()}数据库加载数据...")
        
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
        
        # 构建查询
        columns = ['timestamp'] + self.feature_columns
        if self.target_column not in columns:
            columns.append(self.target_column)
        
        # 加载所有数据
        query = f"SELECT {', '.join(columns)} FROM {self.table_name} ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        
        print(f"加载了 {len(df)} 条数据记录")
        print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
        
        # 数据预处理：删除最早的6000条数据
        if len(df) > 13000:
            df = df.iloc[-13000:].copy()  # 保留最新的13000条
            print(f"删除最早数据后，保留 {len(df)} 条记录")
            print(f"新时间范围: {df.index.min()} 到 {df.index.max()}")
        
        # 删除包含NaN的行
        df.dropna(inplace=True)
        
        print(f"最终数据量: {len(df)} 条记录")
        
        return df
    
    def prepare_rolling_windows(self, df):
        """准备滚动窗口训练数据"""
        print("正在准备滚动窗口训练数据...")
        
        # 提取特征和目标
        X_data = df[self.feature_columns].values
        y_data = df[self.target_column].values.reshape(-1, 1)
        
        # 标准化
        X_scaled = self.scaler_X.fit_transform(X_data)
        y_scaled = self.scaler_y.fit_transform(y_data)
        
        # 创建序列数据
        X_sequences = []
        y_sequences = []
        
        for i in range(len(X_scaled) - self.sequence_length - self.prediction_horizon + 1):
            X_sequences.append(X_scaled[i:i+self.sequence_length])
            y_sequences.append(y_scaled[i+self.sequence_length+self.prediction_horizon-1])
        
        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)
        
        print(f"创建了 {len(X_sequences)} 个序列样本")
        
        # 时间序列滚动窗口分割
        # 从最新数据开始，向过去滑动
        train_size = 24 * 180  # 4320小时 ≈ 180天
        val_size = 24 * 30     # 720小时 ≈ 30天
        
        total_samples = len(X_sequences)
        print(f"总样本数: {total_samples}")
        print(f"训练窗口大小: {train_size} 样本")
        print(f"验证窗口大小: {val_size} 样本")
        
        # 计算可以分成的周期数
        window_size = train_size + val_size
        num_windows = total_samples // window_size
        
        if num_windows == 0:
            raise ValueError(f"数据不足：需要至少 {window_size} 个样本，但只有 {total_samples} 个")
        
        print(f"可以分成 {num_windows} 个训练周期")
        
        # 从最新数据开始（数组末尾）
        rolling_datasets = []
        current_end = total_samples
        
        for i in range(num_windows):
            # 验证集（最新的数据）
            val_end = current_end
            val_start = val_end - val_size
            
            # 训练集（验证集之前的数据）
            train_end = val_start
            train_start = train_end - train_size
            
            if train_start < 0:
                break
                
            X_train = X_sequences[train_start:train_end]
            y_train = y_sequences[train_start:train_end]
            X_val = X_sequences[val_start:val_end]
            y_val = y_sequences[val_start:val_end]
            
            rolling_datasets.append({
                'X_train': X_train,
                'y_train': y_train,
                'X_val': X_val,
                'y_val': y_val,
                'period': i + 1
            })
            
            current_end = train_start
            
            print(f"周期 {i+1}: 训练集 {len(X_train)} 样本, 验证集 {len(X_val)} 样本")
        
        # 剩余最老的数据作为测试集
        test_end = current_end
        test_start = 0
        
        X_test = X_sequences[test_start:test_end]
        y_test = y_sequences[test_start:test_end]
        
        print(f"测试集: {len(X_test)} 样本 (最老的剩余数据)")
        
        return rolling_datasets, (X_test, y_test)
    
    def create_dataloaders(self, train_data, val_data, test_data):
        """创建数据加载器"""
        train_dataset = StockDataset(*train_data)
        val_dataset = StockDataset(*val_data)
        test_dataset = StockDataset(*test_data)
        
        train_loader = DataLoader(
            train_dataset, 
            batch_size=self.batch_size, 
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset, 
            batch_size=self.batch_size, 
            shuffle=False
        )
        test_loader = DataLoader(
            test_dataset, 
            batch_size=self.batch_size, 
            shuffle=False
        )
        
        return train_loader, val_loader, test_loader
    
    def build_model(self, input_size):
        """构建LSTM模型"""
        print("正在构建LSTM模型...")
        
        model = LSTMModel(
            input_size=input_size,
            hidden_sizes=self.lstm_units,
            dropout_rate=self.dropout_rate
        )
        
        model = model.to(self.device)
        
        # 打印模型结构
        print(model)
        
        # 计算参数量
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\n总参数量: {total_params:,}")
        print(f"可训练参数量: {trainable_params:,}")
        
        return model
    
    def train_epoch(self, model, train_loader, criterion, optimizer):
        """训练一个epoch"""
        model.train()
        total_loss = 0
        total_mae = 0
        
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            # 前向传播
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            
            # 反向传播
            loss.backward()
            optimizer.step()
            
            # 统计
            total_loss += loss.item()
            total_mae += torch.mean(torch.abs(outputs - y_batch)).item()
        
        avg_loss = total_loss / len(train_loader)
        avg_mae = total_mae / len(train_loader)
        
        return avg_loss, avg_mae
    
    def validate(self, model, val_loader, criterion):
        """验证模型"""
        model.eval()
        total_loss = 0
        total_mae = 0
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                
                total_loss += loss.item()
                total_mae += torch.mean(torch.abs(outputs - y_batch)).item()
        
        avg_loss = total_loss / len(val_loader)
        avg_mae = total_mae / len(val_loader)
        
        return avg_loss, avg_mae
    
    def train(self):
        """训练模型"""
        print("="*50)
        print("开始LSTM模型训练 (时间序列滚动窗口)")
        print("="*50)
        
        # 加载数据
        df = self.load_data()
        
        # 准备滚动窗口数据
        rolling_datasets, test_data = self.prepare_rolling_windows(df)
        
        # 创建测试数据加载器
        X_test, y_test = test_data
        test_dataset = StockDataset(X_test, y_test)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size, shuffle=False)
        
        # 构建模型
        input_size = len(self.feature_columns)
        model = self.build_model(input_size)
        
        # 定义损失函数和优化器
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        
        # 学习率调度器
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )
        
        # 多周期训练
        best_val_loss = float('inf')
        training_history = {
            'train_loss': [],
            'train_mae': [],
            'val_loss': [],
            'val_mae': [],
            'periods': []
        }
        
        print("\n开始多周期滚动训练...")
        print("-" * 80)
        
        for period_data in rolling_datasets:
            period = period_data['period']
            X_train = period_data['X_train']
            y_train = period_data['y_train']
            X_val = period_data['X_val']
            y_val = period_data['y_val']
            
            print(f"\n=== 训练周期 {period} ===")
            print(f"训练集: {len(X_train)} 样本")
            print(f"验证集: {len(X_val)} 样本")
            
            # 创建数据加载器
            train_dataset = StockDataset(X_train, y_train)
            val_dataset = StockDataset(X_val, y_val)
            
            train_loader = DataLoader(
                train_dataset, 
                batch_size=self.batch_size, 
                shuffle=True
            )
            val_loader = DataLoader(
                val_dataset, 
                batch_size=self.batch_size, 
                shuffle=False
            )
            
            # 在当前周期上训练
            period_train_loss = []
            period_train_mae = []
            period_val_loss = []
            period_val_mae = []
            
            for epoch in range(self.epochs):
                # 训练一个epoch
                train_loss, train_mae = self.train_epoch(
                    model, train_loader, criterion, optimizer
                )
                
                # 验证
                val_loss, val_mae = self.validate(model, val_loader, criterion)
                
                period_train_loss.append(train_loss)
                period_train_mae.append(train_mae)
                period_val_loss.append(val_loss)
                period_val_mae.append(val_mae)
                
                # 学习率调度
                scheduler.step(val_loss)
                
                # 打印进度（每5个epoch）
                if (epoch + 1) % 5 == 0 or epoch == 0:
                    print(f"周期{period} Epoch [{epoch+1}/{self.epochs}] "
                          f"Train Loss: {train_loss:.6f}, Train MAE: {train_mae:.6f} | "
                          f"Val Loss: {val_loss:.6f}, Val MAE: {val_mae:.6f}")
                
                # 保存最佳模型
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    
                    best_model_path = os.path.join(self.model_dir, 'lstm_best_model.pth')
                    torch.save({
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'val_loss': val_loss,
                        'config': {
                            'input_size': input_size,
                            'hidden_sizes': self.lstm_units,
                            'dropout_rate': self.dropout_rate
                        }
                    }, best_model_path)
                    
                    if (epoch + 1) % 5 == 0:
                        print(f"  ✓ 保存最佳模型 (Val Loss: {val_loss:.6f})")
            
            # 记录周期历史
            training_history['train_loss'].extend(period_train_loss)
            training_history['train_mae'].extend(period_train_mae)
            training_history['val_loss'].extend(period_val_loss)
            training_history['val_mae'].extend(period_val_mae)
            training_history['periods'].extend([period] * len(period_train_loss))
        
        print("-" * 80)
        
        # 在测试集上评估
        print("\n在测试集上评估模型...")
        test_loss, test_mae = self.validate(model, test_loader, criterion)
        print(f"测试集损失 (MSE): {test_loss:.6f}")
        print(f"测试集平均绝对误差 (MAE): {test_mae:.6f}")
        
        # 保存最终模型
        final_model_path = os.path.join(self.model_dir, 'lstm_model_final.pth')
        torch.save({
            'model_state_dict': model.state_dict(),
            'config': {
                'input_size': input_size,
                'hidden_sizes': self.lstm_units,
                'dropout_rate': self.dropout_rate
            }
        }, final_model_path)
        print(f"\n最终模型已保存到: {final_model_path}")
        
        # 保存缩放器
        scaler_path = os.path.join(self.model_dir, 'scalers.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump({
                'scaler_X': self.scaler_X,
                'scaler_y': self.scaler_y,
                'feature_columns': self.feature_columns,
                'target_column': self.target_column,
                'sequence_length': self.sequence_length
            }, f)
        print(f"缩放器已保存到: {scaler_path}")
        
        # 保存训练历史
        training_history['test_loss'] = test_loss
        training_history['test_mae'] = test_mae
        history_path = os.path.join(self.model_dir, 'training_history.json')
        with open(history_path, 'w') as f:
            json.dump(training_history, f, indent=2)
        print(f"训练历史已保存到: {history_path}")
        
        print("\n训练完成!")
        return model, training_history


def main():
    """主函数"""
    trainer = LSTMTrainer()
    model, history = trainer.train()


if __name__ == '__main__':
    main()
