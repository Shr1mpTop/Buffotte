# 系统架构

## 整体架构

Buffotte 采用前后端分离的架构，通过 Docker Compose 编排部署：

```
                         ┌──────────────────────────────────┐
                         │           用户浏览器              │
                         └──────────┬───────────┬───────────┘
                                    │           │
                              HTTP/HTTPS    HTTP/HTTPS
                                    │           │
                    ┌───────────────▼──┐  ┌─────▼─────────────┐
                    │   Nginx (80)     │  │  FastAPI (8000)    │
                    │   前端静态资源    │  │  REST API 服务     │
                    └──────────────────┘  └──────┬────────────┘
                                                 │
                              ┌───────────────────┼───────────────────┐
                              │                   │                   │
                    ┌─────────▼──────┐  ┌────────▼───────┐  ┌───────▼──────┐
                    │   MySQL 数据库  │  │  Playwright    │  │  豆包 LLM    │
                    │   数据存储      │  │  爬虫引擎      │  │  AI 分析     │
                    └────────────────┘  └────────────────┘  └──────────────┘
```

## 模块划分

### 后端 (FastAPI)

**入口**: `api.py` — 所有 REST API 端点

核心模块：

| 模块 | 路径 | 职责 |
|------|------|------|
| 爬虫 | `crawler/` | 通过 Playwright 绕过 WAF 抓取 SteamDT 数据 |
| 数据库 | `db/` | 数据入库、缓存管理、查询处理 |
| LLM | `llm/` | AI 新闻分析流水线 (Scout → Parser → Investigator) |
| 模型 | `models/` | LightGBM 价格预测模型训练与推理 |

### 前端 (Vue 3)

**入口**: `frontend/src/`

| 页面 | 路径 | 功能 |
|------|------|------|
| Login | `/login` | 用户登录 |
| Register | `/register` | 用户注册 |
| Dashboard | `/dashboard` | 首页大盘概览 |
| Kline | `/kline` | K 线图 + 预测走势 |
| Items | `/items` | 饰品搜索与比价 |
| News | `/news` | 新闻聚合与分类 |
| Skins | `/skins` | 热门饰品排行 |
| Tracking | `/tracking` | 我的追踪列表 |

## 数据流

### 每日数据流（自动化）

```
07:00 定时触发
    │
    ├──▶ 新闻爬取 (llm/agents/news_crawler.py)
    │       │
    │       ▼
    ├──▶ 新闻入库 (db/news_processor.py)
    │       │
    │       ▼
    ├──▶ AI 摘要生成 (db/summary_processor.py)
    │       │
    │       ▼
    └──▶ 大盘分析 (db/market_analysis_processor.py)
            │  使用豆包 LLM 分析当日行情
            ▼
        前端展示
```

### 每小时数据流

```
每小时触发
    │
    └──▶ K线数据更新 (db/kline_data_processor.py)
            │  调用 SteamDT API 获取最新数据
            ▼
        数据库 kline_data_day 表更新
            │
            ▼
        前端 3s 轮询获取最新数据
```

### 饰品追踪数据流

```
用户添加追踪
    │
    ├──▶ 写入 user_actions 记录
    │
    └──▶ 后台异步获取 K 线数据
            │  通过 buff-tracker API 获取
            ▼
        缓存到 item_kline_day 表
            │  1 小时缓存有效期
            ▼
        前端展示 K 线图
```

## 外部依赖

| 服务 | 用途 | 配置项 |
|------|------|--------|
| SteamDT API | K 线数据源 | 爬虫自动获取 |
| 网易 BUFF | 饰品价格与资讯 | 爬虫自动获取 |
| 豆包 LLM | AI 分析引擎 | `ARK_API_KEY`, `DOUBAO_MODEL` |
| buff-tracker | 饰品 K 线数据代理 | `BUFFTRACKER_URL` |
