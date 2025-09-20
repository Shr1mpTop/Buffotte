const express = require('express');
const { pool } = require('../database/connection');
const { refreshItemFromCrawler } = require('../services/crawlerService');

const router = express.Router();

// 获取单个饰品详情
router.get('/:identifier', async (req, res) => {
  try {
    const { identifier } = req.params;
    
    // 判断是ID还是名称
    const isId = /^\d+$/.test(identifier);
    
    let query, params;
    if (isId) {
      query = 'SELECT * FROM items WHERE id = ?';
      params = [parseInt(identifier)];
    } else {
      query = 'SELECT * FROM items WHERE name = ? OR market_hash_name = ?';
      params = [identifier, identifier];
    }
    
    const [rows] = await pool.execute(query, params);
    
    if (rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '未找到该饰品'
      });
    }
    
    res.json({
      success: true,
      data: rows[0]
    });
  } catch (error) {
    console.error('获取饰品详情失败:', error);
    res.status(500).json({
      success: false,
      message: '获取饰品详情失败',
      error: error.message
    });
  }
});

// 刷新单个饰品数据
router.post('/refresh', async (req, res) => {
  try {
    const { id, name } = req.body;
    
    if (!id && !name) {
      return res.status(400).json({
        success: false,
        message: '请提供饰品ID或名称'
      });
    }
    
    // 首先尝试通过爬虫更新数据
    try {
      await refreshItemFromCrawler(id, name);
    } catch (crawlerError) {
      console.warn('爬虫更新失败，使用现有数据:', crawlerError.message);
    }
    
    // 获取更新后的数据
    let query, params;
    if (id) {
      query = 'SELECT * FROM items WHERE id = ?';
      params = [parseInt(id)];
    } else {
      query = 'SELECT * FROM items WHERE name = ? OR market_hash_name = ?';
      params = [name, name];
    }
    
    const [rows] = await pool.execute(query, params);
    
    if (rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '未找到该饰品'
      });
    }
    
    res.json({
      success: true,
      data: rows[0],
      message: '数据已刷新'
    });
  } catch (error) {
    console.error('刷新饰品数据失败:', error);
    res.status(500).json({
      success: false,
      message: '刷新失败',
      error: error.message
    });
  }
});

module.exports = router;