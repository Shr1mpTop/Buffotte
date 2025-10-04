# PyTorch版本更新说明

## 🎉 更新完成！

LSTM股市预测系统已成功从TensorFlow迁移到PyTorch！

## ✅ 已完成的修改

### 1. 核心脚本更新
- ✅ `train_lstm_model.py` - 使用PyTorch重写，支持GPU自动检测
- ✅ `predict_future.py` - 适配PyTorch模型加载和推理
- ✅ `visualize_predictions.py` - 适配PyTorch模型
- ✅ `quick_start_lstm.py` - 更新依赖检查

### 2. 模型变化
- **旧格式**: `.keras` 文件（TensorFlow/Keras）
- **新格式**: `.pth` 文件（PyTorch）
- **保存内容**: 模型状态字典 + 配置信息

### 3. 文档更新
- ✅ `LSTM_README.md` - 更新安装命令和说明
- ✅ `docs/LSTM_PREDICTION_GUIDE.md` - 更新技术栈说明
- ✅ `docs/LSTM_PROJECT_SUMMARY.md` - 更新框架信息
- ✅ `requirements.txt` - 移除TensorFlow，保留PyTorch

## 🔥 PyTorch的优势

### 1. 自动GPU加速
```python
# PyTorch自动检测CUDA
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"使用设备: {device}")
```

### 2. 更灵活的模型定义
```python
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_sizes, dropout_rate):
        super(LSTMModel, self).__init__()
        # 更清晰的模型结构定义
        self.lstm_layers = nn.ModuleList()
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(hidden_sizes[-1], 1)
```

### 3. 更直观的训练循环
```python
for epoch in range(epochs):
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
```

### 4. 更好的调试体验
- 动态计算图，易于调试
- 清晰的错误信息
- Python原生的编程体验

## 📦 安装依赖

### CPU版本（适合测试）
```bash
pip install torch numpy pandas scikit-learn matplotlib
```

### GPU版本（推荐，加速训练）
```bash
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或 CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 🚀 快速开始

### 一键运行
```bash
python quick_start_lstm.py
```

### 分步运行
```bash
# 1. 训练模型（自动使用GPU）
python train_lstm_model.py

# 2. 预测未来
python predict_future.py

# 3. 可视化
python visualize_predictions.py
```

## 📊 性能对比

### 训练速度
- **CPU**: ~20-30分钟（取决于数据量）
- **GPU**: ~5-10分钟（显著加速）

### 模型大小
- PyTorch模型: 约1-2MB
- 保存格式更紧凑

### 推理速度
- 预测168小时: <1秒（CPU）
- GPU加速后更快

## 🔧 代码变化示例

### 模型定义
**TensorFlow/Keras:**
```python
model = Sequential()
model.add(LSTM(128, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(64))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')
```

**PyTorch:**
```python
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_sizes, dropout_rate):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_sizes[0], batch_first=True)
        self.lstm2 = nn.LSTM(hidden_sizes[0], hidden_sizes[1], batch_first=True)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(hidden_sizes[1], 1)
    
    def forward(self, x):
        x, _ = self.lstm1(x)
        x = self.dropout(x)
        x, _ = self.lstm2(x)
        x = x[:, -1, :]
        return self.fc(x)

model = LSTMModel(input_size, [128, 64], 0.2)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
```

### 模型保存/加载
**TensorFlow/Keras:**
```python
# 保存
model.save('model.keras')

# 加载
model = keras.models.load_model('model.keras')
```

**PyTorch:**
```python
# 保存
torch.save({
    'model_state_dict': model.state_dict(),
    'config': model_config
}, 'model.pth')

# 加载
checkpoint = torch.load('model.pth')
model = LSTMModel(**checkpoint['config'])
model.load_state_dict(checkpoint['model_state_dict'])
```

### 训练循环
**TensorFlow/Keras:**
```python
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32
)
```

**PyTorch:**
```python
for epoch in range(epochs):
    model.train()
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
```

## ⚙️ 配置文件

配置文件 `lstm_config.json` 保持不变，无需修改！

```json
{
  "db_path": "buffotte.db",
  "sequence_length": 60,
  "lstm_units": [128, 64],
  "dropout_rate": 0.2,
  "batch_size": 32,
  "epochs": 100,
  "learning_rate": 0.001
}
```

## 🎯 GPU使用说明

### 检查CUDA可用性
```python
import torch
print(f"CUDA可用: {torch.cuda.is_available()}")
print(f"CUDA版本: {torch.version.cuda}")
print(f"GPU数量: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU名称: {torch.cuda.get_device_name(0)}")
```

### 训练时会自动显示
```
使用设备: cuda
正在构建LSTM模型...
LSTMModel(
  (lstm_layers): ModuleList(...)
  (dropout): Dropout(p=0.2)
  (fc): Linear(in_features=64, out_features=1)
)
总参数量: 123,456
```

## 📝 注意事项

### 1. 模型不兼容
- PyTorch模型（.pth）无法加载TensorFlow模型（.keras）
- 需要重新训练模型

### 2. 训练时间
- 首次训练需要完整运行
- 建议有足够数据后再训练

### 3. GPU内存
- 如果GPU内存不足，可以减小 `batch_size`
- 或者使用CPU训练（自动回退）

### 4. 依赖安装
- 确保卸载TensorFlow避免冲突
- PyTorch安装可能需要几分钟

## 🔄 迁移步骤

如果你之前使用TensorFlow版本：

1. **备份旧模型**（可选）
   ```bash
   mkdir models_backup
   move models\*.keras models_backup\
   ```

2. **安装PyTorch**
   ```bash
   pip uninstall tensorflow keras
   pip install torch numpy pandas scikit-learn matplotlib
   ```

3. **重新训练**
   ```bash
   python train_lstm_model.py
   ```

4. **验证预测**
   ```bash
   python predict_future.py
   ```

## 📚 相关文档

- [PyTorch官方文档](https://pytorch.org/docs/stable/index.html)
- [LSTM教程](https://pytorch.org/docs/stable/generated/torch.nn.LSTM.html)
- [GPU加速指南](https://pytorch.org/tutorials/beginner/blitz/tensor_tutorial.html#cuda-tensors)

## 🎊 总结

PyTorch版本提供：
- ✅ 更好的性能
- ✅ 更灵活的模型定义
- ✅ 自动GPU加速
- ✅ 更好的调试体验
- ✅ 与项目中已有的PyTorch组件统一

现在你可以开始使用新的PyTorch版本了！🚀

---

**更新日期**: 2025年10月4日
**版本**: v2.0.0 (PyTorch)
