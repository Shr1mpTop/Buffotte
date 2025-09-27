require('dotenv').config({ path: '../../.env' });
const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3000;

// 数据库配置
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '123456',
  database: process.env.DB_NAME || 'buffotte'
};

// 中间件
app.use(cors());
app.use(express.json());

// 数据库连接池
let pool;

async function initDB() {
  try {
    pool = mysql.createPool(dbConfig);
    console.log('Database connected');
  } catch (error) {
    console.error('Database connection failed:', error);
  }
}

// API路由
app.get('/api/stats', async (req, res) => {
  try {
    const [rows] = await pool.execute(
      "SELECT COUNT(*) as total_items FROM items WHERE BUFF IS NOT NULL AND BUFF != ''"
    );
    const totalItems = rows[0].total_items;

    // 从小时K线获取平均价格
    const [priceRows] = await pool.execute(
      "SELECT AVG(close_price) as avg_price FROM kline_data_hour"
    );
    const avgPrice = priceRows[0].avg_price || 0;

    res.json({
      total_items: totalItems,
      average_price: Math.round(avgPrice * 100) / 100
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/kline/:type', async (req, res) => {
  try {
    const { type } = req.params;
    const validTypes = ['hour', 'day', 'week'];
    if (!validTypes.includes(type)) {
      return res.status(400).json({ error: 'Invalid kline type' });
    }

    const tableName = `kline_data_${type}`;
    let query = `SELECT * FROM ${tableName}`;

    // 根据K线类型设置过滤条件，只返回正式数据
    if (type === 'hour') {
      // 小时K：只保留每小时55:10北京时间的数据
      query += ` WHERE (timestamp % 3600) = 3310`; // 55:10 = 55*60 + 10 = 3310秒
    } else if (type === 'day') {
      // 日K：只保留每天15:55:10的数据（这是数据库中的正式数据）
      query += ` WHERE (timestamp % 86400) = 57310`; // 15:55:10 = 15*3600 + 55*60 + 10 = 57310秒
    } else if (type === 'week') {
      // 周K：只保留每周3天15:55:10的数据（这是数据库中最多的正式数据）
      query += ` WHERE (timestamp % 604800) = 316510`; // 3天15:55:10 = 3*86400 + 15*3600 + 55*60 + 10 = 316510秒
    }

    query += ` ORDER BY timestamp DESC LIMIT 100`;

    const [rows] = await pool.execute(query);

    res.json(rows);
  } catch (error) {
    console.error('Error fetching kline data:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/items', async (req, res) => {
  try {
    const [rows] = await pool.execute(
      "SELECT * FROM items WHERE BUFF IS NOT NULL AND BUFF != '' LIMIT 100"
    );
    res.json(rows);
  } catch (error) {
    console.error('Error fetching items:', error);
    res.status(500).json({ error: error.message });
  }
});

// 清理过期临时数据的函数
async function cleanupExpiredTempData() {
  try {
    const now = Math.floor(Date.now() / 1000); // 当前时间戳（秒）

    // 清理小时K线中过期的临时数据（保留55:10数据，删除其他数据超过1小时的记录）
    const hourThreshold = now - 3600; // 1小时前
    await pool.execute(
      `DELETE FROM kline_data_hour WHERE (timestamp % 3600) != 3310 AND timestamp < ?`,
      [hourThreshold]
    );

    // 清理日K线中过期的临时数据（保留15:55:10数据，删除其他数据超过24小时的记录）
    const dayThreshold = now - 86400; // 24小时前
    await pool.execute(
      `DELETE FROM kline_data_day WHERE (timestamp % 86400) != 57310 AND timestamp < ?`,
      [dayThreshold]
    );

    // 清理周K线中过期的临时数据（保留3天15:55:10数据，删除其他数据超过7天的记录）
    const weekThreshold = now - 604800; // 7天前
    await pool.execute(
      `DELETE FROM kline_data_week WHERE (timestamp % 604800) != 316510 AND timestamp < ?`,
      [weekThreshold]
    );

    console.log('临时数据清理完成');
  } catch (error) {
    console.error('清理临时数据失败:', error);
  }
}

// 刷新数据API - 触发爬虫更新数据
app.post('/api/refresh', async (req, res) => {
  try {
    // 先清理过期临时数据
    await cleanupExpiredTempData();

    const { spawn } = require('child_process');

    console.log('开始执行数据刷新...');

    // 调用Python爬虫脚本 - 使用正确的路径
    const pythonProcess = spawn('python', ['../../crawler/src/kline_crawler.py'], {
      cwd: __dirname,
      stdio: 'inherit'
    });

    pythonProcess.on('close', (code) => {
      console.log(`爬虫进程退出，退出码: ${code}`);
      if (code === 0) {
        console.log('数据刷新完成');
      } else {
        console.log('数据刷新失败');
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('启动爬虫失败:', error);
    });

    res.json({
      success: true,
      message: '数据刷新已启动，正在后台执行爬虫...',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error refreshing data:', error);
    res.status(500).json({ error: error.message });
  }
});

// 启动服务器
app.listen(port, async () => {
  await initDB();

  // 设置定期清理任务 - 每小时清理一次过期临时数据
  setInterval(async () => {
    console.log('开始定期清理过期临时数据...');
    await cleanupExpiredTempData();
  }, 60 * 60 * 1000); // 每小时执行一次

  console.log(`Server running at http://localhost:${port}`);
});