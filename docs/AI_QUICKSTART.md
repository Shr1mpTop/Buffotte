# AI多Agent分析系统 - 快速使用指南

## 🚀 5分钟快速开始

### 第一步：安装依赖

```powershell
# 在项目根目录
pip install google-generativeai pillow
```

### 第二步：获取API Key

1. 打开浏览器访问: https://aistudio.google.com/
2. 登录Google账号
3. 点击 "Get API Key" 创建新的API密钥
4. 复制API密钥

### 第三步：设置环境变量

**Windows PowerShell**:
```powershell
# 临时设置（当前会话有效）
$env:GEMINI_API_KEY = "粘贴你的API-Key"

# 永久设置（推荐）
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', '粘贴你的API-Key', 'User')
```

验证设置是否成功：
```powershell
echo $env:GEMINI_API_KEY
```

### 第四步：运行测试

```powershell
# 测试AI分析功能
python test_ai_analysis.py
```

如果看到以下输出，说明配置成功：
```
🤖 启动多Agent AI分析工作流
============================================================
[1/3] 📊 数据分析师正在分析历史数据和预测...
✓ 数据分析完成 - 识别 5 个关键发现
[2/3] 📰 市场分析师正在分析市场动态和新闻...
✓ 市场分析完成 - 情绪: positive
[3/3] 💼 基金经理正在综合分析并制定投资策略...
✓ 投资建议生成完成 - 建议: BUY
  信心度: 75%
```

### 第五步：集成到日常流程

```powershell
# AI分析已自动集成，直接运行日报告即可
python -m src.run_daily_report
```

## 📊 查看分析报告

运行后会生成以下文件：

### 1. HTML可视化报告
路径: `models/ai_analysis_report_YYYYMMDD_HHMMSS.html`

**打开方式**:
- 双击HTML文件
- 或在浏览器中打开
- 包含精美格式和所有分析内容

### 2. JSON数据报告
路径: `models/ai_analysis_report.json`

**用途**:
- 程序化读取分析结果
- 集成到其他系统
- 数据存档和分析

### 3. 邮件报告
如果配置了邮件，会自动收到包含：
- 预测K线图
- AI分析摘要
- 完整HTML报告附件

## 🎯 理解分析结果

### 投资建议类型
- **BUY (买入)**: AI建议当前是买入时机
- **SELL (卖出)**: AI建议当前应该卖出或做空
- **HOLD (持有)**: AI建议观望或持有现有仓位

### 信心度说明
- **75%+**: 高信心，数据和市场面都支持该建议
- **50-75%**: 中等信心，有一定支持但存在不确定性
- **50%以下**: 低信心，建议谨慎对待

### 风险等级
- **Low (低)**: 风险较小，市场较稳定
- **Medium (中)**: 存在一定风险，需要关注
- **High (高)**: 风险较大，建议谨慎或观望

## ⚙️ 高级配置

### 自定义分析参数

编辑 `llm_config.json`:

```json
{
  "llm": {
    "model": "gemini-2.0-flash-exp",  // 使用的模型
    "temperature": {
      "data_analyst": 0.3,      // 数据分析师创造性（越低越保守）
      "market_analyst": 0.5,     // 市场分析师创造性
      "fund_manager": 0.4        // 基金经理创造性
    }
  },
  "workflow": {
    "enable_news_search": false,  // 是否启用真实新闻搜索
    "save_reports": true,         // 是否保存报告文件
    "generate_html": true         // 是否生成HTML报告
  }
}
```

### 启用真实新闻搜索

默认使用模拟新闻数据。要启用真实新闻：

1. 设置 `enable_news_search: true`
2. 在 `llm/agents/market_analyst.py` 中实现 `_search_news()` 方法
3. 可以使用：
   - Google News API
   - Bing Search API
   - 网页爬虫（注意遵守网站robots.txt）

## 🐛 常见问题

### Q1: 提示"API Key未设置"
**A**: 确保正确设置了环境变量，并重启PowerShell或IDE

### Q2: 提示"模块未找到"
**A**: 运行 `pip install google-generativeai pillow`

### Q3: API调用失败
**A**: 
- 检查网络连接
- 验证API Key是否有效
- 查看是否超出免费配额

### Q4: 分析结果质量不佳
**A**: 
- 确保有足够的历史数据（至少30天）
- 尝试调整temperature参数
- 检查预测模型的准确性

### Q5: 分析速度慢
**A**: 
- 正常情况需要30-60秒
- 可以减少历史数据窗口
- 确保网络稳定

## 💡 使用建议

1. **每日运行**: 建议每天运行一次，获取最新分析
2. **人工复核**: AI分析仅供参考，重要决策需要人工判断
3. **记录准确率**: 定期对比AI建议和实际结果，评估准确性
4. **风险控制**: 严格遵守AI建议中的止损策略
5. **持续优化**: 根据反馈调整配置参数

## 📈 后续步骤

1. **查看详细文档**: `llm/README.md`
2. **自定义Agent**: 修改prompt或添加新agent
3. **集成到自动化**: 配置Windows计划任务
4. **监控准确率**: 建立回测和评估系统

## 🆘 获取帮助

- 查看详细文档: `llm/README.md`
- 查看代码注释: 所有文件都有详细注释
- 提交Issue: 如果遇到问题或有建议

---

**祝使用愉快！** 🎉
