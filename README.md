# Buffotte

**CS2 饰品市场智能分析平台**

<div align="center">

![Version](https://img.shields.io/badge/version-2.0+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.0+-green.svg)

**在线体验：[https://buffotte.hezhili.online/login](https://buffotte.hezhili.online/login)**

</div>

## 核心功能

| 数据分析      | 实时追踪     | 预测模型     | 用户系统 |
| ------------- | ------------ | ------------ | -------- |
| 实时 K 线数据 | 价格监控     | 机器学习预测 | 用户认证 |
| 价格趋势分析  | 个人收藏管理 | 趋势分析     | 数据同步 |
| 市场洞察      | 收益统计     | 风险评估     | 权限管理 |

## 项目架构优势

### 全新架构 2.0

- **代码重构** - 基于 0.10 版本经验，完全重新设计架构
- **模块化设计** - 清晰的代码结构，易于维护和扩展
- **容器化部署** - Docker 一键启动，环境隔离
- **高性能** - FastAPI + Vue3，响应速度提升 300%

### 数据流架构

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#f3f9ff',
    'primaryTextColor': '#0d47a1',
    'primaryBorderColor': '#2196f3',
    'lineColor': '#42a5f5',
    'fillType0': '#e3f2fd',
    'fillType1': '#bbdefb',
    'fillType2': '#90caf9'
  }
}}%%
flowchart LR
    A[🌐 外部API] --> B[🕷️ 数据爬虫]
    B --> C[🗄️ MySQL数据库]
    C --> D[⚙️ 数据处理器]
    D --> E[🤖 AI模型]
    E --> F[🚀 RESTful API]
    F --> G[🎨 Vue3前端]

    style A fill:#e3f2fd,stroke:#2196f3,color:#0d47a1
    style B fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style C fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style D fill:#fff3e0,stroke:#ff9800,color:#e65100
    style E fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style F fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style G fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
```

### 项目目录结构

```mermaid
%%{init: {
  'theme': 'forest',
  'themeVariables': {
    'primaryColor': '#f1f8e9',
    'primaryTextColor': '#1b5e20',
    'primaryBorderColor': '#4caf50',
    'lineColor': '#66bb6a',
    'clusterBkg': '#f9fbe7',
    'clusterBorder': '#9ccc65'
  }
}}%%
flowchart TD
    A[📦 Buffotte] --> B[⚡ api.py]
    A --> C[🕷️ crawler/]
    A --> D[🗄️ db/]
    A --> E[🎨 frontend/]
    A --> F[🤖 llm/]
    A --> G[📊 models/]
    A --> H[📚 docs/]

    C --> C1[📅 daily_crawler.py]
    C --> C2[💰 item_price.py]

    D --> D1[📈 kline_data_processor.py]
    D --> D2[🎯 item_kline_processor.py]
    D --> D3[👤 user_manager.py]
    D --> D4[📰 news_processor.py]

    E --> E1[📁 src/]
    E1 --> E11[🧩 components/]
    E1 --> E12[🔗 services/]
    E1 --> E13[👁️ views/]

    F --> F1[🕵️ agents/]
    F --> F2[💬 clients/]

    G --> G1[🤖 train_model.py]

    style A fill:#f1f8e9,stroke:#4caf50,color:#1b5e20,stroke-width:3px
    style B fill:#e8f5e8,stroke:#66bb6a,color:#1b5e20
    style C fill:#f3f9ff,stroke:#42a5f5,color:#0d47a1
    style D fill:#fff3e0,stroke:#ff9800,color:#e65100
    style E fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style F fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style G fill:#e0f2f1,stroke:#009688,color:#004d40
    style H fill:#fff8e1,stroke:#ffc107,color:#f57c00
