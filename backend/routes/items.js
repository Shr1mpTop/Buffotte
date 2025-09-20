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
    
    console.log(`开始刷新饰品数据: ID=${id}, Name=${name}`);
    
    // 获取刷新前的数据作为对比
    let query, params;
    if (id) {
      query = 'SELECT * FROM items WHERE id = ?';
      params = [parseInt(id)];
    } else {
      query = 'SELECT * FROM items WHERE name = ? OR market_hash_name = ?';
      params = [name, name];
    }
    
    const [beforeRows] = await pool.execute(query, params);
    
    if (beforeRows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '未找到该饰品'
      });
    }
    
    const beforeData = beforeRows[0];
    console.log(`刷新前数据: 价格=${beforeData.sell_reference_price}, 更新时间=${beforeData.updated_at}`);
    
    // 尝试通过爬虫更新数据
    let crawlerSuccess = false;
    let crawlerError = null;
    
    try {
      // 对于ID查询，我们使用物品名称而不是ID来搜索，因为ID搜索可能找不到
      const searchTerm = id ? beforeData.name : name;
      console.log(`使用搜索词: ${searchTerm}`);
      await refreshItemFromCrawler(null, searchTerm);
      crawlerSuccess = true;
      console.log(`爬虫更新成功: ${searchTerm}`);
    } catch (error) {
      crawlerError = error.message;
      console.error('爬虫更新失败:', error.message);
      
      // 如果爬虫失败，直接返回错误
      return res.status(500).json({
        success: false,
        message: '数据刷新失败',
        error: crawlerError,
        data: beforeData  // 返回原数据
      });
    }
    
    // 等待一小段时间确保数据库写入完成
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 获取更新后的数据，并重试几次以确保数据已更新
    let afterData = null;
    let retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      const [afterRows] = await pool.execute(query, params);
      
      if (afterRows.length === 0) {
        return res.status(404).json({
          success: false,
          message: '饰品数据异常'
        });
      }
      
      afterData = afterRows[0];
      const beforeTime = new Date(beforeData.updated_at).getTime();
      const afterTime = new Date(afterData.updated_at).getTime();
      
      // 如果数据已更新，跳出重试循环
      if (afterTime > beforeTime) {
        break;
      }
      
      // 等待后重试
      retryCount++;
      if (retryCount < maxRetries) {
        console.log(`数据未更新，进行第 ${retryCount + 1} 次重试...`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    console.log(`刷新后数据: 价格=${afterData.sell_reference_price}, 更新时间=${afterData.updated_at}`);
    
    // 检查数据是否真的更新了（比较时间戳）
    const beforeTime = new Date(beforeData.updated_at).getTime();
    const afterTime = new Date(afterData.updated_at).getTime();
    const dataUpdated = afterTime > beforeTime;
    
    // 检查价格是否有变化
    const priceChanged = parseFloat(beforeData.sell_reference_price) !== parseFloat(afterData.sell_reference_price);
    
    let message;
    if (dataUpdated) {
      if (priceChanged) {
        message = `数据刷新成功，价格从 ¥${beforeData.sell_reference_price} 更新为 ¥${afterData.sell_reference_price}`;
      } else {
        message = '数据刷新成功，价格未变化但数据已更新';
      }
    } else {
      message = '数据刷新异常，时间戳未更新';
    }
    
    res.json({
      success: true,
      data: afterData,
      message: message,
      crawlerSuccess: crawlerSuccess,
      dataUpdated: dataUpdated,
      priceChanged: priceChanged,
      priceChange: priceChanged ? {
        before: parseFloat(beforeData.sell_reference_price),
        after: parseFloat(afterData.sell_reference_price),
        diff: parseFloat(afterData.sell_reference_price) - parseFloat(beforeData.sell_reference_price)
      } : null,
      refreshTime: new Date().toISOString()
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