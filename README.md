<div align="center">

# Buffotte

**CS2 饰品市场智能分析平台**

[![Live](https://img.shields.io/badge/LIVE-buffotte.hezhili.online-00ff41?style=flat-square)](https://buffotte.hezhili.online/login)
[![Version](https://img.shields.io/badge/version-0.13.0-blue?style=flat-square)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-444?style=flat-square)](LICENSE)

<br />

**[即刻体验 →](https://buffotte.hezhili.online/login)**

</div>

---

## 项目简介

Buffotte 是一个 CS2 饰品市场分析平台，通过爬虫实时采集市场数据，结合 LLM 智能分析和 LightGBM 价格预测模型，为用户提供全方位的市场洞察。

## 核心功能

| 功能 | 描述 |
|------|------|
| **大盘指数** | 实时 K 线图 + 3 秒轮询动态更新 |
| **AI 分析** | 豆包 LLM 每日自动生成行情解读 |
| **价格预测** | LightGBM 模型预测未来 30 天走势，附带 95% 置信区间 |
| **饰品追踪** | 多平台比价，一键追踪关注的饰品 |
| **新闻聚合** | AI 自动抓取多源新闻并生成分类摘要 |
| **系统监控** | 服务器 CPU / 内存 / 负载实时展示 |

## 技术架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Vue 3 +    │────▶│  FastAPI +   │────▶│   MySQL     │
│  ECharts    │◀────│  Uvicorn     │◀────│   Database  │
│  GSAP       │     │              │     │             │
└─────────────┘     ├──────────────┤     └─────────────┘
                    │  Playwright  │
                    │  Crawler     │
                    ├──────────────┤
                    │  LightGBM    │
                    │  Predictor   │
                    ├──────────────┤
                    │  豆包 LLM    │
                    │  Analyzer    │
                    └──────────────┘
```

**后端**: FastAPI · Playwright · LightGBM · PyMySQL · 豆包 LLM (OpenAI SDK)
**前端**: Vue 3 · ECharts · GSAP · Vite
**基础设施**: Docker · Docker Compose · Nginx · PM2

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+
- MySQL 5.7+
- Docker & Docker Compose (部署用)

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/Shr1mpTop/Buffotte.git
cd Buffotte

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库和 API 密钥配置

# 3. 安装后端依赖
pip install -e ".[dev]"

# 4. 启动后端
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 5. 安装前端依赖并启动
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker compose up -d --build
```

- 后端: `http://localhost:8002`
- 前端: `http://localhost:4000`
- 在线文档: `http://localhost:8002/wiki`

## 项目结构

```
Buffotte/
├── api.py                  # FastAPI 主应用，所有 REST API 端点
├── crawler/                # 数据爬虫模块
│   ├── daily_crawler.py    #   大盘日K线爬虫 (SteamDT)
│   └── item_price.py       #   单品价格爬虫 (SteamDT)
├── db/                     # 数据库处理模块
│   ├── user_manager.py     #   用户管理（注册/登录）
│   ├── user_actions.py     #   用户操作（追踪/取消追踪）
│   ├── kline_data_processor.py   # 大盘K线数据入库
│   ├── item_kline_processor.py   # 饰品K线数据入库与缓存
│   ├── news_processor.py         # 新闻数据解析入库
│   ├── summary_processor.py      # AI 摘要生成入库
│   ├── market_analysis_processor.py # LLM 大盘分析
│   ├── cs2_items_processor.py    # CS2 饰品基础数据同步
│   ├── create_dataset.py         # 训练数据集生成
│   └── skin_processor.py         # 饰品实体/详情管理
├── llm/                    # LLM 智能分析模块
│   ├── orchestrator.py     #   流水线调度器 (Scout→Parser→Investigator)
│   ├── clients/            #   LLM 客户端 (豆包)
│   └── agents/             #   AI Agent 集合
│       ├── scout_agent.py       #  侦察：搜索新闻热点
│       ├── skin_parser.py       #  解析：提取饰品实体
│       ├── skin_investigator.py #  调查：深入饰品分析
│       ├── news_crawler.py      #  新闻爬取
│       └── news_classifier.py   #  新闻分类
├── models/                 # 机器学习模型
│   ├── train_model.py      #   LightGBM 训练 + 30天预测
│   └── train.csv           #   训练数据集
├── scripts/                # 自动化脚本
│   ├── daily_automation.sh       # 每日任务 (新闻+分析)
│   ├── hourly_automation.sh      # 每小时任务 (K线更新)
│   ├── predict.sh                # 模型训练+预测
│   └── kline_daily_refresh.sh    # K线数据刷新
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          #   页面组件
│   │   ├── components/     #   公共组件
│   │   └── layouts/        #   布局组件
│   ├── vite.config.js
│   └── nginx.conf
├── docs/                   # 项目文档
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── pyproject.toml
```

## API 概览

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/register` | 用户注册 |
| POST | `/api/login` | 用户登录 |
| GET  | `/api/kline/chart-data` | 大盘 K 线 + 预测数据 |
| GET  | `/api/kline/latest` | 最新一条 K 线（轻量轮询） |
| GET  | `/api/kline/market-analysis` | LLM 大盘分析 |
| GET  | `/api/item/kline-data/{name}` | 饰品 K 线数据 |
| GET  | `/api/item/kline-cached/{name}` | 饰品 K 线缓存 |
| GET  | `/api/item-price/{item_id}` | 饰品实时价格 |
| GET  | `/api/news` | 新闻列表（分页/分类） |
| GET  | `/api/news/stats` | 新闻统计看板 |
| GET  | `/api/skin/trending` | 热门饰品 |
| GET  | `/api/skin/search?q=` | 饰品搜索 |
| POST | `/api/track/add` | 添加追踪 |
| GET  | `/api/track/list/{email}` | 追踪列表 |
| GET  | `/api/system/stats` | 系统状态 |
| GET  | `/wiki` | 在线文档 |

完整 API 文档请访问: `http://localhost:8000/docs` (Swagger UI)

## 自动化运维

通过 cron 调度脚本实现全自动运行：

| 任务 | 频率 | 脚本 |
|------|------|------|
| 新闻抓取 + AI 摘要 + 大盘分析 | 每日 07:00 | `scripts/daily_automation.sh` |
| K 线实时数据更新 | 每小时 | `scripts/hourly_automation.sh` |
| 模型训练 + 预测更新 | 手动/按需 | `scripts/predict.sh` |

## License

MIT
