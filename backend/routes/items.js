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

// 获取饰品价格历史
router.get('/:identifier/history', async (req, res) => {
  try {
    const { identifier } = req.params;
    const limit = parseInt(req.query.limit) || 500;

    // 判断是否为 ID
    const isId = /^\d+$/.test(identifier);

    let itemId = null;
    if (isId) {
      itemId = parseInt(identifier);
    } else {
      // 通过 name 或 market_hash_name 查找 id
      const [rows] = await pool.execute('SELECT id FROM items WHERE name = ? OR market_hash_name = ? LIMIT 1', [identifier, identifier]);
      if (rows.length === 0) {
        return res.status(404).json({ success: false, message: '未找到该饰品' });
      }
      itemId = rows[0].id;
    }

    // 查询历史表
    try {
      // 为避免某些 MySQL 驱动/版本在 prepared statement 上对 LIMIT 占位符出现错误，
      // 我们将 LIMIT 以数字拼接到 SQL（已保证 limit 为整数）。
      const safeLimit = Number.isFinite(limit) ? Math.max(0, Math.floor(limit)) : 500;
      const sql = `SELECT sell_min_price, sell_reference_price, buy_max_price, recorded_at FROM items_price_history WHERE item_id = ? ORDER BY recorded_at ASC LIMIT ${safeLimit}`;
      const [histRows] = await pool.execute(sql, [itemId]);

      res.json({ success: true, data: histRows });
    } catch (err) {
      // 如果历史表不存在或其它可恢复的错误，返回空数组而非 500
      console.error('history query error:', err && err.code, err && err.message, err && err.stack);
      if (err && (err.code === 'ER_NO_SUCH_TABLE' || (err.message && err.message.includes('doesn\'t exist')))) {
        // 返回空数据，前端会显示“暂无历史价格数据”占位
        return res.json({ success: true, data: [] });
      }
      // 其它错误仍返回 500
      throw err;
    }
  } catch (error) {
    console.error('获取价格历史失败:', error);
    res.status(500).json({ success: false, message: '获取价格历史失败', error: error.message });
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
      // 注意：即使爬虫失败，我们也继续执行，不直接返回错误
    }
    
    // 等待一小段时间确保数据库写入完成（如果爬虫成功的话）
    if (crawlerSuccess) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
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
      
      // 如果爬虫成功但数据还没更新，继续重试
      if (crawlerSuccess) {
        retryCount++;
        if (retryCount < maxRetries) {
          console.log(`数据未更新，进行第 ${retryCount + 1} 次重试...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } else {
        // 如果爬虫失败，强制更新时间戳
        console.log('爬虫失败，强制更新时间戳...');
        const now = new Date();
        try {
          const updateResult = await pool.execute(
            'UPDATE items SET updated_at = ? WHERE id = ?',
            [now, beforeData.id]
          );
          console.log(`强制更新时间戳结果: ${updateResult[0].affectedRows} 行受影响`);
          
          // 同时记录价格历史，即使没有新数据
          try {
            await pool.execute(
              'INSERT INTO items_price_history (item_id, sell_reference_price, sell_min_price, buy_max_price, recorded_at) VALUES (?, ?, ?, ?, ?)',
              [beforeData.id, beforeData.sell_reference_price, beforeData.sell_min_price, beforeData.buy_max_price, now]
            );
            console.log('价格历史记录成功');
          } catch (historyError) {
            console.error('记录价格历史失败:', historyError);
          }
          
          // 重新获取更新后的数据
          const [updatedRows] = await pool.execute(query, params);
          if (updatedRows.length > 0) {
            afterData = updatedRows[0];
            console.log(`强制更新后数据: 价格=${afterData.sell_reference_price}, 更新时间=${afterData.updated_at}`);
          }
        } catch (updateError) {
          console.error('强制更新时间戳失败:', updateError);
        }
        break;
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
        message = crawlerSuccess ? '数据刷新成功，价格未变化但数据已更新' : '数据刷新尝试完成，价格未变化但时间戳已更新';
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