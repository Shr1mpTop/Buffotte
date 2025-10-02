# 🎉 新功能总结 - 邮件批量发送与缓存系统

## 📋 功能概述

本次更新实现了两大核心功能：

### 1️⃣ 邮件内容缓存系统
将报告生成和邮件发送解耦，支持独立操作。

### 2️⃣ 批量邮件发送
支持同时向多个收件人发送报告，提供灵活的配置方式。

---

## 🆕 新增功能详解

### 功能 1：邮件缓存系统

#### 📌 核心改进
- `run_daily_report.py` 现在只生成报告并保存到缓存
- 新增 `send_cached_report.py` 脚本专门负责发送邮件
- 缓存文件保存在 `models/email_cache.json`

#### 💡 使用方法

```bash
# 步骤 1：生成报告（自动缓存）
python run_daily_report.py

# 步骤 2：预览邮件内容
python send_cached_report.py --preview

# 步骤 3：确认后发送
python send_cached_report.py
```

#### ✨ 优势
- ✅ **灵活性**：可以先生成报告，稍后再决定是否发送
- ✅ **可靠性**：即使邮件发送失败，也不需要重新生成报告
- ✅ **可测试**：可以预览邮件内容，确认无误后再发送
- ✅ **可重发**：支持从历史缓存重新发送旧报告

---

### 功能 2：批量邮件发送

#### 📌 核心功能
- 支持配置文件方式指定多个收件人
- 支持命令行方式动态指定收件人
- 命令行参数可覆盖配置文件设置

#### 💡 使用方法

**方式 A：配置文件（推荐用于固定收件人）**

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

发送：
```bash
python send_cached_report.py
```

**方式 B：命令行（推荐用于临时发送）**

```bash
# 单个收件人
python send_cached_report.py --to someone@example.com

# 多个收件人
python send_cached_report.py --to email1@example.com email2@example.com email3@example.com
```

#### ✨ 优势
- ✅ **批量发送**：一次性发送给多个收件人
- ✅ **灵活配置**：支持配置文件和命令行两种方式
- ✅ **分组管理**：可创建多个配置文件管理不同收件人组
- ✅ **临时调整**：命令行参数可临时覆盖配置

---

## 📂 新增文件

### 1. `send_cached_report.py`
独立的邮件发送脚本，支持：
- 从缓存读取邮件内容
- 预览邮件内容
- 批量发送
- 自定义收件人

### 2. `docs/email_caching_workflow.md`
邮件缓存系统的完整使用指南

### 3. `docs/batch_email_guide.md`
批量发送功能的详细文档

### 4. `docs/QUICK_REFERENCE.md`
快速参考指南，包含常用命令和示例

---

## 🔄 修改的文件

### 1. `run_daily_report.py`
- ✏️ 移除了邮件发送功能
- ➕ 添加了邮件内容缓存功能
- 💾 生成的缓存保存在 `models/email_cache.json`

### 2. `src/email_sender.py`
- ➕ 添加了 `to_addresses` 参数
- ✨ 支持单个或多个收件人
- 🔧 改进了错误处理

### 3. `email_config.json`
- ➕ 添加了批量发送示例
- 📝 添加了配置说明注释
- 支持 `to_address` 为字符串或数组

---

## 📖 使用场景

### 场景 1：日常自动化报告

```bash
# 每天自动运行（可以通过定时任务）
python run_daily_report.py

# 稍后确认后发送
python send_cached_report.py --preview
python send_cached_report.py
```

**适用于**：需要先审核报告内容的情况

---

### 场景 2：多个收件人群组

**配置不同的邮件组：**

`email_config_team.json`：
```json
{
  "to_address": ["dev@company.com", "analyst@company.com"]
}
```

`email_config_clients.json`：
```json
{
  "to_address": ["client1@example.com", "client2@example.com"]
}
```

**发送：**
```bash
# 发给内部团队
python send_cached_report.py --email-config email_config_team.json

# 发给客户
python send_cached_report.py --email-config email_config_clients.json
```

**适用于**：需要向不同群体发送同一份报告

---

### 场景 3：测试与生产环境

```bash
# 1. 生成报告
python run_daily_report.py

# 2. 先发给自己测试
python send_cached_report.py --to your_test_email@example.com

# 3. 确认无误后发给所有人
python send_cached_report.py
```

**适用于**：需要先测试邮件效果的情况

---

### 场景 4：历史报告重发

```bash
# 查看历史缓存
ls models/email_cache*.json

# 重发某个历史报告
python send_cached_report.py --cache models/email_cache_2025-10-01.json --to new_client@example.com
```

**适用于**：需要补发历史报告给新订阅者

---

