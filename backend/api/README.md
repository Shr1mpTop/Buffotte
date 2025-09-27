# SteamDT API 集成

这个目录包含了与SteamDT开放平台集成的代码，用于获取CS2饰品的价格数据。

## 文件说明

- `data_source.py` - SteamDTDataSource 类，封装了所有数据获取和处理功能
- `config.json` - 数据库配置
- `api-keys.txt` - API keys 列表
- `requirements.txt` - Python 依赖

## 使用方法

### 1. 环境配置

确保数据库配置正确（`config.json`），并安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 运行完整数据获取流程

```python
from data_source import SteamDTDataSource

ds = SteamDTDataSource()
ds.run_full_pipeline()
```

这将执行以下步骤：
- 连接数据库
- 创建必要的表
- 解析 JSON 数据为 CSV
- 导入饰品数据到数据库
- 多线程获取价格数据

### 3. 单独使用方法

```python
from data_source import SteamDTDataSource

ds = SteamDTDataSource()

# 连接数据库
ds.connect_db()

# 创建表
ds.create_tables()

# 解析数据
ds.parse_json_to_csv()

# 导入数据
ds.import_items_from_csv()

# 获取价格
ds.fetch_prices()

# 断开连接
ds.disconnect_db()
```

## API说明

### SteamDT API限制

| 接口 | 限制 | 说明 |
|---|---|---|
| `/open/cs2/v1/base` | 每日1次 | 获取饰品基础信息 |
| `/open/cs2/v1/price/batch` | 每分钟1次 | 批量查询价格 |

### 优化特性

- **多线程并行**: 使用 25 个 API key 并行获取数据，每分钟最多 25 次调用
- **进度条**: 显示数据获取进度
- **数据库更新**: 使用 ON DUPLICATE KEY UPDATE 避免重复插入

### 数据流程

1. 获取所有饰品的基础信息（包含market_hash_name）
2. 批量查询所有饰品的价格数据
3. 将数据存储到MySQL数据库

### 数据库表结构

#### items
- 存储饰品基础信息
- 字段：id, name, marketHashName, BUFF, C5, HALOSKINS, YOUPIN

#### prices
- 存储价格历史数据
- 字段：id, marketHashName, platform, platformItemId, sellPrice, sellCount, biddingPrice, biddingCount, updateTime

## 注意事项

1. **API限制**: 严格遵守SteamDT的调用限制，避免被封禁
2. **多线程安全**: 每个线程使用独立的数据库连接
3. **数据新鲜度**: 价格数据实时获取，可根据需要调整频率
4. API密钥存储在 `api-keys.txt` 中，请妥善保管