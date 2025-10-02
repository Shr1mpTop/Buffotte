# 📧 邮件批量发送功能

## ✨ 新增功能

本次更新新增了两大核心功能：

### 1. 邮件内容缓存系统
- 报告生成和邮件发送完全解耦
- 支持预览、重发、历史报告管理

### 2. 批量邮件发送
- 支持同时向多个收件人发送报告
- 灵活的配置方式（配置文件 + 命令行）
- 支持收件人分组管理

## 🚀 快速开始

### 基础用法

```bash
# 1. 生成报告并缓存
python run_daily_report.py

# 2. 预览邮件内容
python send_cached_report.py --preview

# 3. 发送邮件
python send_cached_report.py
```

### 批量发送

**配置文件方式**（推荐用于固定收件人）：

编辑 `email_config.json`：
```json
{
  "to_address": [
    "recipient1@example.com",
    "recipient2@example.com",
    "recipient3@example.com"
  ]
}
```

**命令行方式**（推荐用于临时发送）：

```bash
python send_cached_report.py --to email1@example.com email2@example.com
```

## 📖 常用命令

```bash
# 预览邮件
python send_cached_report.py --preview

# 发送给所有人（配置文件）
python send_cached_report.py

# 发送给指定人员
python send_cached_report.py --to boss@company.com

# 使用不同配置文件
python send_cached_report.py --email-config email_config_vip.json

# 重发历史报告
python send_cached_report.py --cache models/email_cache_2025-10-01.json
```

## 🎯 使用场景

### 场景 1：日常自动化
```bash
# 每天运行
python run_daily_report.py
python send_cached_report.py
```

### 场景 2：测试后发送
```bash
# 先发给自己测试
python send_cached_report.py --to your_email@example.com

# 确认后发给所有人
python send_cached_report.py
```

### 场景 3：不同收件人组
```bash
# 内部团队
python send_cached_report.py --email-config email_config_team.json

# VIP客户
python send_cached_report.py --email-config email_config_vip.json
```

### 场景 4：交互式菜单（Windows）
```bash
# 使用图形化菜单选择发送对象
send_example.bat
```

## 📚 详细文档

- 📖 [新功能总结](./docs/NEW_FEATURES_SUMMARY.md) - 完整的功能说明
- 📖 [快速参考指南](./docs/QUICK_REFERENCE.md) - 常用命令和示例
- 📖 [批量发送指南](./docs/batch_email_guide.md) - 批量发送详细文档
- 📖 [缓存工作流](./docs/email_caching_workflow.md) - 缓存系统使用指南

## 🆘 帮助

```bash
# 查看所有可用参数
python send_cached_report.py --help
```

## 💡 提示

- ✅ 使用 `--preview` 预览内容，避免发送错误
- ✅ 先发给自己测试，确认无误后再批量发送
- ✅ 为不同收件人组创建不同的配置文件
- ✅ 注意邮件服务商的发送限制（如QQ邮箱每天500封）

---

**享受高效的批量报告发送！** 🎉
