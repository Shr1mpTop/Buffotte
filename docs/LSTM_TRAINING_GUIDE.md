# LSTM K线预测模型使用指南

## 概述

本项目使用PyTorch实现LSTM模型对日K线数据进行预测训练。模型从数据库的`kline_data_day`表中读取历史数据，包括timestamp、open_price、close_price、high_price、low_price、volume等字段。

## 功能特性

- ✅ 自动从MySQL数据库加载K线数据
- ✅ 丰富的特征工程（移动平均、波动率、成交量等）
- ✅ 基于PyTorch的LSTM模型
- ✅ 训练/验证/测试集自动划分
- ✅ 数据标准化处理
- ✅ 早停机制防止过拟合
- ✅ 学习率自适应调整
- ✅ 训练过程可视化
- ✅ 方向预测准确率评估
- ✅ 模型自动保存和加载

## 安装依赖

### 方法1: 使用pip安装PyTorch (CPU版本)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 方法2: 使用conda安装PyTorch (推荐)

```bash
conda install pytorch torchvision torchaudio cpuonly -c pytorch -y
```

### 方法3: GPU版本（如果有NVIDIA显卡）

```bash
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或使用conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
```

### 安装其他依赖

```bash
pip install -r requirements.txt
```

## 配置文件

### 1. 数据库配置 (config.json)

```json
{
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "buffotte",
    "charset": "utf8mb4"
}
```

### 2. LSTM模型配置 (lstm_config.json)

```json
{
  "seq_length": 20,
  "hidden_size": 64,
  "num_layers": 2,
  "dropout": 0.2,
  "batch_size": 32,
  "learning_rate": 0.001,
  "num_epochs": 100,
  "train_ratio": 0.8,
  "val_ratio": 0.1,
  "early_stopping_patience": 15,
  "features": [
    "open_price",
    "close_price",
    "high_price",
    "low_price",
    "volume"
  ]
}
```

**参数说明：**

- `seq_length`: 序列长度，使用过去N天的数据进行预测（默认20天）
- `hidden_size`: LSTM隐藏层大小（默认64）
- `num_layers`: LSTM层数（默认2层）
- `dropout`: Dropout比例，防止过拟合（默认0.2）
- `batch_size`: 批次大小（默认32）
- `learning_rate`: 学习率（默认0.001）
- `num_epochs`: 最大训练轮数（默认100）
- `train_ratio`: 训练集比例（默认0.8）
- `val_ratio`: 验证集比例（默认0.1）
- `early_stopping_patience`: 早停耐心值（默认15）
- `features`: 基础特征列表（会自动生成更多衍生特征）

## 使用方法

### 1. 准备配置文件

复制示例配置文件并修改：

```bash
# 如果还没有config.json
cp config.example.json config.json

# 复制LSTM配置文件
cp lstm_config.example.json lstm_config.json
```

### 2. 运行训练

```bash
cd src
python lstm_trainer.py
```

### 3. 训练输出

训练过程会在`models/`目录下生成以下文件：

- `best_model_YYYYMMDD_HHMMSS.pth` - 最佳模型权重
- `scaler_X_YYYYMMDD_HHMMSS.pkl` - 特征标准化器
- `scaler_y_YYYYMMDD_HHMMSS.pkl` - 目标标准化器
- `lstm_training_info.json` - 训练详细信息
- `training_curves_YYYYMMDD_HHMMSS.png` - 训练曲线图
- `predictions_YYYYMMDD_HHMMSS.png` - 预测结果可视化

## 模型架构

```
LSTMModel(
  (lstm): LSTM(input_size, hidden_size=64, num_layers=2, batch_first=True, dropout=0.2)
  (fc): Sequential(
    (0): Linear(64, 32)
    (1): ReLU()
    (2): Dropout(p=0.2)
    (3): Linear(32, 1)
  )
)
```

## 特征工程

模型自动生成以下特征：

1. **价格变化率特征** (Lag 1-5)
   - `close_pct_1` 到 `close_pct_5`
   - `volume_pct_1` 到 `volume_pct_5`

2. **移动平均特征** (5, 10, 20, 30天)
   - `ma_5`, `ma_10`, `ma_20`, `ma_30`
   - `ma_5_ratio`, `ma_10_ratio`, `ma_20_ratio`, `ma_30_ratio`

