# Kline Crawler 增强版使用指南

## 概述

`kline_crawler_enhanced.py` 是原 `kline_crawler.py` 的增强版本，新增以下功能：

1. **时线数据支持**：支持爬取时线（hour）数据
2. **智能过滤**：时线数据自动过滤，只保留每小时 xx:55:10 的数据点
3. **技术指标计算**：自动计算多个股市技术指标
4. **批量爬取**：支持一次性爬取所有历史数据

## 技术指标

爬虫会自动计算以下技术指标并存入数据库：

### 移动平均线 (MA)
- **MA5**: 5周期简单移动平均
- **MA10**: 10周期简单移动平均
- **MA20**: 20周期简单移动平均
- **MA30**: 30周期简单移动平均

### 指数移动平均 (EMA)
- **EMA12**: 12周期指数移动平均
- **EMA26**: 26周期指数移动平均

### MACD 指标
- **MACD**: MACD 线 (EMA12 - EMA26)
- **MACD Signal**: 信号线 (MACD 的9周期 EMA)
- **MACD Histogram**: MACD 柱状图 (MACD - Signal)

### RSI 相对强弱指标
- **RSI6**: 6周期 RSI
- **RSI12**: 12周期 RSI
- **RSI24**: 24周期 RSI

### KDJ 随机指标
- **K值**: K线（快线）
- **D值**: D线（慢线）
- **J值**: J线（超快线）

### 布林带 (Bollinger Bands)
- **Upper Band**: 上轨
- **Middle Band**: 中轨
- **Lower Band**: 下轨

## 数据库表结构

```sql
CREATE TABLE IF NOT EXISTS kline_data_hour (
    timestamp BIGINT PRIMARY KEY,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    turnover DECIMAL(15,2),
    -- 移动平均线
    ma5 DECIMAL(10,2),
    ma10 DECIMAL(10,2),
    ma20 DECIMAL(10,2),
    ma30 DECIMAL(10,2),
    -- 指数移动平均
    ema12 DECIMAL(10,2),
    ema26 DECIMAL(10,2),
    -- MACD
    macd DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    macd_hist DECIMAL(10,4),
    -- RSI
    rsi6 DECIMAL(10,4),
    rsi12 DECIMAL(10,4),
    rsi24 DECIMAL(10,4),
    -- KDJ
    k_value DECIMAL(10,4),
    d_value DECIMAL(10,4),
    j_value DECIMAL(10,4),
    -- 布林带
    bollinger_upper DECIMAL(10,2),
    bollinger_middle DECIMAL(10,2),
    bollinger_lower DECIMAL(10,2),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
);
```

## 使用方法

### 1. 爬取最新时线数据

```bash
cd src
python kline_crawler_enhanced.py --mode recent --type hour --config ../config.json
```

### 2. 爬取指定时间点的历史数据

```bash
python kline_crawler_enhanced.py --mode historical --type hour --maxTime 1719414000 --config ../config.json
```

### 3. 批量爬取所有历史数据（推荐首次使用）

```bash
python kline_crawler_enhanced.py --mode batch --type hour --config ../config.json
```

这个命令会：
1. 爬取最新的数据（近3个月）
2. 爬取所有历史数据点（从2024年4月至今）
3. 自动去重
4. 计算技术指标
5. 批量插入数据库

### 4. 爬取日线数据

```bash
# 最新日线
python kline_crawler_enhanced.py --mode recent --type day --config ../config.json

# 批量日线
python kline_crawler_enhanced.py --mode batch --type day --config ../config.json
```

## 时线数据过滤说明

**重要**：时线数据的过滤规则根据数据时期不同：

### 最新数据（Recent Mode）
对于最新的时线数据（近3个月），爬虫会自动过滤，只保留 `xx:55:10` 格式的时间戳。

例如：
- ✅ `2025-10-04 15:55:10` - 保留
- ❌ `2025-10-04 15:00:00` - 过滤
- ❌ `2025-10-04 15:30:00` - 过滤

### 历史数据（Historical/Batch Mode）
对于历史数据（2024年及更早），**不进行时间过滤**，因为历史数据不是严格按 xx:55:10 记录的，而是大约每小时记录一次。

这样可以确保：
- 最新数据：每小时只保留标准的 55:10 数据点
- 历史数据：保留所有可用的时线数据

## 历史数据时间点

批量模式会爬取以下历史时间点（Unix 秒时间戳）：

