# API 接口文档

> 完整的交互式 API 文档请访问 Swagger UI: `http://localhost:8000/docs`

## 认证

目前采用简单的邮箱 + 密码认证，登录成功后客户端通过 `localStorage` 存储用户信息。

## 接口列表

### 用户认证

#### POST `/api/register` — 用户注册

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应** `200`:
```json
{ "success": true, "message": "注册成功" }
```

**错误**: `409` 邮箱已存在 | `503` 数据库不可用

---

#### POST `/api/login` — 用户登录

**请求体**:
```json
{
  "email": "string",
  "password": "string"
}
```

**响应** `200`:
```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "id": "string",
    "email": "string",
    "username": "string",
    "created_at": "2025-01-01T00:00:00"
  }
}
```

**错误**: `401` 邮箱或密码错误 | `404` 用户不存在

---

### K 线数据

#### GET `/api/kline/chart-data` — 大盘图表数据

一次性返回历史 K 线和预测数据。

**响应**:
```json
{
  "historical": [
    {
      "timestamp": 1757346910,
      "open": 1554.01,
      "high": 1558.66,
      "low": 1551.89,
      "close": 1551.89,
      "volume": 2203908,
      "turnover": 110775711.58
    }
  ],
  "prediction": [
    {
      "timestamp": 1757433310,
      "predicted_close_price": 1560.5,
      "rolling_std_7": 12.3
    }
  ]
}
```

---

#### GET `/api/kline/latest` — 最新 K 线数据

轻量级接口，仅返回最新一条记录，用于前端秒级轮询。

**响应**:
```json
{
  "success": true,
  "data": {
    "timestamp": 1757433310,
    "open": 1551.89,
    "high": 1564.23,
    "low": 1539.85,
    "close": 1564.23,
    "volume": 2484992,
    "turnover": 129727462.8
  }
}
```

---

#### POST `/api/kline/refresh` — 刷新 K 线数据

手动触发数据更新脚本。

---

#### GET `/api/kline/market-analysis` — LLM 大盘分析

获取最新的 AI 生成大盘分析报告。

**响应**:
```json
{
  "success": true,
  "analysis": "今日CS2饰品市场整体呈现...",
  "date": "2025-12-08"
}
```

---

### 饰品数据

#### GET `/api/item-price/{item_id}` — 饰品实时价格

**路径参数**: `item_id` — SteamDT 饰品 ID

**响应**:
```json
{
  "success": true,
  "data": [{
    "platform": "BUFF",
    "sellPrice": 170.0,
    "sellCount": 186,
    "biddingPrice": 149.0,
    "biddingCount": 50,
    "turnover": 4074.42,
    "volume": 21,
    "totalCount": 63749,
    "updateTime": 1765043769
  }]
}
```

---

#### GET `/api/item-price-history/{item_id}` — 饰品历史价格

返回所有历史价格数据点，用于绘制价格走势图。

---

#### GET `/api/item/kline-data/{market_hash_name}` — 饰品 K 线

**查询参数**: `platform=BUFF` `type_day=1` `date_type=3`

---

#### GET `/api/item/kline-cached/{market_hash_name}` — 饰品 K 线缓存

毫秒级响应，用于追踪饰品的首屏加载。

---

### 新闻

#### GET `/api/news` — 新闻列表

**查询参数**:
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码 |
| size | int | 10 | 每页条数 |
| category | string | — | 按分类筛选 |
| days | int | — | 最近 N 天 |
| summary_id | int | — | 关联摘要 ID |

**响应**:
```json
{
  "items": [
    {
      "id": 1,
      "title": "CS2更新公告",
      "url": "https://...",
      "source": "Steam",
      "publish_time": "2025-12-08T10:00:00",
      "preview": "摘要内容...",
      "category": "游戏更新",
      "highlighted": true
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10
}
```

---

#### GET `/api/news/stats` — 新闻统计

返回分类分布、来源排行、每日趋势等统计数据。

---

### 饰品搜索

#### GET `/api/skin/trending` — 热门饰品

**查询参数**: `limit=20`

#### GET `/api/skin/search` — 饰品搜索

**查询参数**: `q=关键词` `limit=20`

#### GET `/api/skin/{skin_id}/detail` — 饰品详情

返回实体信息 + 多平台价格详情。

---

### 用户操作

#### POST `/api/track/add` — 添加追踪

**请求体**: `{ "email": "...", "market_hash_name": "..." }`

#### GET `/api/track/list/{email}` — 追踪列表

#### POST `/api/track/remove` — 取消追踪

**请求体**: `{ "email": "...", "market_hash_name": "..." }`

#### GET `/api/user/profile?email=` — 用户资料

#### GET `/api/user/details/{email}` — 用户详情

---

### 系统

#### GET `/api/system/stats` — 系统状态

返回服务器 CPU、内存、负载、运行时间。

**响应**:
```json
{
  "success": true,
  "data": {
    "cpu_percent": 25.3,
    "mem_total_gb": 8.0,
    "mem_used_gb": 3.2,
    "mem_percent": 40.0,
    "load_1m": 0.5,
    "load_5m": 0.4,
    "load_15m": 0.3,
    "uptime": "15d 6h",
    "uptime_seconds": 1323600
  }
}
```

---

### 代理

#### `/api/bufftracker/{path}` — Buff-Tracker 代理

代理所有请求到 buff-tracker 服务，解决 HTTPS Mixed Content 问题。
