const express = require('express');
const { pool } = require('../database/connection');

const router = express.Router();

// 搜索饰品接口
router.get('/', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (!q || q.trim().length < 2) {
      return res.json({
        success: true,
        data: []
      });
    }
    
    const searchTerm = `%${q.trim()}%`;
    const query = `
      SELECT 
        id,
        name,
        market_hash_name,
        sell_min_price,
        sell_reference_price,
        steam_market_url
      FROM items 
      WHERE name LIKE ? OR market_hash_name LIKE ?
      ORDER BY sell_reference_price DESC
      LIMIT 20
    `;
    
    const [rows] = await pool.execute(query, [searchTerm, searchTerm]);
    
    res.json({
      success: true,
      data: rows
    });
  } catch (error) {
    console.error('搜索饰品失败:', error);
    res.status(500).json({
      success: false,
      message: '搜索失败',
      error: error.message
    });
  }
});

module.exports = router;