```python
[
    1756911600,  # 2025-05-04
    1754233200,  # 2025-04-03
    1751554800,  # 2025-03-03
    1748876400,  # 2025-01-31
    1746198000,  # 2024-12-31
    1743519600,  # 2024-11-30
    1740841200,  # 2024-10-30
    1738162800,  # 2024-09-29
    1735484400,  # 2024-08-29
    1732806000,  # 2024-07-28
    1730127600,  # 2024-06-27
    1727449200,  # 2024-05-27
    1724770800,  # 2024-04-26
    1722092400,  # 2024-03-27
    1719414000,  # 2024-02-25
    1716735600,  # 2024-01-25
    1714057200,  # 2023-12-26
]
```

## 依赖安装

确保已安装以下依赖：

```bash
pip install pandas numpy pymysql requests
```

## 查询示例

### 查询最新的时线数据

```sql
SELECT 
    FROM_UNIXTIME(timestamp) as time,
    close_price,
    ma5, ma10, ma20,
    rsi12,
    macd, macd_signal,
    k_value, d_value
FROM kline_data_hour
ORDER BY timestamp DESC
LIMIT 24;  -- 最近24小时
```

### 查找 RSI 超买超卖信号

```sql
-- RSI > 70 超买
SELECT 
    FROM_UNIXTIME(timestamp) as time,
    close_price,
    rsi12
FROM kline_data_hour
WHERE rsi12 > 70
ORDER BY timestamp DESC;

-- RSI < 30 超卖
SELECT 
    FROM_UNIXTIME(timestamp) as time,
    close_price,
    rsi12
FROM kline_data_hour
WHERE rsi12 < 30
ORDER BY timestamp DESC;
```

### 查找 MACD 金叉/死叉

```sql
-- MACD 金叉（MACD 上穿信号线）
SELECT 
    t1.timestamp,
    FROM_UNIXTIME(t1.timestamp) as time,
    t1.close_price,
    t1.macd,
    t1.macd_signal
FROM kline_data_hour t1
JOIN kline_data_hour t2 ON t2.timestamp = (
    SELECT MAX(timestamp) 
    FROM kline_data_hour 
    WHERE timestamp < t1.timestamp
)
WHERE t1.macd > t1.macd_signal 
  AND t2.macd <= t2.macd_signal
ORDER BY t1.timestamp DESC
LIMIT 10;
```

### 查找价格突破布林带

```sql
-- 价格突破上轨
SELECT 
    FROM_UNIXTIME(timestamp) as time,
    close_price,
    bollinger_upper,
    bollinger_middle,
    bollinger_lower
FROM kline_data_hour
WHERE close_price > bollinger_upper
ORDER BY timestamp DESC
LIMIT 20;
```

## 定时任务

可以使用 Windows 任务计划程序每小时自动爬取：

```powershell
# 创建定时任务（每小时55分执行）
$action = New-ScheduledTaskAction -Execute "python" -Argument "E:\github\Buffotte\src\kline_crawler_enhanced.py --mode recent --type hour --config E:\github\Buffotte\config.json" -WorkingDirectory "E:\github\Buffotte\src"

$trigger = New-ScheduledTaskTrigger -Once -At "00:55" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "BuffKlineHourly" -Action $action -Trigger $trigger -Description "Fetch hourly kline data with indicators"
```

## 性能优化建议

1. **首次爬取**：使用 batch 模式一次性获取所有历史数据
2. **定期更新**：使用 recent 模式每小时更新最新数据
3. **数据库索引**：已自动创建 timestamp 索引
4. **批量插入**：使用 `INSERT IGNORE` 避免重复数据

## 故障排查

### 问题：pandas/numpy 未安装

```bash
pip install pandas numpy
```

### 问题：数据库连接失败

检查 `config.json` 中的数据库配置：

```json
{
  "host": "localhost",
  "user": "your_user",
  "password": "your_password",
  "database": "your_db",
  "port": 3306,
  "charset": "utf8mb4"
}
```

### 问题：没有数据返回

- 检查网络连接
- 确认 API 可访问
- 查看错误日志

## 与原版的兼容性

新版本完全独立于原 `kline_crawler.py`，不会影响现有代码。可以同时保留两个版本：

- `kline_crawler.py` - 原版（简单、稳定）
- `kline_crawler_enhanced.py` - 增强版（功能丰富）

## 未来改进

- [ ] 支持更多技术指标（OBV、ATR 等）
- [ ] 添加指标异常检测
- [ ] 支持多币种/多市场
- [ ] 实时推送价格预警
