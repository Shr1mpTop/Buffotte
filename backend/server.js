const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// 中间件
app.use(cors());
app.use(express.json());

// 数据库配置
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 3306,
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '123456',
  database: process.env.DB_DATABASE || 'buffotte',
  charset: 'utf8mb4'
};

// 创建数据库连接池
const pool = mysql.createPool({
  ...dbConfig,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// 测试数据库连接
async function testConnection() {
  try {
    const connection = await pool.getConnection();
    console.log('数据库连接成功');
    connection.release();
  } catch (error) {
    console.error('数据库连接失败:', error.message);
  }
}

// API 路由

// 搜索饰品接口
app.get('/api/search', async (req, res) => {
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

// 获取单个饰品详情
app.get('/api/item/:identifier', async (req, res) => {
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
app.post('/api/refresh-item', async (req, res) => {
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

// 爬虫刷新函数（简化版本）
async function refreshItemFromCrawler(itemId, itemName) {
  const { spawn } = require('child_process');
  const path = require('path');
  
  return new Promise((resolve, reject) => {
    // 构建爬虫命令
    const crawlerPath = path.join(__dirname, '../crawler/buffcrawl.py');
    const args = ['--single-item'];
    
    if (itemId) {
      args.push('--item-id', itemId.toString());
    } else if (itemName) {
      args.push('--item-name', itemName);
    }
    
    const crawlerProcess = spawn('python', [crawlerPath, ...args], {
      cwd: path.dirname(crawlerPath)
    });
    
    let output = '';
    let errorOutput = '';
    
    crawlerProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    crawlerProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    crawlerProcess.on('close', (code) => {
      if (code === 0) {
        console.log('爬虫更新成功:', output);
        resolve(output);
      } else {
        console.error('爬虫更新失败:', errorOutput);
        reject(new Error(`爬虫进程退出码: ${code}, 错误: ${errorOutput}`));
      }
    });
    
    // 设置超时
    setTimeout(() => {
      crawlerProcess.kill();
      reject(new Error('爬虫更新超时'));
    }, 30000); // 30秒超时
  });
}

// 获取饰品价格分布数据
app.get('/api/price-distribution', async (req, res) => {
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
app.get('/api/stats', async (req, res) => {
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

// 健康检查接口
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'Buffotte Backend API 运行正常',
    timestamp: new Date().toISOString()
  });
});

// 启动服务器
app.listen(PORT, async () => {
  console.log(`服务器运行在 http://localhost:${PORT}`);
  await testConnection();
});

module.exports = app;