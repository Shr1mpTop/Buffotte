# 📧 邮件批量发送 - 快速参考

## ✨ 新功能

现在支持向多个收件人批量发送报告！

## 🚀 快速开始

### 方式 1：配置文件（推荐用于固定收件人）

编辑 `email_config.json`：

```json
{
  "smtp_server": "smtp.qq.com",
  "smtp_port": 587,
  "use_tls": true,
  "username": "your_email@qq.com",
  "password": "your_password",
  "from_address": "your_email@qq.com",
  "to_address": [
    "recipient1@example.com",
    "recipient2@example.com",
    "recipient3@example.com"
  ]
}
```

然后运行：
```bash
python send_cached_report.py
```

### 方式 2：命令行（推荐用于临时发送）

```bash
# 发送给单个人
python send_cached_report.py --to someone@example.com

# 发送给多个人
python send_cached_report.py --to email1@example.com email2@example.com email3@example.com
```

## 📖 常用命令

```bash
# 1. 预览邮件内容
python send_cached_report.py --preview

# 2. 发送给配置文件中的所有人
python send_cached_report.py

# 3. 发送给指定的人（覆盖配置文件）
python send_cached_report.py --to boss@company.com analyst@company.com

# 4. 使用其他配置文件
python send_cached_report.py --email-config email_config_vip.json

# 5. 从特定缓存发送
python send_cached_report.py --cache models/old_report.json

# 6. 组合使用
python send_cached_report.py --cache models/old_report.json --to test@example.com --preview
```

## 💡 实用技巧

### 技巧 1：测试发送
先发给自己测试，确认无误后再发给所有人：

```bash
# 第一步：发给自己
python send_cached_report.py --to your_email@example.com

# 第二步：确认后发给所有人
python send_cached_report.py
```

### 技巧 2：创建多个配置文件

**email_config_internal.json** （内部团队）
```json
{
  "to_address": ["team1@company.com", "team2@company.com"]
}
```

**email_config_clients.json** （客户）
```json
{
  "to_address": ["client1@example.com", "client2@example.com"]
}
```

使用时：
```bash
python send_cached_report.py --email-config email_config_internal.json
python send_cached_report.py --email-config email_config_clients.json
```

### 技巧 3：创建发送脚本

**send_to_all.bat** （Windows）：
```batch
@echo off
echo Sending to internal team...
python send_cached_report.py --email-config email_config_internal.json

echo Sending to clients...
python send_cached_report.py --email-config email_config_clients.json

echo All emails sent!
pause
```

**send_to_all.sh** （Linux/Mac）：
```bash
#!/bin/bash
echo "Sending to internal team..."
python send_cached_report.py --email-config email_config_internal.json

echo "Sending to clients..."
python send_cached_report.py --email-config email_config_clients.json

echo "All emails sent!"
```

## 🔄 完整工作流

### 日常使用流程

```bash
# Step 1: 生成报告（自动缓存）
python run_daily_report.py

# Step 2: 预览邮件内容
python send_cached_report.py --preview

# Step 3: 确认后发送
python send_cached_report.py
```

### 紧急修改后重发

```bash
# 如果需要重新生成报告
python run_daily_report.py

# 发送新报告
python send_cached_report.py
```

### 历史报告重发

```bash
# 查看可用的缓存文件
ls models/email_cache*.json

# 发送特定日期的报告
python send_cached_report.py --cache models/email_cache_2025-10-01.json
```

## ⚠️ 注意事项

1. **邮件配额**：
   - QQ邮箱：每天最多 500 封
   - Gmail：每天最多 500 封（免费账户）

2. **防止垃圾邮件**：
   - 避免短时间内大量发送
   - 请收件人将您的地址加入白名单

3. **命令行参数优先级**：
   - `--to` 参数会覆盖配置文件中的 `to_address`

## 🆘 故障排查

### 问题：发送失败

```bash
# 检查配置文件是否正确
cat email_config.json

# 测试发送给自己
python send_cached_report.py --to your_email@example.com

# 查看详细错误信息（如果有）
python send_cached_report.py --preview
```

### 问题：部分人未收到

- 检查垃圾邮件文件夹
- 验证邮件地址拼写
- 确认对方邮箱未满

## 📚 更多信息

详细文档请查看：
- [批量发送完整指南](./batch_email_guide.md)
- [邮件缓存使用说明](./email_caching_workflow.md)

## 🎯 示例场景

### 场景 1：每日自动报告（5人团队）

`email_config.json`：
```json
{
  "to_address": [
    "manager@company.com",
    "analyst1@company.com",
    "analyst2@company.com",
    "developer@company.com",
    "investor@company.com"
  ]
}
```

每天运行：
```bash
python run_daily_report.py
python send_cached_report.py
```

### 场景 2：重要报告（需要审核）

```bash
# 生成报告
python run_daily_report.py

# 先发给经理审核
python send_cached_report.py --to manager@company.com

# 经理确认后，发给所有人
python send_cached_report.py
```

### 场景 3：不同客户群

```bash
# VIP客户（详细版）
python send_cached_report.py --email-config email_config_vip.json

# 普通客户（摘要版）
python send_cached_report.py --email-config email_config_regular.json
```

---

**享受高效的批量报告发送！** 🎉