```

### 自动化工作流程

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#0d47a1',
    'primaryBorderColor': '#2196f3',
    'gridColor': '#bbdefb',
    'todayLineColor': '#f44336',
    'sectionBkgColor': '#f8fff8',
    'altSectionBkgColor': '#f1f8e9',
    'taskBkgColor': '#e8f5e8',
    'taskTextColor': '#1b5e20',
    'taskBorderColor': '#4caf50',
    'activeTaskBkgColor': '#fff3e0',
    'activeTaskBorderColor': '#ff9800'
  }
}}%%
gantt
    title 🕐 Buffotte 自动化任务时间线
    dateFormat HH:mm
    axisFormat %H:%M

    section 📅 每日任务
    📰 新闻获取     :07:00, 60m
    ⚙️ 数据处理     :07:02, 58m
    📊 摘要生成     :07:05, 55m

    section ⏰ 每小时任务
    📈 K线更新      :00:00, 55m
    📈 K线更新      :01:00, 55m
    📈 K线更新      :02:00, 55m
    📈 K线更新      :03:00, 55m
    📈 K线更新      :04:00, 55m
    📈 K线更新      :05:00, 55m
    📈 K线更新      :06:00, 55m
    📈 K线更新      :07:00, 55m
    📈 K线更新      :08:00, 55m
    📈 K线更新      :09:00, 55m
    📈 K线更新      :10:00, 55m
    📈 K线更新      :11:00, 55m
    📈 K线更新      :12:00, 55m
    📈 K线更新      :13:00, 55m
    📈 K线更新      :14:00, 55m
    📈 K线更新      :15:00, 55m
    📈 K线更新      :16:00, 55m
    📈 K线更新      :17:00, 55m
    📈 K线更新      :18:00, 55m
    📈 K线更新      :19:00, 55m
    📈 K线更新      :20:00, 55m
    📈 K线更新      :21:00, 55m
    📈 K线更新      :22:00, 55m
    📈 K线更新      :23:00, 55m

```

### 用户操作流程

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e8f5e8',
    'primaryTextColor': '#1b5e20',
    'primaryBorderColor': '#4caf50',
    'lineColor': '#66bb6a',
    'actorBkg': '#f3f9ff',
    'actorBorder': '#2196f3',
    'actorTextColor': '#0d47a1',
    'actorLineColor': '#42a5f5',
    'signalColor': '#ff9800',
    'signalTextColor': '#e65100'
  }
}}%%
sequenceDiagram
    participant 👤 as 用户
    participant 🎨 as 前端
    participant 🚀 as API服务
    participant 🗄️ as 数据库
    participant 🤖 as AI模型

    👤->>🎨: 🔐 访问登录页面
    🎨->>🚀: 🔑 请求登录认证
    🚀->>🗄️: 🔍 验证用户信息
    🗄️-->>🚀: ✅ 返回用户数据
    🚀-->>🎨: 🎫 返回认证结果
    🎨-->>👤: 👋 显示登录状态

    👤->>🎨: 🔍 搜索饰品
    🎨->>🚀: 📡 发送搜索请求
    🚀->>🗄️: 📊 查询饰品数据
    🗄️-->>🚀: 📦 返回饰品信息
    🚀-->>🎨: 📋 返回搜索结果
    🎨-->>👤: 🎯 显示饰品列表

    👤->>🎨: 📈 查看价格预测
    🎨->>🚀: 🔮 请求预测数据
    🚀->>🤖: 🧠 调用预测模型
    🤖-->>🚀: 🎯 返回预测结果
    🚀-->>🎨: 📊 返回预测数据
    🎨-->>👤: 📈 显示价格预测
