const mysql = require('mysql2/promise');
const { dbConfig } = require('../config/database');

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
    return true;
  } catch (error) {
    console.error('数据库连接失败:', error.message);
    return false;
  }
}

module.exports = {
  pool,
  testConnection
};

// 确保价格历史表存在（如果不存在则创建）
async function ensurePriceHistoryTable(tableName = 'items_price_history') {
  try {
    const createSql =
      'CREATE TABLE IF NOT EXISTS `' + tableName + '` (' +
      '`id` BIGINT AUTO_INCREMENT PRIMARY KEY,' +
      '`item_id` BIGINT NOT NULL,' +
      '`sell_reference_price` DECIMAL(16,6),' +
      '`sell_min_price` DECIMAL(16,6),' +
      '`buy_max_price` DECIMAL(16,6),' +
      '`sell_num` INT,' +
      '`buy_num` INT,' +
      '`transacted_num` INT,' +
      '`recorded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,' +
      'INDEX `idx_item_time` (`item_id`, `recorded_at`),' +
      'INDEX `idx_recorded_at` (`recorded_at`)' +
      ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;';
    await pool.execute(createSql);
    console.log(`ensured table ${tableName} exists`);
    return true;
  } catch (err) {
    console.error('ensurePriceHistoryTable error:', err.message || err);
    return false;
  }
}

module.exports.ensurePriceHistoryTable = ensurePriceHistoryTable;