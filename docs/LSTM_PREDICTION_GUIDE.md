# LSTM股市预测系统使用指南

## 概述

本系统使用LSTM（长短期记忆网络）深度学习模型，基于历史K线数据和技术指标预测未来7天的股市走势。

## 系统架构

### 数据来源
- **数据库**: `buffotte.db`
- **数据表**: `kline_data_hour`
- **数据频率**: 小时级K线数据

### 特征指标（共24个）
1. **价格指标**
   - `open_price` - 开盘价
   - `high_price` - 最高价
   - `low_price` - 最低价
   - `close_price` - 收盘价 (预测目标)

2. **成交量指标**
   - `volume` - 成交量
   - `turnover` - 成交额

3. **移动平均线**
   - `ma5` - 5周期移动平均
   - `ma10` - 10周期移动平均
   - `ma20` - 20周期移动平均
   - `ma30` - 30周期移动平均

4. **指数移动平均**
   - `ema12` - 12周期指数移动平均
   - `ema26` - 26周期指数移动平均

5. **MACD指标**
   - `macd` - MACD值
   - `macd_signal` - MACD信号线
   - `macd_hist` - MACD柱状图

6. **RSI相对强弱指标**
   - `rsi6` - 6周期RSI
   - `rsi12` - 12周期RSI
   - `rsi24` - 24周期RSI

7. **KDJ指标**
   - `k_value` - K值
   - `d_value` - D值
   - `j_value` - J值

8. **布林带**
   - `bollinger_upper` - 上轨
   - `bollinger_middle` - 中轨
   - `bollinger_lower` - 下轨

## 快速开始

### 1. 环境准备

确保已安装必要的Python包：

```bash
pip install torch numpy pandas scikit-learn matplotlib
```

**注意**: 系统使用PyTorch深度学习框架，会自动检测并使用GPU（如果可用）。

### 2. 配置文件

编辑 `lstm_config.json` 文件调整训练参数：

```json
{
  "db_path": "buffotte.db",
  "table_name": "kline_data_hour",
  "sequence_length": 60,          // 使用过去60小时的数据
  "prediction_horizon": 1,        // 预测未来1小时
  "lstm_units": [128, 64],        // LSTM层配置
  "dropout_rate": 0.2,            // Dropout比例
  "batch_size": 32,               // 批次大小
  "epochs": 100,                  // 最大训练轮数
  "learning_rate": 0.001,         // 学习率
  "train_ratio": 0.7,             // 训练集70%
  "val_ratio": 0.15,              // 验证集15%
  "test_ratio": 0.15              // 测试集15%
}
```

### 3. 训练模型

运行训练脚本：

```bash
python train_lstm_model.py
```

训练过程会：
- 从数据库加载数据
- 自动分割训练集、验证集、测试集
- 使用早停机制防止过拟合
- 保存最佳模型和训练历史

**输出文件**：
- `models/lstm_model_final.pth` - 最终模型（PyTorch格式）
- `models/lstm_best_model.pth` - 最佳模型（PyTorch格式）
- `models/scalers.pkl` - 数据缩放器
- `models/training_history.json` - 训练历史

### 4. 预测未来走势

运行预测脚本：

```bash
python predict_future.py
```

**输出**：
- 控制台显示未来7天的每日汇总预测
- `predictions/predictions_detailed_*.csv` - 详细的小时级预测
- `predictions/predictions_daily_*.csv` - 每日汇总

**预测结果包含**：
- 每日开盘价、收盘价、最高价、最低价
- 每日涨跌幅
- 整体趋势分析
- 上涨/下跌天数统计

### 5. 可视化结果

运行可视化脚本：

```bash
python visualize_predictions.py
```

**生成图表**：
1. **历史数据与预测对比** - 显示历史数据和预测的连续性
2. **未来7天趋势图** - 每日平均价格和涨跌趋势
3. **每日涨跌幅柱状图** - 清晰显示每天的涨跌情况
4. **价格分布对比** - 历史价格与预测价格的分布对比
5. **训练历史曲线** - 模型训练过程的损失和MAE曲线

## 模型架构

### LSTM网络结构

```
输入层: (序列长度=60, 特征数=24)
    ↓
LSTM层1: 128单元 + Dropout(0.2)
    ↓
LSTM层2: 64单元 + Dropout(0.2)
    ↓
全连接层: 1单元（输出预测价格）
```

### 数据预处理

1. **标准化**: 使用MinMaxScaler将所有特征缩放到[0,1]范围
2. **序列构建**: 滑动窗口方式创建时间序列样本
3. **数据分割**: 按时间顺序分割，保证不泄露未来信息

### 训练策略