```

### 数据库设计架构

```mermaid
%%{init: {
  'theme': 'forest',
  'themeVariables': {
    'primaryColor': '#f1f8e9',
    'primaryTextColor': '#1b5e20',
    'primaryBorderColor': '#4caf50',
    'lineColor': '#66bb6a',
    'entityBkg': '#e8f5e8',
    'entityBorder': '#4caf50',
    'attributeBkg': '#f3f9ff',
    'attributeBorder': '#2196f3',
    'relationshipColor': '#ff9800'
  }
}}%%
erDiagram
    👤 USER {
        string id PK "🔑 唯一标识"
        string username "👤 用户名"
        string email UK "📧 邮箱地址"
        string password_hash "🔒 密码哈希"
        datetime created_at "📅 创建时间"
    }

    📊 KLINE_DATA_DAY {
        bigint timestamp PK "⏰ 时间戳"
        date date "📅 日期"
        decimal open_price "💰 开盘价"
        decimal high_price "📈 最高价"
        decimal low_price "📉 最低价"
        decimal close_price "💵 收盘价"
        int volume "📦 成交量"
        decimal turnover "💸 成交额"
    }

    📰 NEWS {
        int id PK "🆔 新闻ID"
        string title "📰 标题"
        text content "📝 内容"
        string source "🌐 来源"
        datetime published_at "📅 发布时间"
        datetime created_at "⏰ 创建时间"
    }

    🎮 CS2_ITEMS {
        string c5_id PK "🎯 饰品ID"
        string market_hash_name "🏷️ 市场名称"
        string name "📛 饰品名称"
        decimal current_price "💰 当前价格"
        datetime updated_at "📅 更新时间"
    }

    🔮 PREDICTIONS {
        int id PK "🆔 预测ID"
        string item_id FK "🎯 饰品ID"
        decimal predicted_price "📈 预测价格"
        decimal confidence "🎯 置信度"
        string prediction_date "📅 预测日期"
        datetime created_at "⏰ 创建时间"
    }

    👤 ||--o{ 🔮 : "📊 追踪预测"
    🎮 ||--o{ 🔮 : "🔮 价格预测"
```

### AI 预测流程

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#f3e5f5',
    'primaryTextColor': '#4a148c',
    'primaryBorderColor': '#9c27b0',
    'lineColor': '#ba68c8',
    'sectionBkgColor': '#f8f9fa',
    'altSectionBkgColor': '#e8f5e8',
    'gridColor': '#e0e0e0'
  }
}}%%
flowchart TD
    A[📊 历史数据收集] --> B[🧹 数据预处理]
    B --> C[⚙️ 特征工程]
    C --> D[🤖 模型训练]
    D --> E[✅ 模型验证]
    E --> F{🤔 验证通过?}
    F -->|✅ 是| G[🚀 部署模型]
    F -->|❌ 否| H[🔧 调整参数]
    H --> D
    G --> I[📈 实时预测]
    I --> J[💾 结果存储]
    J --> K[🎨 前端展示]

    L[📰 新闻数据] --> M[😊 情绪分析]
    M --> N[🔗 特征融合]
    N --> C

    style A fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style B fill:#fff3e0,stroke:#ff9800,color:#e65100
    style C fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style D fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style E fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style G fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style I fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style J fill:#fff8e1,stroke:#ffc107,color:#f57c00
    style K fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style L fill:#e0f2f1,stroke:#009688,color:#004d40
    style M fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style N fill:#fff3e0,stroke:#ff9800,color:#e65100
```

### 智能分析能力

- **多维度数据** - 价格、成交量、新闻情绪分析
- **机器学习预测** - LightGBM 模型预测价格趋势
- **AI 新闻聚合** - 自动抓取和分析 CS2 相关资讯
- **自动化更新** - 7×24 小时数据同步

## 技术栈

### 后端技术

```python
# 核心框架
FastAPI          # 高性能异步框架
PyMySQL          # 数据库连接
LightGBM         # 机器学习模型
OpenAI SDK       # AI 智能体
```

### 前端技术

```javascript
// 现代化前端
Vue 3.0+         // 渐进式框架
Vite             // 构建工具
Axios            // HTTP 客户端
Chart.js         // 数据可视化
```

### 部署架构

```yaml
# 容器化服务
Docker Compose   # 容器编排
Nginx            # 反向代理
MySQL            # 数据存储
```

### 系统部署架构

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#0d47a1',
    'primaryBorderColor': '#2196f3',
    'lineColor': '#42a5f5',
    'clusterBkg': '#f8fff8',
    'clusterBorder': '#9ccc65',
    'secondaryColor': '#fce4ec',
    'tertiaryColor': '#fff3e0'
  }
}}%%
flowchart TB
    subgraph "🐳 Docker Host"
        subgraph "🎨 Frontend Container"
            F1[🌐 Nginx]
            F2[⚡ Vue.js App]
        end

        subgraph "🚀 Backend Container"
            B1[⚡ FastAPI Server]
            B2[🐍 Python Runtime]
        end

        subgraph "🗄️ Database Container"
            D1[🗄️ MySQL Server]
            D2[💾 Data Volume]
        end
    end

    subgraph "🌐 External Services"
        E1[🎮 SteamDT API]
        E2[🤖 OpenAI API]
        E3[⏰ Time Scheduler]
    end

    U[👤 用户] --> F1
    F1 --> F2
    F2 --> B1
    B1 --> D1
    B1 --> E1
    B1 --> E2
    E3 --> B1

    style U fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style F1 fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style F2 fill:#e3f2fd,stroke:#42a5f5,color:#0d47a1
    style B1 fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style B2 fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style D1 fill:#fff3e0,stroke:#ff9800,color:#e65100
    style D2 fill:#fff8e1,stroke:#ffc107,color:#f57c00
    style E1 fill:#e0f2f1,stroke:#009688,color:#004d40
    style E2 fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style E3 fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
