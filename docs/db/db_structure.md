# 数据库结构和关系

## 概述

Buffotte 项目使用 MySQL 数据库存储用户数据、市场数据、新闻资讯和预测信息。数据库采用关系型设计，支持用户认证、K线数据存储、新闻聚合和AI预测功能。

## 表结构

### 1. user 表 - 用户信息表

```sql
CREATE TABLE IF NOT EXISTS user (
    id VARCHAR(255) PRIMARY KEY,           -- 基于邮箱生成的唯一 SHA256 哈希 ID
    username VARCHAR(255) NOT NULL,        -- 用户名
    email VARCHAR(255) UNIQUE NOT NULL,    -- 邮箱地址（唯一）
    password_hash VARCHAR(255) NOT NULL,   -- bcrypt 哈希后的密码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
)
```

**说明**:
- 用户ID通过 `hashlib.sha256(email.encode()).hexdigest()` 生成
- 密码使用 bcrypt 算法哈希存储
- 邮箱字段具有唯一约束

### 2. kline_data_day 表 - 日K线数据表

```sql
CREATE TABLE IF NOT EXISTS kline_data_day (
    timestamp BIGINT PRIMARY KEY,          -- 时间戳（秒）
    date DATE,                             -- 日期
    open_price DECIMAL(10,2),              -- 开盘价
    high_price DECIMAL(10,2),              -- 最高价
    low_price DECIMAL(10,2),               -- 最低价
    close_price DECIMAL(10,2),             -- 收盘价
    volume INT,                            -- 成交量
    turnover DECIMAL(15,2)                 -- 成交额
)
```

**说明**:
- timestamp 为主键，使用 BIGINT 类型存储 Unix 时间戳
- 价格字段使用 DECIMAL(10,2) 保证精度
- 存储每日股票/指数的K线数据

### 3. news 表 - 新闻资讯表

```sql
CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- 自增主键
    title TEXT,                           -- 新闻标题
    url VARCHAR(768) UNIQUE,              -- 新闻链接（唯一）
    source VARCHAR(255),                  -- 新闻来源
    publish_time DATETIME,                -- 发布时间
    summary TEXT,                         -- 新闻摘要
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
)
```

**说明**:
- id 为主键，自增
- url 字段具有唯一约束，避免重复插入
- title 和 summary 使用 TEXT 类型，支持长文本

### 4. summary 表 - 新闻摘要表

```sql
CREATE TABLE IF NOT EXISTS summary (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- 自增主键
    summary TEXT NOT NULL,                -- 摘要内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
)
```

**说明**:
- 存储AI生成的新闻摘要
- 与 news 表通过关联表建立多对多关系

### 5. summary_news_association 表 - 摘要新闻关联表

```sql
CREATE TABLE IF NOT EXISTS summary_news_association (
    summary_id INT,                       -- 摘要ID
    news_id INT,                          -- 新闻ID
    PRIMARY KEY (summary_id, news_id),    -- 复合主键
    FOREIGN KEY (summary_id) REFERENCES summary(id),
    FOREIGN KEY (news_id) REFERENCES news(id)
)
```

**说明**:
- 实现 summary 和 news 的多对多关系
- 复合主键确保同一摘要不会重复关联同一新闻

### 6. kline_data_prediction 表 - 预测数据表

```sql
CREATE TABLE IF NOT EXISTS kline_data_prediction (
    date DATE PRIMARY KEY,                -- 日期（主键）
    predicted_close_price DECIMAL(10, 2), -- 预测收盘价
    rolling_mean_7 DECIMAL(10, 2),        -- 7日滚动均值
    rolling_std_7 DECIMAL(10, 2),         -- 7日滚动标准差
    rolling_mean_14 DECIMAL(10, 2),       -- 14日滚动均值
    rolling_std_14 DECIMAL(10, 2),        -- 14日滚动标准差
    rolling_mean_30 DECIMAL(10, 2),       -- 30日滚动均值
    rolling_std_30 DECIMAL(10, 2)         -- 30日滚动标准差
)
```

**说明**:
- 存储机器学习模型的预测结果
- 包含多种技术指标的滚动统计数据
- date 字段为主键

## 表关系图

```
user (用户信息)
├── id (主键)
├── username
├── email (唯一)
├── password_hash
└── created_at

kline_data_day (日K线数据)
├── timestamp (主键)
├── date
├── open_price
├── high_price
├── low_price
├── close_price
├── volume
└── turnover

news (新闻资讯)
├── id (主键)
├── title
├── url (唯一)
├── source
├── publish_time
├── summary
└── created_at

summary (新闻摘要)
├── id (主键)
├── summary
└── created_at

summary_news_association (摘要-新闻关联)
├── summary_id (外键 → summary.id)
└── news_id (外键 → news.id)

kline_data_prediction (预测数据)
├── date (主键)
├── predicted_close_price
├── rolling_mean_7
├── rolling_std_7
├── rolling_mean_14
├── rolling_std_14
├── rolling_mean_30
└── rolling_std_30
```

## 数据库设计特点

### 数据完整性
- 外键约束确保关联数据的完整性
- 唯一约束防止重复数据
- 主键保证数据唯一性

### 性能优化
- 时间戳字段使用 BIGINT 类型，便于索引和查询
- 价格字段使用 DECIMAL 类型，保证精确计算
- 复合主键优化多对多关系查询

### 可扩展性
- 自增主键支持水平扩展
- TEXT 类型字段支持长文本内容
- 时间戳字段支持时间范围查询

### 数据一致性
- 使用事务确保批量操作的原子性
- ON DUPLICATE KEY UPDATE 支持数据更新
- 级联删除维护关联关系

## 使用说明

### 连接配置
数据库连接通过环境变量配置：
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_NAME`: 数据库名称
- `DB_USER`: 用户名
- `DB_PASSWORD`: 密码

### 表创建
各模块会自动创建所需的数据表，无需手动执行 SQL。

### 数据流程
1. 用户注册 → user 表
2. 爬虫抓取 → kline_data_day 表
3. 新闻采集 → news 表
4. AI摘要 → summary + summary_news_association 表
5. 模型预测 → kline_data_prediction 表