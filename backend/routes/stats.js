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

module.exports = router;