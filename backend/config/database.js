// 数据库配置
require('dotenv').config();

const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 3306,
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '123456',
  database: process.env.DB_DATABASE || 'buffotte',
  charset: 'utf8mb4'
};

module.exports = {
  dbConfig,
  port: process.env.PORT || 3001,
  crawlerTimeout: 30000
};