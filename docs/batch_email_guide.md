# 邮件批量发送功能使用指南

## 概述

邮件发送功能现已支持批量发送到多个收件人，您可以通过以下两种方式指定收件人：

1. **配置文件方式**：在 `email_config.json` 中配置多个收件人
2. **命令行方式**：在运行脚本时动态指定收件人

## 方式一：配置文件方式

### 配置多个收件人

编辑 `email_config.json` 文件，将 `to_address` 字段设置为数组：

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

### 配置单个收件人

如果只有一个收件人，可以使用字符串格式：

```json
{
  "to_address": "single_recipient@example.com"
}
```

或者数组格式：

```json
{
  "to_address": ["single_recipient@example.com"]
}
```

### 发送邮件

配置完成后，正常运行发送脚本即可：

```bash
python send_cached_report.py
```

邮件将自动发送给配置文件中的所有收件人。

## 方式二：命令行方式

使用 `--to` 参数可以在运行时动态指定收件人，这会**覆盖**配置文件中的设置。

### 发送给单个收件人

```bash
python send_cached_report.py --to recipient@example.com
```

### 发送给多个收件人

```bash
python send_cached_report.py --to email1@example.com email2@example.com email3@example.com
```

### 结合其他参数使用

```bash
# 预览后发送给指定收件人
python send_cached_report.py --preview --to recipient@example.com

# 从特定缓存文件发送给多个收件人
python send_cached_report.py --cache models/old_report.json --to email1@example.com email2@example.com
```

## 使用场景

### 场景 1: 固定收件人列表

如果每次都发送给同一组人，推荐使用**配置文件方式**：

1. 在 `email_config.json` 中配置所有收件人
2. 直接运行 `python send_cached_report.py`

### 场景 2: 测试发送

在正式发送前，可以先发送给自己测试：

```bash
python send_cached_report.py --to your_test_email@example.com
```

### 场景 3: 特殊报告

某些报告需要发送给特定人员：

```bash
python send_cached_report.py --to vip_client1@example.com vip_client2@example.com
```

### 场景 4: 不同部门

可以创建多个配置文件，针对不同部门：

```bash
# 发送给管理层
python send_cached_report.py --email-config email_config_management.json

# 发送给技术团队
python send_cached_report.py --email-config email_config_tech.json
```

## 完整工作流示例

### 日常自动化流程

```bash
# 1. 生成报告并缓存
python run_daily_report.py

# 2. 预览报告内容
python send_cached_report.py --preview

# 3. 确认无误后发送（发送给配置文件中的所有人）
python send_cached_report.py
```

### 手动选择收件人

```bash
# 1. 生成报告并缓存
python run_daily_report.py

# 2. 先发送给自己预览
python send_cached_report.py --to your_email@example.com

# 3. 确认无误后发送给所有人
python send_cached_report.py --to \
  manager@example.com \
  analyst@example.com \
  investor@example.com
```

## 注意事项

1. **邮件配额限制**：某些邮件服务提供商对发送频率和数量有限制，请注意：
   - QQ邮箱：每天最多发送 500 封
   - Gmail：每天最多发送 500 封（免费账户）
   
2. **防垃圾邮件**：批量发送可能被识别为垃圾邮件，建议：
   - 使用企业邮箱
   - 确保收件人已将您的地址加入白名单
   - 避免过于频繁的发送

3. **隐私保护**：所有收件人都会在邮件头中看到完整的收件人列表，如需隐藏收件人信息，请考虑使用密送（BCC）功能（需要修改代码）。

4. **性能考虑**：当前实现会将邮件发送给所有收件人，如果收件人很多，建议：
   - 分批发送
   - 使用专业的邮件服务（如 SendGrid、Mailgun）

## 高级用法

### 创建收件人分组

可以创建不同的配置文件来管理不同的收件人组：

**email_config_vip.json** （VIP客户）
```json
{
  "to_address": [
    "vip1@example.com",
    "vip2@example.com"
  ]
}
```

**email_config_team.json** （内部团队）
```json
{
  "to_address": [
    "analyst@example.com",
    "developer@example.com",
    "manager@example.com"
  ]
}
```

使用时指定配置文件：
```bash
python send_cached_report.py --email-config email_config_vip.json
python send_cached_report.py --email-config email_config_team.json
```

### Shell 脚本自动化

创建一个 `send_to_all.sh` 脚本（Linux/Mac）：

```bash
#!/bin/bash

# 发送给所有分组
echo "Sending to VIP clients..."
python send_cached_report.py --email-config email_config_vip.json

echo "Sending to internal team..."
python send_cached_report.py --email-config email_config_team.json

echo "Done!"
```

或者 `send_to_all.bat` （Windows）：

```batch
@echo off
echo Sending to VIP clients...
python send_cached_report.py --email-config email_config_vip.json

echo Sending to internal team...
python send_cached_report.py --email-config email_config_team.json

echo Done!
pause
```

## 故障排查

### 问题：邮件发送失败

**可能原因：**
- SMTP 服务器拒绝连接
- 认证失败
- 收件人地址格式错误

**解决方法：**
1. 检查 SMTP 配置是否正确
2. 确认邮箱密码/授权码是否有效
3. 验证所有收件人地址格式是否正确

### 问题：部分收件人未收到

**可能原因：**
- 被识别为垃圾邮件
- 收件人邮箱已满
- 邮件地址错误

**解决方法：**
1. 检查垃圾邮件文件夹
2. 要求收件人将您的地址加入白名单
3. 验证邮件地址是否正确

## 总结

批量发送功能提供了灵活的收件人管理方式：

- ✅ **配置文件方式**：适合固定的收件人列表
- ✅ **命令行方式**：适合临时或测试场景
- ✅ **支持混合使用**：可以同时使用两种方式

选择最适合您工作流程的方式，提高报告分发效率！