- **深度学习框架**: PyTorch
- **优化器**: Adam
- **损失函数**: MSE (均方误差)
- **评估指标**: MAE (平均绝对误差)
- **早停机制**: 验证损失10轮不下降则停止
- **学习率调整**: 验证损失5轮不改善则减半
- **设备支持**: 自动检测并使用CUDA GPU（如果可用）

## 参数调优建议

### 序列长度 (sequence_length)
- **默认**: 60小时
- **建议范围**: 24-168小时
- **说明**: 更长的序列可以捕捉更长期的趋势，但需要更多数据和计算

### LSTM单元数 (lstm_units)
- **默认**: [128, 64]
- **建议**: 根据数据量调整
  - 小数据集: [64, 32]
  - 中等数据集: [128, 64]
  - 大数据集: [256, 128]

### Dropout率 (dropout_rate)
- **默认**: 0.2
- **建议范围**: 0.1-0.5
- **说明**: 过拟合严重时增加，欠拟合时减少

### 学习率 (learning_rate)
- **默认**: 0.001
- **建议范围**: 0.0001-0.01
- **说明**: 训练不稳定时降低，收敛太慢时提高

## 性能评估

### 评估指标

1. **MSE (均方误差)**: 越小越好
2. **MAE (平均绝对误差)**: 实际价格误差
3. **方向准确率**: 涨跌方向预测准确率

### 模型验证

建议通过以下方式验证模型：
1. 观察训练曲线是否收敛
2. 验证集和测试集性能接近
3. 预测结果与实际走势趋势一致
4. 回测历史数据验证准确性

## 注意事项

### 1. 数据质量
- 确保数据库有足够的历史数据（建议至少3个月）
- 检查数据中是否有异常值或缺失值
- 技术指标需要正确计算

### 2. 模型限制
- LSTM预测短期趋势较准确，长期预测不确定性大
- 模型无法预测突发事件的影响
- 需要定期重新训练以适应市场变化

### 3. 使用建议
- 将预测结果作为参考，不作为唯一决策依据
- 结合其他分析方法综合判断
- 定期评估模型性能，必要时重新训练

### 4. 计算资源
- 训练时间取决于数据量和硬件配置
- PyTorch自动检测并使用GPU加速（CUDA）
- CPU训练也完全可行，只是速度稍慢
- 预测速度快，可以实时使用

## 高级用法

### 自定义特征

编辑 `lstm_config.json` 的 `feature_columns`，添加或删除特征：

```json
{
  "feature_columns": [
    "close_price",
    "volume",
    "ma20",
    "rsi12",
    "macd"
    // 添加自定义特征
  ]
}
```

### 多步预测

修改 `prediction_horizon` 参数实现多步预测：

```json
{
  "prediction_horizon": 3  // 预测未来3小时
}
```

### 批量预测

可以修改 `predict_future.py` 中的 `days` 参数预测不同天数：

```python
predictor.predict_and_display(days=14)  # 预测14天
```

## 故障排除

### 问题1: 内存不足
**解决方案**: 
- 减少 `batch_size`
- 减少 `sequence_length`
- 减少特征数量

### 问题2: 训练不收敛
**解决方案**:
- 降低 `learning_rate`
- 增加训练数据
- 调整网络结构

### 问题3: 过拟合
**解决方案**:
- 增加 `dropout_rate`
- 减少网络层数或单元数
- 增加训练数据

### 问题4: 预测结果不合理
**解决方案**:
- 检查数据质量
- 重新训练模型
- 调整特征选择

## 文件结构

```
Buffotte/
├── train_lstm_model.py          # 训练脚本（PyTorch）
├── predict_future.py            # 预测脚本（PyTorch）
├── visualize_predictions.py    # 可视化脚本（PyTorch）
├── quick_start_lstm.py          # 一键运行脚本
├── lstm_config.json            # 配置文件
├── buffotte.db                 # 数据库
├── models/                     # 模型目录
│   ├── lstm_model_final.pth    # PyTorch模型
│   ├── lstm_best_model.pth     # PyTorch最佳模型
│   ├── scalers.pkl
│   └── training_history.json
├── predictions/                # 预测结果目录
│   ├── predictions_detailed_*.csv
│   ├── predictions_daily_*.csv
│   ├── prediction_visualization_*.png
│   └── training_history.png
└── docs/
    └── LSTM_PREDICTION_GUIDE.md
```

## 更新日志

### v1.0.0 (2025-10-04)
- 初始版本发布
- 使用PyTorch深度学习框架
- 支持24个技术指标的LSTM预测
- 自动GPU加速支持
- 完整的训练、预测、可视化流程
- 详细的配置和文档

## 联系支持

如有问题或建议，请查阅项目README或提交Issue。

---

祝您使用愉快！📈
