# LSTM模型预测 vs 真实K线对比分析系统

这是一个交互式Web可视化系统，用于对比LSTM模型预测结果与真实市场K线数据。

## 文件结构

```
web_visualization/
├── index.html              # 主页面
├── generate_web_data.py     # 数据生成脚本
├── data/                   # 数据文件夹
│   ├── kline_comparison_data.json      # 完整对比数据
│   └── kline_simplified_data.json      # 简化数据（快速加载）
└── static/                 # 静态资源
    ├── style.css           # 样式文件
    ├── kline-chart.js      # K线图表处理类
    └── main.js             # 主要功能JavaScript
```

## 使用步骤

### 1. 生成数据

首先运行数据生成脚本来提取数据库数据并生成预测结果：

```bash
cd web_visualization
python generate_web_data.py
```

这将会：
- 从数据库加载最近30天的K线数据
- 使用训练好的LSTM模型生成预测结果
- 计算预测误差和统计指标
- 生成JSON格式的数据文件

### 2. 启动Web服务器

由于涉及到AJAX请求加载JSON文件，需要通过HTTP服务器访问：

**使用Python内置服务器：**
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

**使用Node.js服务器（如果已安装）：**
```bash
npx http-server -p 8000
```

### 3. 访问Web界面

在浏览器中打开：
```
http://localhost:8000
```

## 功能特性

### 🔍 交互式图表
- **缩放功能**：使用鼠标滚轮或双指手势缩放图表
- **平移功能**：拖拽图表进行水平滚动
- **时间范围选择**：快速选择24小时、3天、7天、30天或全部数据
- **图表类型切换**：支持K线图、折线图、组合显示

### 📊 数据对比
- **真实 vs 预测**：并列显示真实价格和模型预测价格
- **误差分析**：显示绝对误差或百分比误差的变化趋势
- **实时统计**：动态计算当前可见时间范围的预测性能指标

### 📈 性能指标
- **MAE**：平均绝对误差
- **RMSE**：均方根误差
- **MAPE**：平均绝对百分比误差
- **方向准确率**：价格变化方向预测准确性
- **误差分布**：误差的统计分布情况

### 🎛️ 用户界面
- **响应式设计**：适配桌面和移动设备
- **现代化UI**：美观的界面设计和流畅的交互动画
- **状态保存**：自动保存用户的设置偏好
- **快速操作**：便捷的重置和刷新功能

## 数据格式说明

### 生成的JSON数据包含：

1. **metadata**：数据元信息
   - 生成时间、数据周期、记录数量等

2. **real_kline**：真实K线数据
   - timestamp, open, high, low, close, volume

3. **predicted_kline**：预测K线数据
   - timestamp, open, high, low, close, volume, error, error_pct

4. **errors**：详细误差数据
   - 每个时间点的预测误差和百分比误差

5. **statistics**：整体统计指标
   - MAE, RMSE, MAPE, 方向准确率等

## 自定义配置

### 修改数据周期
在 `generate_web_data.py` 中修改：
```python
# 生成最近60天的数据
web_data = generator.generate_web_data(days_back=60)
```

### 调整图表样式
修改 `static/style.css` 中的颜色和样式定义：
```css
.real-color {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}
.pred-color {
    background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
}
```

### 添加新的时间范围
在 `static/main.js` 中的 `applyTimeRange()` 方法添加新选项。

## 故障排除

### 1. 数据文件不存在
- 确保运行了 `generate_web_data.py`
- 检查 `data/` 文件夹是否有JSON文件
- 确认数据库连接配置正确

### 2. 图表不显示
- 确保通过HTTP服务器访问（不是直接打开HTML文件）
- 检查浏览器控制台是否有错误信息
- 确认JSON数据格式正确

### 3. 性能问题
- 使用简化数据文件（自动优先加载）
- 减少数据周期天数
- 考虑数据采样（如每4小时一个点）

## 技术栈

- **前端框架**：原生JavaScript (ES6+)
- **图表库**：Chart.js v4.x
- **样式**：CSS3 + Flexbox + Grid
- **数据处理**：Python + PyTorch + pandas
- **数据格式**：JSON

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- 移动端Safari和Chrome

## 更新数据

要更新可视化数据，只需重新运行：
```bash
python generate_web_data.py
```

然后刷新浏览器页面即可看到最新数据。

---

**提示**：首次使用建议先用较小的数据集（如7天）测试功能，确认一切正常后再生成更大范围的数据集。