```

### 数据同步策略

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e8f5e8',
    'primaryTextColor': '#1b5e20',
    'primaryBorderColor': '#4caf50',
    'lineColor': '#66bb6a',
    'clusterBkg': '#f3f9ff',
    'clusterBorder': '#2196f3',
    'secondaryColor': '#fce4ec',
    'tertiaryColor': '#fff3e0'
  }
}}%%
flowchart LR
    subgraph "📊 数据源"
        A1[🎮 SteamDT API]
        A2[🤖 OpenAI API]
        A3[👤 用户操作]
    end

    subgraph "⚙️ 数据处理"
        B1[⚡ 实时同步]
        B2[📦 批量处理]
        B3[🧠 AI分析]
    end

    subgraph "🗄️ 存储层"
        C1[🗄️ MySQL主库]
        C2[⚡ Redis缓存]
    end

    subgraph "🎨 展示层"
        D1[🚀 API接口]
        D2[📱 前端展示]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B1
    B1 --> C1
    B2 --> C1
    B3 --> C1
    C1 --> C2
    C2 --> D1
    C1 --> D1
    D1 --> D2

    style A1 fill:#e0f2f1,stroke:#009688,color:#004d40
    style A2 fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style A3 fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style B1 fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style B2 fill:#fff3e0,stroke:#ff9800,color:#e65100
    style B3 fill:#fce4ec,stroke:#e91e63,color:#880e4f
    style C1 fill:#fff3e0,stroke:#ff9800,color:#e65100
    style C2 fill:#e8f5e8,stroke:#4caf50,color:#1b5e20
    style D1 fill:#f3f9ff,stroke:#2196f3,color:#0d47a1
    style D2 fill:#fce4ec,stroke:#e91e63,color:#880e4f
```

## 快速开始

### 一键部署

```bash
# 克隆项目
git clone https://github.com/your-username/Buffotte.git
cd Buffotte

# 启动服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:4000
# 后端: http://localhost:8002
```

### 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

## 数据流程

### 自动化任务

```bash
# 每日任务 (7:00 AM)
新闻获取 → 数据处理 → 摘要生成

# 每小时任务 (除7点)
K线更新 → 数据同步 → 实时展示
```

### 数据流向

```
外部API → 爬虫模块 → 数据库 → 处理器 → AI分析 → API → 前端
```

## 功能模块

| 模块     | 功能               | 技术          |
| -------- | ------------------ | ------------- |
| 用户系统 | 注册/登录/个人中心 | JWT + bcrypt  |
| K 线分析 | 实时价格/历史数据  | SteamDT API   |
| 新闻聚合 | AI 抓取/智能摘要   | OpenAI + 爬虫 |
| 价格预测 | 机器学习/趋势分析  | LightGBM      |
| 饰品追踪 | 个人收藏/价格监控  | 实时数据同步  |

## 项目特色

- **现代化 UI** - 响应式设计，支持多端访问
- **高性能** - 异步处理，秒级响应
- **智能化** - AI 驱动的数据分析和预测
- **安全性** - 完善的用户认证和数据保护
- **可视化** - 丰富的图表和数据展示
- **实时性** - 数据自动更新，市场动态一手掌握

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- **在线体验**: [https://buffotte.hezhili.online/login](https://buffotte.hezhili.online/login)
- **邮箱**: HEZH0014@e.ntu.edu.sg
- **问题反馈**: [Issues](https://github.com/Shr1mpTop/Buffotte/issues)

---

<div align="center">

**祝您在 CS2 饰品市场投资顺利，早日财富自由！**

Made with ❤️ by Buffotte Team

</div>
