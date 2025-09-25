const express = require('express');
const { pool } = require('../database/connection');

const router = express.Router();

// 获取饰品价格分布数据
router.get('/price-distribution', async (req, res) => {
  try {
    const query = `
      SELECT 
        price_range,
        COUNT(*) as count
      FROM (
        SELECT 
          CASE 
            WHEN sell_reference_price < 10 THEN '0-10'
            WHEN sell_reference_price < 50 THEN '10-50'
            WHEN sell_reference_price < 100 THEN '50-100'
            WHEN sell_reference_price < 500 THEN '100-500'
            WHEN sell_reference_price < 1000 THEN '500-1000'
            ELSE '1000+'
          END as price_range,
          CASE 
            WHEN sell_reference_price < 10 THEN 1
            WHEN sell_reference_price < 50 THEN 2
            WHEN sell_reference_price < 100 THEN 3
            WHEN sell_reference_price < 500 THEN 4
            WHEN sell_reference_price < 1000 THEN 5
            ELSE 6
          END as sort_order
        FROM items 
        WHERE sell_reference_price > 0
      ) as price_ranges
      GROUP BY price_range, sort_order
      ORDER BY sort_order
    `;
    
    const [rows] = await pool.execute(query);
    
    // 转换数据格式为饼状图需要的格式
    const data = rows.map(row => ({
      name: `¥${row.price_range}`,
      value: row.count
    }));
    
    res.json({
      success: true,
      data: data
    });
  } catch (error) {
    console.error('获取价格分布数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取数据失败',
      error: error.message
    });
  }
});

// 获取总体统计数据
router.get('/', async (req, res) => {
  try {
    const query = `
      SELECT 
        COUNT(*) as total_items,
        AVG(sell_reference_price) as avg_price,
        MIN(sell_reference_price) as min_price,
        MAX(sell_reference_price) as max_price,
        SUM(sell_num) as total_sell_orders,
        SUM(buy_num) as total_buy_orders
      FROM items 
      WHERE sell_reference_price > 0
    `;
    
    const [rows] = await pool.execute(query);
    const stats = rows[0];
    
    res.json({
      success: true,
      data: {
        totalItems: stats.total_items,
        avgPrice: Math.round(stats.avg_price * 100) / 100,
        minPrice: stats.min_price,
        maxPrice: stats.max_price,
        totalSellOrders: stats.total_sell_orders,
        totalBuyOrders: stats.total_buy_orders
      }
    });
  } catch (error) {
    console.error('获取统计数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取统计数据失败',
      error: error.message
    });
  }
});

// 获取致力指数数据
router.get('/zhili-index', async (req, res) => {
  try {
    // 确保市值历史表存在
    await pool.execute(`
      CREATE TABLE IF NOT EXISTS market_cap_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        total_market_cap DECIMAL(20,2) NOT NULL,
        total_items INT NOT NULL,
        avg_price DECIMAL(16,2),
        zhili_index DECIMAL(16,2) NOT NULL DEFAULT 10000,
        recorded_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_date (recorded_date)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    `);

    // 获取今天日期
    const today = new Date().toISOString().split('T')[0];

    // 计算今天的市值总和（基于最新的items数据）
    const [todayRows] = await pool.execute(`
      SELECT
        SUM(sell_reference_price * sell_num) as total_market_cap,
        COUNT(*) as total_items,
        AVG(sell_reference_price) as avg_price
      FROM items
      WHERE sell_reference_price > 0 AND sell_num > 0
    `);

    const todayData = todayRows[0];
    const currentMarketCap = todayData.total_market_cap || 0;

    // 获取历史数据来计算基准值
    const [baseHistoryRows] = await pool.execute(`
      SELECT
        recorded_date as date,
        total_market_cap as marketCap
      FROM market_cap_history
      ORDER BY recorded_date ASC
    `);

    // 计算基准市值（第一天或10000对应的市值）
    let baseCap = 10000; // 默认基准
    if (baseHistoryRows.length > 0) {
      baseCap = baseHistoryRows[0].marketCap;
    }

    // 计算今天的指数
    const currentIndex = baseCap > 0 ? (currentMarketCap / baseCap) * 10000 : 10000;

    // 存储今天的市值数据
    await pool.execute(`
      INSERT INTO market_cap_history (total_market_cap, total_items, avg_price, zhili_index, recorded_date)
      VALUES (?, ?, ?, ?, ?)
      ON DUPLICATE KEY UPDATE
        total_market_cap = VALUES(total_market_cap),
        total_items = VALUES(total_items),
        avg_price = VALUES(avg_price),
        zhili_index = VALUES(zhili_index)
    `, [currentMarketCap, todayData.total_items, todayData.avg_price, currentIndex, today]);

    // 获取历史数据
    const [historyRows] = await pool.execute(`
      SELECT
        DATE_FORMAT(recorded_date, '%Y-%m-%d') as date,
        total_market_cap as marketCap,
        total_items as itemCount,
        avg_price as avgPrice,
        zhili_index as zhiliIndex
      FROM market_cap_history
      ORDER BY recorded_date ASC
    `);

    // 使用存储的指数值
    const historyData = historyRows.map((row) => ({
      date: row.date,
      zhiliIndex: Math.round(parseFloat(row.zhiliIndex || 10000) * 100) / 100,
      marketCap: Math.round(parseFloat(row.marketCap || 0) * 100) / 100,
      itemCount: row.itemCount,
      avgPrice: Math.round(parseFloat(row.avgPrice || 0) * 100) / 100
    }));

    // 当前数据
    const currentData = historyData[historyData.length - 1] || {
      zhiliIndex: 10000,
      marketCap: Math.round(parseFloat(currentMarketCap) * 100) / 100,
      itemCount: todayData.total_items,
      avgPrice: Math.round(parseFloat(todayData.avg_price) * 100) / 100
    };

    res.json({
      success: true,
      data: {
        currentIndex: currentData.zhiliIndex,
        currentMarketCap: currentData.marketCap,
        currentItemCount: currentData.itemCount,
        currentAvgPrice: currentData.avgPrice,
        baseValue: 10000,
        history: historyData
      }
    });
  } catch (error) {
    console.error('获取致力指数数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取指数数据失败',
      error: error.message
    });
  }
});

module.exports = router;