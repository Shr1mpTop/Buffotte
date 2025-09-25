const express = require('express');
const cors = require('cors');
const { port } = require('./config/database');
const { testConnection } = require('./database/connection');

// 导入路由模块
const searchRoutes = require('./routes/search');
const itemRoutes = require('./routes/items');
const statsRoutes = require('./routes/stats');

const app = express();

// 中间件
app.use(cors());
app.use(express.json());

// 路由注册
app.use('/api/search', searchRoutes);
app.use('/api/item', itemRoutes);
app.use('/api/stats', statsRoutes);

// 兼容性路由 - 保持向后兼容
app.post('/api/refresh-item', (req, res, next) => {
  // 重定向到新的路由结构
  req.url = '/refresh';
  itemRoutes(req, res, next);
});

// 价格分布兼容性路由
app.get('/api/price-distribution', (req, res, next) => {
  // 重定向到新的路由结构
  req.url = '/price-distribution';
  statsRoutes(req, res, next);
});

// 致力指数兼容性路由
app.get('/api/zhili-index', (req, res, next) => {
  // 重定向到新的路由结构
  req.url = '/zhili-index';
  statsRoutes(req, res, next);
});

// 健康检查接口
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'Buffotte Backend API 运行正常 - v0.6.1 模块化版本',
    timestamp: new Date().toISOString(),
    version: '0.6.1'
  });
});

// 404处理
app.use('/api/*', (req, res) => {
  res.status(404).json({
    success: false,
    message: '接口不存在',
    path: req.path
  });
});

// 启动服务器
app.listen(port, async () => {
  console.log(`Buffotte Backend v0.6.1 服务器运行在 http://localhost:${port}`);
  console.log('架构: 模块化结构');
  const connected = await testConnection();
  if (connected) {
    console.log('系统就绪');
    // 确保历史表存在
    try {
      const { ensurePriceHistoryTable } = require('./database/connection');
      await ensurePriceHistoryTable('items_price_history');
    } catch (e) {
      console.error('ensurePriceHistoryTable failed:', e && e.message);
    }
  } else {
    console.log('警告: 数据库连接失败，部分功能可能不可用');
  }
});

module.exports = app;