# 价格历史功能说明

## 📊 功能概述

Buffotte v0.2.0 新增了价格历史记录功能，在保持原有数据结构的基础上，新增独立的价格历史表来记录每次爬取的价格数据。

## 🗄️ 数据库结构

### 主表 `items`
保持原有结构不变，存储最新的商品信息：
```sql
items (
  id BIGINT PRIMARY KEY,
  appid INT,
  game VARCHAR(50),
  name TEXT,
  market_hash_name TEXT,
  steam_market_url TEXT,
  sell_reference_price DECIMAL(16,6),  -- 最新参考价格
  sell_min_price DECIMAL(16,6),        -- 最新最低售价
  buy_max_price DECIMAL(16,6),         -- 最新最高求购价
  sell_num INT,                        -- 当前在售数量
  buy_num INT,                         -- 当前求购数量
  transacted_num INT,                  -- 成交数量
  goods_info JSON,
  updated_at TIMESTAMP
)
```

### 价格历史表 `items_price_history`
记录所有历史价格变化：
```sql
items_price_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  item_id BIGINT NOT NULL,                -- 关联商品ID
  sell_reference_price DECIMAL(16,6),     -- 历史参考价格
  sell_min_price DECIMAL(16,6),           -- 历史最低售价
  buy_max_price DECIMAL(16,6),            -- 历史最高求购价
  sell_num INT,                           -- 历史在售数量
  buy_num INT,                            -- 历史求购数量
  transacted_num INT,                     -- 历史成交数量
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 记录时间
  INDEX idx_item_time (item_id, recorded_at),
  INDEX idx_recorded_at (recorded_at)
)
```

## ⚙️ 配置选项

在 `config.json` 中添加：
```json
{
  "enable_price_history": true
}
```

或使用环境变量：
```bash
set BUFF_ENABLE_PRICE_HISTORY=true
```

## 🔍 联查询示例

### 1. 获取商品最新信息和最近价格历史
```sql
SELECT 
    i.name,
    i.sell_min_price as current_price,
    ph.sell_min_price as history_price,
    ph.recorded_at
FROM items i
LEFT JOIN items_price_history ph ON i.id = ph.item_id
WHERE i.id = 33815
ORDER BY ph.recorded_at DESC
LIMIT 10;
```

### 2. 分析价格趋势 - 获取近7天价格变化
```sql
SELECT 
    i.name,
    i.market_hash_name,
    ph.sell_min_price,
    ph.buy_max_price,
    ph.recorded_at,
    LAG(ph.sell_min_price) OVER (ORDER BY ph.recorded_at) as prev_price,
    (ph.sell_min_price - LAG(ph.sell_min_price) OVER (ORDER BY ph.recorded_at)) as price_change
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE i.id = 33815
  AND ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY ph.recorded_at;
```

### 3. 找出价格波动最大的商品（近24小时）
```sql
SELECT 
    i.name,
    i.market_hash_name,
    MIN(ph.sell_min_price) as min_price_24h,
    MAX(ph.sell_min_price) as max_price_24h,
    (MAX(ph.sell_min_price) - MIN(ph.sell_min_price)) as price_volatility,
    ((MAX(ph.sell_min_price) - MIN(ph.sell_min_price)) / MIN(ph.sell_min_price) * 100) as volatility_percent
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY i.id, i.name, i.market_hash_name
HAVING price_volatility > 0
ORDER BY volatility_percent DESC
LIMIT 20;
```

### 4. 获取商品的日均价格（按日期聚合）
```sql
SELECT 
    i.name,
    DATE(ph.recorded_at) as price_date,
    AVG(ph.sell_min_price) as avg_sell_price,
    AVG(ph.buy_max_price) as avg_buy_price,
    AVG(ph.sell_num) as avg_sell_num,
    COUNT(*) as records_count
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE i.id = 33815
  AND ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY i.id, i.name, DATE(ph.recorded_at)
ORDER BY price_date DESC;
```

### 5. 比较当前价格与历史平均价格
```sql
SELECT 
    i.name,
    i.sell_min_price as current_price,
    AVG(ph.sell_min_price) as avg_7d_price,
    (i.sell_min_price - AVG(ph.sell_min_price)) as price_diff,
    ((i.sell_min_price - AVG(ph.sell_min_price)) / AVG(ph.sell_min_price) * 100) as price_change_percent
FROM items i
LEFT JOIN items_price_history ph ON i.id = ph.item_id
WHERE ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY i.id, i.name, i.sell_min_price
HAVING AVG(ph.sell_min_price) IS NOT NULL
ORDER BY price_change_percent DESC
LIMIT 20;
```

### 6. 查找价格突然下跌的商品（潜在投资机会）
```sql
WITH price_changes AS (
    SELECT 
        ph.item_id,
        ph.sell_min_price,
        ph.recorded_at,
        LAG(ph.sell_min_price, 1) OVER (PARTITION BY ph.item_id ORDER BY ph.recorded_at) as prev_price,
        ROW_NUMBER() OVER (PARTITION BY ph.item_id ORDER BY ph.recorded_at DESC) as rn
    FROM items_price_history ph
    WHERE ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 2 DAY)
)
SELECT 
    i.name,
    i.market_hash_name,
    pc.sell_min_price as current_price,
    pc.prev_price,
    (pc.prev_price - pc.sell_min_price) as price_drop,
    ((pc.prev_price - pc.sell_min_price) / pc.prev_price * 100) as drop_percent
FROM price_changes pc
JOIN items i ON pc.item_id = i.id
WHERE pc.rn = 1
  AND pc.prev_price IS NOT NULL
  AND ((pc.prev_price - pc.sell_min_price) / pc.prev_price * 100) > 10  -- 下跌超过10%
ORDER BY drop_percent DESC
LIMIT 20;
```

## 🎯 使用场景

1. **价格趋势分析**: 观察商品价格的长期走势
2. **市场波动监控**: 识别价格异常波动的商品
3. **投资机会发现**: 找出价格被低估或高估的商品
4. **交易策略回测**: 基于历史数据验证交易策略
5. **市场研究**: 分析整体市场的价格变化模式

## 📈 性能优化建议

1. **定期清理**: 建议定期清理超过一定时间的历史数据
2. **分区表**: 大数据量时可考虑按时间分区
3. **索引优化**: 根据查询模式添加合适的复合索引
4. **数据归档**: 将旧数据归档到单独的表或文件

## 🚀 未来扩展

- 支持更多统计维度（如交易量变化）
- 增加价格预警功能
- 提供API接口查询历史数据
- 增加数据可视化图表功能