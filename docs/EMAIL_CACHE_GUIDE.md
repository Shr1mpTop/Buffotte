# 邮件缓存与发送系统

## 概述

邮件缓存系统将报告生成和邮件发送解耦，提供更灵活的工作流程。

## 工作流程

### 1. 生成报告（不发送邮件）

```bash
python run_daily_report.py
```

**功能：**
- 获取最新市场数据
- 生成AI分析报告
- 创建可视化图表
- 导出PNG/PDF报告
- **将邮件内容缓存到 `models/email_cache.json`**

**输出文件：**
- `models/email_cache.json` - 邮件内容缓存
- `models/daily_market_report_*.png` - 报告PNG版本
- `models/daily_market_report_*.pdf` - 报告PDF版本
- `models/next_week_prediction_*.png` - 预测图表
- `models/next_week_prediction.json` - 预测数据

### 2. 发送缓存的报告

```bash
python send_cached_report.py
```

**功能：**
- 从缓存加载邮件内容
- 显示邮件预览
- 确认后发送邮件
- 记录发送时间

## 使用场景

### 场景1：日常自动化报告

```bash
# 每日定时任务（如凌晨2点）
python run_daily_report.py

# 工作时间手动审核后发送（如上午9点）
python send_cached_report.py
```

### 场景2：仅预览不发送

```bash
# 生成报告
python run_daily_report.py

# 预览邮件内容
python send_cached_report.py --preview
```

### 场景3：重新发送报告

```bash
# 邮件发送失败或需要重发
python send_cached_report.py
```

### 场景4：发送历史报告

```bash
# 备份当前缓存
cp models/email_cache.json models/email_cache_backup_2025-10-02.json

# 稍后发送备份的报告
python send_cached_report.py --cache models/email_cache_backup_2025-10-02.json
```

## 命令行选项

### `send_cached_report.py` 参数

```bash
# 显示帮助信息
python send_cached_report.py --help

# 预览模式（不发送）
python send_cached_report.py --preview

# 指定缓存文件
python send_cached_report.py --cache <path>

# 指定邮件配置文件
python send_cached_report.py --email-config <path>

# 组合使用
python send_cached_report.py --cache models/old_cache.json --preview
```

## 缓存文件格式

`models/email_cache.json` 结构：

```json
{
  "generated_at": "20251002T051927Z",
  "date": "2025-10-02",
  "subject": "BUFF市场AI分析日报 - 2025-10-02",
  "body": "AI分析摘要...",
  "attachments": [
    "models/daily_market_report_20251002_051927.png",
    "models/daily_market_report_20251002_051927.pdf",
    "models/next_week_prediction_20251002T051927Z.png"
  ],
  "markdown_report": "完整的Markdown报告内容...",
  "ai_results_summary": {
    "data_analyst": {...},
    "market_analyst": {...},
    "fund_manager": {...},
    "summary_agent": {...}
  },
  "last_sent_at": "2025-10-02T09:15:30.123456"
}
```

## 优势

1. **灵活性**
   - 可以先生成报告，审核后再发送
   - 随时重新发送报告，无需重新分析

2. **可靠性**
   - 邮件发送失败不影响报告生成
   - 可以单独重试邮件发送

3. **测试友好**
   - 使用 `--preview` 查看邮件内容
   - 修改邮件配置后可重新发送

4. **历史追溯**
   - 备份缓存文件保留历史报告
   - 可以发送任意历史日期的报告

## 注意事项

1. **附件文件**
   - 确保附件文件存在于指定路径
   - 移动或删除附件会导致发送失败

2. **缓存覆盖**
   - 每次运行 `run_daily_report.py` 会覆盖 `email_cache.json`
   - 需要保留历史缓存请手动备份

3. **邮件配置**
   - 确保 `email_config.json` 配置正确
   - 或设置环境变量（见 `src/email_sender.py`）

## 故障排查

### 问题：缓存文件不存在

```
❌ Error: Cache file not found: models/email_cache.json
```

**解决方案：**
```bash
# 先运行报告生成
python run_daily_report.py
```

### 问题：附件文件缺失

```
⚠️  Warning: Some attachment files are missing:
  ✗ models/daily_market_report_xxx.png
```

**解决方案：**
- 确认文件路径正确
- 重新运行 `run_daily_report.py`
- 或选择继续发送（不包含缺失文件）

### 问题：邮件发送失败

```
❌ Failed to send email. Check email configuration and try again.
```

**解决方案：**
1. 检查 `email_config.json` 配置
2. 检查网络连接
3. 查看详细错误信息
4. 修复后重新运行 `send_cached_report.py`

## 集成到定时任务

### Linux/Mac (crontab)

```bash
# 编辑定时任务
crontab -e

# 每天凌晨2点生成报告
0 2 * * * cd /path/to/Buffotte && python run_daily_report.py >> logs/daily_report.log 2>&1

# 每天上午9点发送报告
0 9 * * * cd /path/to/Buffotte && echo "y" | python send_cached_report.py >> logs/email_send.log 2>&1
```

### Windows (任务计划程序)

创建两个任务：

1. **任务1：生成报告**
   - 触发器：每天凌晨2点
   - 操作：`python run_daily_report.py`

2. **任务2：发送邮件**
   - 触发器：每天上午9点
   - 操作：`cmd /c echo y | python send_cached_report.py`

## 相关文件

- `run_daily_report.py` - 主报告生成脚本
- `send_cached_report.py` - 邮件发送脚本
- `src/email_sender.py` - 邮件发送模块
- `models/email_cache.json` - 邮件内容缓存
- `email_config.json` - 邮件配置文件