3. **波动率特征** (5, 10, 20天)
   - `volatility_5`, `volatility_10`, `volatility_20`

4. **成交量移动平均** (5, 10, 20天)
   - `volume_ma_5`, `volume_ma_10`, `volume_ma_20`

5. **价格范围特征**
   - `price_range` - 价格波动范围
   - `body_ratio` - K线实体比例

## 预测目标

模型预测**下一天的收益率**：

```
target = (close_price[t+1] - close_price[t]) / close_price[t]
```

## 评估指标

- **MSE (Mean Squared Error)** - 均方误差
- **RMSE (Root Mean Squared Error)** - 均方根误差
- **MAE (Mean Absolute Error)** - 平均绝对误差
- **Direction Accuracy** - 方向预测准确率（涨跌方向是否正确）

## 高级用法

### 使用Python API

```python
from lstm_trainer import LSTMTrainer

# 初始化训练器
trainer = LSTMTrainer(
    config_path='config.json',
    lstm_config_path='lstm_config.json'
)

# 训练模型
training_info = trainer.train(save_model=True)

# 加载数据并预测
df = trainer.load_data_from_db()
predictions = trainer.predict(df)
```

### 加载已训练模型进行预测

```python
from lstm_trainer import LSTMTrainer
import pandas as pd

# 初始化训练器
trainer = LSTMTrainer()

# 加载模型和标准化器
trainer.load_model('best_model')

# 加载新数据并预测
df = trainer.load_data_from_db()
predictions = trainer.predict(df)

print(f"预测的下一天收益率: {predictions[-1]:.4f}")
```

## 注意事项

1. **数据量要求**：建议至少有200条以上的历史数据才能获得较好的训练效果
2. **时间序列特性**：数据按时间顺序划分训练/验证/测试集，不进行随机打乱
3. **硬件要求**：CPU即可训练，如有GPU可显著提升训练速度
4. **过拟合问题**：已使用Dropout、早停等技术，但仍需关注验证集表现
5. **市场变化**：金融市场是非平稳的，模型需要定期重新训练

## 调优建议

### 提高预测准确率

1. **增加序列长度** (`seq_length`): 使用更长的历史数据
2. **调整模型复杂度**:
   - 增加 `hidden_size` (如128, 256)
   - 增加 `num_layers` (如3, 4层)
3. **特征工程**: 在代码中添加更多技术指标
4. **数据增强**: 使用更多相关数据源

### 防止过拟合

1. **增加Dropout** (`dropout`): 如0.3, 0.4
2. **减少模型复杂度**: 降低 `hidden_size` 或 `num_layers`
3. **早停**: 调整 `early_stopping_patience`
4. **正则化**: 在优化器中添加weight_decay

### 加速训练

1. **增大批次** (`batch_size`): 如64, 128
2. **使用GPU**: 自动检测并使用
3. **减少epochs**: 依靠早停机制

## 故障排查

### 1. 连接数据库失败

- 检查 `config.json` 中的数据库配置
- 确认数据库服务正在运行
- 验证用户名和密码是否正确

### 2. 内存不足

- 减小 `batch_size`
- 减小 `seq_length`
- 减少训练数据量

### 3. 训练损失不下降

- 检查学习率是否合适
- 尝试不同的 `learning_rate` (如0.0001, 0.01)
- 检查数据是否存在异常值

### 4. 方向准确率接近50%

- 说明模型几乎没有预测能力
- 尝试增加特征工程
- 考虑使用更长的历史数据
- 检查数据质量

## 目录结构

```
.
├── src/
│   └── lstm_trainer.py          # LSTM训练脚本
├── models/                       # 模型保存目录（自动创建）
│   ├── best_model_*.pth
│   ├── scaler_X_*.pkl
│   ├── scaler_y_*.pkl
│   ├── lstm_training_info.json
│   ├── training_curves_*.png
│   └── predictions_*.png
├── config.json                   # 数据库配置
├── lstm_config.json              # LSTM模型配置
└── requirements.txt              # Python依赖
```

## 参考资料

- [PyTorch官方文档](https://pytorch.org/docs/stable/index.html)
- [LSTM原理](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [时间序列预测](https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/)

## License

MIT License
