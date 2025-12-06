# 数据库数据插入说明

## 概述

本项目使用 `db/kline_data_processor.py` 模块处理和插入日K数据。该模块从爬虫抓取的 JSON 数据中解析历史和实时数据，并存储到 Remote 数据库的 `kline_data_day` 表中，避免重复插入。

## 数据解析流程

1. **接收原始 JSON**：从 `Crawler/daily_crawler.py` 获取的 SteamDT API 数据。
2. **分离数据**：
   - 历史数据：除最后一个外的所有条目（每日收盘数据）。
   - 实时数据：最后一个条目（当前时间戳的实时市场数据）。
3. **转换格式**：将数组转换为字典，便于数据库操作。

## 数据库插入逻辑

1. **连接数据库**：使用 `.env` 中的 Remote 配置连接 MySQL。
2. **检查重复**：查询 `kline_data_day` 表中已存在的 `timestamp`，避免插入重复历史数据。
3. **插入历史数据**：只插入新 `timestamp` 的数据，使用批量插入提高效率。
4. **插入实时数据**：先删除旧实时数据（相同 `timestamp`），然后插入新实时数据。
5. **提交事务**：确保数据一致性。

## 表结构

`kline_data_day` 表字段：
- `timestamp` (BIGINT PRIMARY KEY): 时间戳（秒）。
- `open` (DECIMAL): 开盘价。
- `high` (DECIMAL): 最高价。
- `low` (DECIMAL): 最低价。
- `close` (DECIMAL): 收盘价。
- `volume` (INT): 成交量。
- `turnover` (DECIMAL): 成交额。

## 代码使用

```python
from db.kline_data_processor import KlineDataProcessor
from Crawler.daily_crawler import DailyKlineCrawler

# 抓取数据
crawler = DailyKlineCrawler()
raw_data = crawler.fetch_daily_data()

# 处理并存储
if raw_data:
    processor = KlineDataProcessor()
    processor.process_and_store(raw_data)
```

## 注意事项

- **依赖**：需要 `pymysql`, `python-dotenv`。
- **环境变量**：确保 `.env` 配置 Remote DB 连接参数。
- **错误处理**：模块包含异常捕获，失败时打印错误信息。
- **性能**：历史数据只插入新条目，实时数据覆盖更新。
- **扩展**：可添加索引或分区以优化查询性能。

## 实践经验

- 数据重合：每次抓取的数据有历史重叠，通过 `timestamp` 去重。
- 实时更新：最后一个数据为实时，可用于实时监控。
- 日志：插入后打印条数，便于调试。