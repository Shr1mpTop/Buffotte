# SteamDT API 集成

这个目录包含了与SteamDT开放平台集成的代码，用于获取CS2饰品的价格数据。

## 文件说明

- `steamdt_client.py` - SteamDT API客户端，封装了所有API调用
- `collector.py` - 数据收集器，负责定期获取数据并存储到数据库
- `test_cache.py` - 缓存测试脚本

## 使用方法

### 1. 环境配置

设置数据库连接环境变量：

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_DATABASE=buffotte
```

### 2. 测试API连接

```bash
cd api
python steamdt_client.py
```

### 3. 测试缓存机制

```bash
cd api
python test_cache.py
```

### 3. 单次数据收集

```bash
cd api
python collector.py
```

### 4. 持续数据收集

每小时收集一次：

```bash
cd api
python collector.py --continuous 1
```

每4小时收集一次：

```bash
cd api
python collector.py --continuous 4
```

## API说明

### SteamDT API限制

| 接口 | 限制 | 说明 |
|---|---|---|
| `/open/cs2/v1/base` | 每日1次 | 获取饰品基础信息 |
| `/open/cs2/v1/price/batch` | 每分钟1次 | 批量查询价格 |
| `/open/cs2/v1/price/single` | 每分钟60次 | 单个查询价格 |

### 缓存机制

为了避免超过API限制，系统实现了多层缓存：

1. **内存缓存**: 24小时内不会重复调用base API
2. **文件缓存**: 本地JSON文件备份，24小时有效
3. **数据库缓存**: API调用记录和限制信息

### SteamDT API特性

- **基础信息**: `GET /open/cs2/v1/base` - 获取所有饰品的基础信息（每天限一次调用）
- **批量价格查询**: `POST /open/cs2/v1/price/batch` - 批量获取饰品价格

### 数据流程

1. 获取所有饰品的基础信息（包含market_hash_name）
2. 批量查询所有饰品的价格数据
3. 将数据存储到MySQL数据库

### 数据库表结构

#### steamdt_base_items
- 存储饰品基础信息
- 字段：id, name, market_hash_name, platform_list, created_at, updated_at

#### steamdt_price_history
- 存储价格历史数据
- 字段：id, market_hash_name, platform, platform_item_id, sell_price, sell_count, bidding_price, bidding_count, update_time, collected_at

## 注意事项

1. **API限制**: 严格遵守SteamDT的调用限制，避免被封禁
2. **缓存优先**: 系统会优先使用缓存，避免不必要的API调用
3. **错误处理**: 当达到API限制时，系统会优雅降级使用缓存数据
4. **数据新鲜度**: 基础信息每天更新一次，价格数据可以更频繁更新
5. SteamDT API有调用频率限制，请合理控制请求间隔
6. 基础信息API每天只能调用一次，客户端会自动缓存24小时
7. 价格查询支持批量操作，每次最多查询100个饰品
8. API密钥已内置在代码中，请妥善保管