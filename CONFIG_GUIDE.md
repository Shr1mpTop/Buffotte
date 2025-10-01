# 配置文件说明 (Configuration Guide)

本项目包含多个配置文件，用于存储敏感信息（如API密钥、数据库密码等）。为了保护您的隐私和安全，这些文件**不会**被提交到Git仓库。

## 📋 配置文件列表

### 1. `config.json` - 数据库配置

**用途**: MySQL数据库连接配置

**创建方法**:
```bash
cp config.example.json config.json
```

**必填字段**:
```json
{
    "host": "localhost",           // 数据库主机地址
    "port": 3306,                  // 数据库端口
    "user": "your_username",       // 数据库用户名
    "password": "your_password",   // 数据库密码
    "database": "buffotte",        // 数据库名称
    "charset": "utf8mb4"           // 字符集
}
```

---

### 2. `email_config.json` - 邮件配置

**用途**: SMTP邮件发送配置（用于每日报告）

**创建方法**:
```bash
cp email_config.example.json email_config.json
```

**必填字段**:
```json
{
  "smtp_server": "smtp.qq.com",              // SMTP服务器地址
  "smtp_port": 587,                          // SMTP端口
  "use_tls": true,                           // 是否使用TLS加密
  "username": "YourQQUsername",              // QQ邮箱用户名
  "password": "your_authorization_code",     // QQ邮箱授权码（不是登录密码！）
  "from_address": "your_email@qq.com",       // 发件人邮箱
  "to_address": "recipient@example.com"      // 收件人邮箱
}
```

**注意事项**:
- QQ邮箱需要开启SMTP服务并获取授权码
- 授权码获取: QQ邮箱设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 → 生成授权码
- `password` 字段填写的是**授权码**，不是QQ密码

---

### 3. `llm_config.json` - AI分析配置

**用途**: Google Gemini API配置（用于多智能体市场分析）

**创建方法**:
```bash
cp llm_config.example.json llm_config.json
```

**必填字段**:
```json
{
  "llm": {
    "provider": "google",
    "model": "gemini-2.0-flash-exp",
    "api_key": "YOUR_GOOGLE_GEMINI_API_KEY",  // ← 在这里填写你的API密钥
    "temperature": {
      "data_analyst": 0.3,
      "market_analyst": 0.5,
      "fund_manager": 0.4
    },
    "max_tokens": 4096
  },
  "workflow": {
    "enable_news_search": false,
    "save_reports": true,
    "generate_html": true,
    "output_dir": "models"
  },
  "agents": {
    "data_analyst": { "enabled": true, "analysis_window_days": 30 },
    "market_analyst": { 
      "enabled": true,
      "news_sources": ["BUFF", "悠悠有品", "Steam社区"],
      "keywords": ["BUFF", "steam饰品", "CSGO饰品"]
    },
    "fund_manager": { "enabled": true, "include_chart_analysis": true }
  }
}
```

**API密钥获取**:
1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登录Google账号
3. 点击"Create API Key"生成密钥
4. 复制密钥并粘贴到 `api_key` 字段

---

### 4. `api-keys.txt` - API密钥文件（可选）

**用途**: 集中管理多个API密钥（可选，也可以直接在 `llm_config.json` 中配置）

**创建方法**:
```bash
cp api-keys.example.txt api-keys.txt
```

**示例内容**:
```
GOOGLE_GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXX
```

---

## 🔒 安全性说明

### 已被 `.gitignore` 忽略的文件
以下文件包含敏感信息，**不会被提交到Git仓库**：

```
config.json              # 数据库密码
email_config.json        # 邮箱密码/授权码
llm_config.json          # AI API密钥
api-keys.txt             # API密钥集合
.env                     # 环境变量
*.secret                 # 所有.secret文件
```

### 会被提交到仓库的示例文件
以下示例文件**会被提交**，供其他开发者参考：

```
config.example.json          # 数据库配置示例
email_config.example.json    # 邮件配置示例
llm_config.example.json      # AI配置示例
api-keys.example.txt         # API密钥示例
```

---

## 🚀 快速开始

### 第一次使用项目时的配置步骤

1. **克隆仓库**:
   ```bash
   git clone <repository_url>
   cd Buffotte
   ```

2. **复制并配置数据库**:
   ```bash
   cp config.example.json config.json
   # 编辑 config.json，填写你的MySQL配置
   ```

3. **复制并配置邮件**（如果需要邮件报告）:
   ```bash
   cp email_config.example.json email_config.json
   # 编辑 email_config.json，填写你的QQ邮箱配置
   ```

4. **复制并配置AI分析**（如果需要AI分析功能）:
   ```bash
   cp llm_config.example.json llm_config.json
   # 编辑 llm_config.json，填写你的Google Gemini API密钥
   ```

5. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

6. **运行项目**:
   ```bash
   python -m src.run_daily_report
   ```

---

## ⚠️ 重要提示

1. **永远不要提交真实配置文件到Git仓库**
   - 如果不小心提交了，立即使用 `git filter-branch` 或 BFG Repo-Cleaner 清除历史记录
   - 修改所有已泄露的密码和API密钥

2. **定期更新密钥**
   - 建议每3-6个月更换一次API密钥和数据库密码
   - 如果怀疑密钥泄露，立即更换

3. **备份配置文件**
   - 将配置文件保存到安全的本地位置
   - 不要将配置文件上传到云盘（除非加密）

4. **多环境配置**
   - 开发环境: `config.json`, `email_config.json`, `llm_config.json`
   - 生产环境: 使用环境变量或密钥管理服务（如AWS Secrets Manager）

---

## 🛠️ 故障排除

### 问题1: "FileNotFoundError: config.json not found"
**解决方案**: 你还没有创建配置文件
```bash
cp config.example.json config.json
# 编辑文件填写真实配置
```

### 问题2: "SMTPAuthenticationError: Username and Password not accepted"
**解决方案**: 
- 检查 `email_config.json` 中的 `password` 是否填写了QQ邮箱**授权码**（不是登录密码）
- 确认QQ邮箱已开启SMTP服务

### 问题3: "Google API Error: Invalid API Key"
**解决方案**:
- 检查 `llm_config.json` 中的 `api_key` 是否正确
- 确认API密钥已激活并有使用配额
- 访问 [Google AI Studio](https://aistudio.google.com/apikey) 重新生成密钥

---

## 📚 相关文档

- [AI分析快速开始](docs/AI_QUICKSTART.md)
- [AI架构设计](docs/AI_ARCHITECTURE.md)
- [邮件报告指南](docs/EMAIL_REPORT_GUIDE.md)
- [项目使用说明](docs/USAGE.md)

---

## 📧 联系方式

如有配置问题，请参考上述文档或联系项目维护者。

**祝使用愉快！** 🎉
