# AI分析报告邮件功能 - 使用说明

## 📧 邮件功能概览

每日运行 `python -m src.run_daily_report` 时，系统会自动发送包含AI分析的专业邮件报告。

## 📊 邮件内容

### 1. 邮件主题
```
BUFF市场分析报告 - 2025年10月02日
```

### 2. 邮件正文结构

#### 🤖 AI多Agent分析结论（置顶，重点关注）
- **投资建议**: BUY/SELL/HOLD
- **信心度**: 0-100%
- **市场情绪**: POSITIVE/NEUTRAL/NEGATIVE
- **风险等级**: HIGH/MEDIUM/LOW
- **关键发现**: Top 3最重要的数据洞察

#### 🔮 模型预测
- **明日预测**: 方向和预期回报率
- **5日预测**: 完整的5天走势预测
- **可视化标识**: 🟢上涨 🔴下跌

#### 📎 附件说明
列出所有附加的文件

## 📁 邮件附件

每封邮件自动包含以下附件：

1. **AI分析完整报告.html** ⭐ 重点查看
   - 精美的可视化HTML报告
   - 包含基金经理、数据分析师、市场分析师的完整分析
   - 可在浏览器中直接打开查看

2. **预测K线图.png**
   - 历史30天 + 未来5天的K线预测图
   - 红绿蜡烛图显示价格走势

3. **预测数据.json**
   - 结构化的预测数据
   - 可用于程序化处理

4. **AI分析数据.json**
   - 完整的AI分析结果（JSON格式）
   - 包含所有Agent的详细输出

## 🎯 关键改进

### ✅ 已实现的优化

1. **AI分析结论置顶**
   - 最重要的投资建议放在邮件最前面
   - 一眼就能看到核心结论

2. **使用最新日期**
   - 所有日期显示为当前真实日期（2025年10月2日）
   - 不再出现历史日期（2024年）

3. **HTML报告优化**
   - 基金经理报告排在最前面
   - 标注"最终投资策略建议（重点）"
   - 清晰的视觉层次

4. **专业的邮件格式**
   - 使用emoji和分隔线增强可读性
   - 结构清晰，重点突出
   - 包含免责声明

## 📋 邮件示例

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BUFF饰品市场 AI分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
报告日期：2025年10月02日
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 【AI多Agent分析结论】（重点关注）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 投资建议：BUY
💯 信心度：75%
📊 市场情绪：POSITIVE
⚠️  风险等级：MEDIUM

🔍 关键发现：
1. 30日均价上涨12.5%，呈现明确上升趋势
2. 交易量较前期增长35%，市场活跃度提升
3. 预测模型显示未来5天持续看涨信号

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔮 【模型预测】未来5天走势

明日预测：UP (预期回报率 0.80%)

完整5日预测：
🟢 第1天: UP     (+0.80%)
🟢 第2天: UP     (+1.20%)
🔴 第3天: DOWN   (-0.30%)
🟢 第4天: UP     (+0.50%)
🟢 第5天: UP     (+0.20%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 附件说明：
• AI分析完整报告.html (⭐推荐查看)
• 预测K线图.png
• 预测数据.json
• AI分析数据.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  免责声明：
本报告由AI系统自动生成，仅供参考，不构成投资建议。
投资有风险，决策需谨慎。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Powered by Buffotte AI Analysis System
```

## 🔧 配置要求

### 1. 邮件配置
确保 `email_config.json` 正确配置：

```json
{
  "smtp_server": "smtp.qq.com",
  "smtp_port": 587,
  "username": "your-email@qq.com",
  "password": "your-smtp-password",
  "from_address": "your-email@qq.com",
  "to_address": "recipient@example.com",
  "use_tls": true
}
```

### 2. AI配置
确保 `llm_config.json` 正确配置：

```json
{
  "llm": {
    "api_key": "AIzaSy...",
    "model": "gemini-2.0-flash-exp"
  },
  "workflow": {
    "save_reports": true,
    "generate_html": true,
    "output_dir": "models"
  }
}
```

## 🚀 使用步骤

### 方式1: 手动运行
```powershell
python -m src.run_daily_report
```

### 方式2: 自动化（Windows计划任务）
```powershell
# 注册每日任务（每天23:00执行）
$action = New-ScheduledTaskAction -Execute "python" -Argument "E:\github\Buffotte\src\run_daily_report.py" -WorkingDirectory "E:\github\Buffotte"
$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"
Register-ScheduledTask -TaskName "Buffotte_Daily_Report" -Action $action -Trigger $trigger -User "SYSTEM"
```

## 📊 查看报告

### 1. 邮件中查看
- **邮件正文**: 快速查看关键结论和预测
- **附件HTML**: 双击打开完整的可视化报告

### 2. 本地查看
所有报告保存在 `models/` 目录：
```
models/
├── ai_analysis_report_20251002_120000.html  # HTML报告
├── ai_analysis_report.json                   # JSON数据
├── next_week_prediction_20251002T120000Z.png # K线图
└── next_week_prediction.json                 # 预测数据
```

## 🎨 HTML报告特点

### 报告结构（优化后）
1. **🎯 最终投资策略建议**（置顶）
   - 基金经理的综合决策
   - 包含执行摘要、策略建议、风险评估

2. **📊 数据分析报告**
   - 历史数据分析
   - 技术指标
   - 关键发现

3. **📰 市场分析报告**
   - 市场动态
   - 利好利空因素
   - 市场情绪

### 视觉设计
- 渐变色头部
- 投资建议卡片（大号显示）
- Agent标签（不同颜色）
- 关键发现高亮框
- 响应式布局

## 💡 使用建议

1. **每日查看邮件**
   - 早上起床后查看邮件中的AI分析结论
   - 快速了解市场趋势和投资建议

2. **详细研究HTML报告**
   - 有时间时打开HTML附件
   - 仔细阅读三个Agent的完整分析
   - 重点关注风险评估部分

3. **对比历史报告**
   - 保存每日的HTML报告
   - 定期回顾AI建议的准确性
   - 用于优化决策流程

4. **结合人工判断**
   - AI分析仅供参考
   - 结合自己的市场理解
   - 不要盲目依赖AI建议

## ⚠️ 注意事项

1. **API配额**: Gemini免费版每分钟15次请求，每天运行一次足够

2. **邮件发送**: 
   - 如果邮件发送失败，报告仍会保存在本地
   - 检查SMTP配置和网络连接

3. **附件大小**: 
   - HTML报告通常 < 100KB
   - 所有附件总大小 < 1MB
   - 不会超过邮件附件限制

4. **时区**: 所有时间均使用本地时区显示

## 🐛 故障排除

### 问题1: 邮件未收到AI分析
**检查**:
- `llm_config.json` 是否正确配置
- API Key是否有效
- 查看终端输出是否有错误

### 问题2: HTML报告打不开
**解决**:
- 使用现代浏览器（Chrome、Edge、Firefox）
- 检查文件编码是否为UTF-8

### 问题3: 日期显示错误
**原因**: 已修复，现在使用当前真实日期

### 问题4: 附件缺失
**检查**:
- `workflow.save_reports` 是否为 `true`
- `workflow.generate_html` 是否为 `true`
- `models/` 目录是否有写权限

## 📞 技术支持

如有问题：
1. 查看 `docs/AI_QUICKSTART.md`
2. 查看 `docs/AI_EXAMPLES.md`
3. 运行 `python test_email_format.py` 预览邮件格式
4. 提交Issue到GitHub仓库

---

**更新日期**: 2025年10月2日
**版本**: 2.0.0
**状态**: ✅ 已优化并测试通过