## 🎯 命令行参数完整列表

### `send_cached_report.py` 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--cache CACHE` | 指定缓存文件路径 | `--cache models/old.json` |
| `--preview` | 预览邮件内容而不发送 | `--preview` |
| `--email-config CONFIG` | 指定邮件配置文件 | `--email-config email_vip.json` |
| `--to EMAIL [EMAIL ...]` | 指定收件人（覆盖配置文件） | `--to email1@example.com email2@example.com` |

### 组合使用示例

```bash
# 从特定缓存预览
python send_cached_report.py --cache models/old.json --preview

# 从特定缓存发送给特定人
python send_cached_report.py --cache models/old.json --to vip@example.com

# 使用特定配置发送给额外的人
python send_cached_report.py --email-config email_team.json --to extra@example.com
```

---

## ⚙️ 配置文件格式

### `email_config.json` 格式

```json
{
  "smtp_server": "smtp.example.com",      // SMTP服务器地址
  "smtp_port": 587,                       // SMTP端口（587用于TLS，465用于SSL）
  "use_tls": true,                        // 是否使用TLS加密
  "username": "your_email@example.com",   // 邮箱用户名
  "password": "your_password",            // 邮箱密码或授权码
  "from_address": "your_email@example.com", // 发件人地址
  "to_address": [                         // 收件人地址（可以是字符串或数组）
    "recipient1@example.com",
    "recipient2@example.com"
  ]
}
```

### `email_cache.json` 格式

```json
{
  "generated_at": "2025-10-02T12:00:00",
  "date": "2025-10-02",
  "subject": "BUFF市场AI分析日报 - 2025-10-02",
  "body": "报告摘要内容...",
  "attachments": [
    "models/daily_market_report_20251002_120000.png",
    "models/daily_market_report_20251002_120000.pdf",
    "models/next_week_prediction_20251002T120000Z.png"
  ],
  "last_sent_at": "2025-10-02T12:05:00"  // 最后发送时间（发送后自动添加）
}
```

---

## 🛡️ 最佳实践

### 1. 安全性
- ✅ 使用环境变量存储敏感信息（SMTP密码）
- ✅ 不要将 `email_config.json` 提交到公开的版本控制系统
- ✅ 使用邮箱授权码而不是真实密码

### 2. 可靠性
- ✅ 定期备份 `email_cache.json`
- ✅ 发送前使用 `--preview` 预览内容
- ✅ 先发给自己测试，确认无误后再批量发送

### 3. 效率
- ✅ 为不同收件人群组创建不同的配置文件
- ✅ 使用 Shell 脚本自动化批量发送流程
- ✅ 利用缓存系统避免重复生成报告

### 4. 维护性
- ✅ 定期清理旧的缓存文件
- ✅ 记录发送历史（通过 `last_sent_at` 字段）
- ✅ 为不同场景创建文档化的发送流程

---

## 📊 工作流对比

### 旧工作流
```
[数据获取] → [特征工程] → [模型预测] → [AI分析] → [生成报告] → [直接发送邮件]
                                                              ↓
                                                         发送失败 = 一切重来
```

### 新工作流
```
[数据获取] → [特征工程] → [模型预测] → [AI分析] → [生成报告] → [保存缓存]
                                                              ↓
                                                    [独立的邮件发送流程]
                                                              ↓
                                          [预览] → [确认] → [批量发送] → [可重发]
```

---

## 🎓 学习资源

- 📖 [邮件缓存工作流详细指南](./email_caching_workflow.md)
- 📖 [批量发送完整文档](./batch_email_guide.md)
- 📖 [快速参考指南](./QUICK_REFERENCE.md)

---

## 🚀 快速开始

### 第一次使用

```bash
# 1. 配置邮件设置（编辑 email_config.json）
# 添加您的 SMTP 配置和收件人列表

# 2. 生成报告
python run_daily_report.py

# 3. 预览邮件
python send_cached_report.py --preview

# 4. 发送邮件
python send_cached_report.py
```

### 日常使用

```bash
# 每天只需运行两个命令
python run_daily_report.py          # 生成报告
python send_cached_report.py        # 发送邮件
```

### 高级使用

```bash
# 发送给特定人员
python send_cached_report.py --to boss@company.com

# 使用不同配置
python send_cached_report.py --email-config email_config_vip.json

# 重发历史报告
python send_cached_report.py --cache models/email_cache_2025-10-01.json
```

---

## 💬 反馈与支持

如有问题或建议，请查看：
- 项目文档：`docs/` 目录
- 问题追踪：GitHub Issues
- 使用示例：`docs/QUICK_REFERENCE.md`

---

**享受更高效、更灵活的报告发送体验！** 🎉
