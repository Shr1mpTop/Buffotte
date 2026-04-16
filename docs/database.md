# 数据库设计

## 概述

Buffotte 使用 MySQL 数据库，共 8 张核心表，覆盖用户管理、市场数据、新闻资讯和 AI 预测四大领域。

## ER 关系图

```
┌──────────┐       ┌──────────────────┐       ┌──────────┐
│   user   │       │ kline_data_day   │       │   news   │
├──────────┤       ├──────────────────┤       ├──────────┤
│ id (PK)  │       │ timestamp (PK)   │       │ id (PK)  │
│ username │       │ date             │       │ title    │
│ email    │       │ open_price       │       │ url (UQ) │
│ password │       │ high_price       │       │ source   │
│ created  │       │ low_price        │       │ pub_time │
└──────────┘       │ close_price      │       │ summary  │
                   │ volume           │       │ category │
                   │ turnover         │       └────┬─────┘
                   └──────────────────┘            │
                                            ┌──────▼──────────┐
┌─────────────────────┐  ┌───────────────┐  │ summary_news_   │
│ kline_data_prediction│  │    summary    │  │   association   │
├─────────────────────┤  ├───────────────┤  ├─────────────────┤
│ date (PK)           │  │ id (PK)       │  │ summary_id (FK) │
│ predicted_close     │  │ summary       │  │ news_id (FK)    │
│ rolling_mean_7      │  │ summary_date  │  └────────┬────────┘
│ rolling_std_7       │  │ created_at    │           │
│ rolling_mean_14     │  └───────┬───────┘           │
│ rolling_std_14      │          │                   │
│ rolling_mean_30     │          └───────────────────┘
│ rolling_std_30      │
└─────────────────────┘

┌──────────────────┐       ┌──────────────────┐
│ item_kline_day   │       │ user_actions     │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ market_hash_name │       │ user_id (FK)     │
│ item_id          │       │ market_hash_name │
│ timestamp        │       │ created_at       │
│ open/close/high/ │       └──────────────────┘
│ low/volume/...   │
│ updated_at       │       ┌──────────────────┐
└──────────────────┘       │ skin_entity      │
                           ├──────────────────┤
                           │ id (PK)          │
                           │ market_hash_name │
                           │ mention_count    │
                           │ ...              │
                           └──────────────────┘
```

## 表结构详情

### user — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(255) | PK | 基于 email 的 SHA256 哈希 |
| username | VARCHAR(255) | NOT NULL | 用户名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱地址 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希密码 |
| created_at | TIMESTAMP | DEFAULT NOW | 创建时间 |

### kline_data_day — 日 K 线数据表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| timestamp | BIGINT | PK | Unix 时间戳（秒） |
| date | DATE | | 对应日期 |
| open_price | DECIMAL(10,2) | | 开盘价 |
| high_price | DECIMAL(10,2) | | 最高价 |
| low_price | DECIMAL(10,2) | | 最低价 |
| close_price | DECIMAL(10,2) | | 收盘价 |
| volume | INT | | 成交量 |
| turnover | DECIMAL(15,2) | | 成交额 |

### kline_data_prediction — 预测数据表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| date | DATE | PK | 预测日期 |
| predicted_close_price | DECIMAL(10,2) | | 预测收盘价 |
| rolling_mean_7 | DECIMAL(10,2) | | 7 日滚动均值 |
| rolling_std_7 | DECIMAL(10,2) | | 7 日滚动标准差 |
| rolling_mean_14 | DECIMAL(10,2) | | 14 日滚动均值 |
| rolling_std_14 | DECIMAL(10,2) | | 14 日滚动标准差 |
| rolling_mean_30 | DECIMAL(10,2) | | 30 日滚动均值 |
| rolling_std_30 | DECIMAL(10,2) | | 30 日滚动标准差 |

### news — 新闻表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| title | TEXT | | 新闻标题 |
| url | VARCHAR(768) | UNIQUE | 新闻链接 |
| source | VARCHAR(255) | | 来源 |
| publish_time | DATETIME | | 发布时间 |
| summary | TEXT | | AI 摘要 |
| category | VARCHAR(100) | | 分类标签 |
| created_at | TIMESTAMP | DEFAULT NOW | 入库时间 |

### summary — AI 摘要表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| summary | TEXT | NOT NULL | LLM 生成的综合摘要 |
| summary_date | DATE | | 摘要对应日期 |
| created_at | TIMESTAMP | DEFAULT NOW | 生成时间 |

### summary_news_association — 摘要-新闻关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| summary_id | INT | FK → summary.id | 摘要 ID |
| news_id | INT | FK → news.id | 新闻 ID |

复合主键: `(summary_id, news_id)`

### item_kline_day — 饰品 K 线缓存表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| market_hash_name | VARCHAR(255) | INDEX | 饰品市场哈希名 |
| item_id | VARCHAR(50) | | SteamDT 饰品 ID |
| timestamp | BIGINT | | Unix 时间戳 |
| open/close/high/low | DECIMAL(10,2) | | OHLC 数据 |
| volume | INT | | 成交量 |
| turnover | DECIMAL(15,2) | | 成交额 |
| updated_at | TIMESTAMP | | 缓存更新时间 |

### user_actions — 用户追踪表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | VARCHAR(255) | FK → user.id | 用户 ID |
| market_hash_name | VARCHAR(255) | | 追踪的饰品名 |
| created_at | TIMESTAMP | DEFAULT NOW | 添加时间 |

## 连接配置

通过 `.env` 文件配置数据库连接：

```ini
HOST=mysql_host
PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DATABASE=buffotte
CHARSET=utf8mb4
```

所有表由各模块在启动时自动创建，无需手动执行 SQL。
