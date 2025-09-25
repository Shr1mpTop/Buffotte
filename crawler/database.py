"""
数据库操作模块
处理饰品数据的数据库写入和查询
"""
import asyncio
import json
from typing import Dict, Any, Optional

try:
    import pymysql
except Exception:
    pymysql = None


async def writer_loop(queue: asyncio.Queue, db_conf: Dict[str, Any], table: str, enable_price_history: bool = True):
    """数据库写入循环"""
    if pymysql is None:
        print('未安装 pymysql，写入数据库不可用')
        return
    
    try:
        conn = pymysql.connect(
            host=db_conf['host'], 
            port=db_conf['port'], 
            user=db_conf['user'], 
            password=db_conf['password'], 
            charset='utf8mb4', 
            autocommit=False
        )
    except Exception as e:
        print('无法连接到 MySQL，writer 线程退出:', e)
        return
    
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;" % db_conf['database'])
    conn.select_db(db_conf['database'])
    
    # 创建主表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS `%s` (
      `id` BIGINT PRIMARY KEY,
      `appid` INT,
      `game` VARCHAR(50),
      `name` TEXT,
      `market_hash_name` TEXT,
      `steam_market_url` TEXT,
      `sell_reference_price` DECIMAL(16,6),
      `sell_min_price` DECIMAL(16,6),
      `buy_max_price` DECIMAL(16,6),
      `sell_num` INT,
      `buy_num` INT,
      `transacted_num` INT,
      `goods_info` JSON,
      `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """ % table)
    
    # 创建价格历史表
    if enable_price_history:
        price_history_table = f"{table}_price_history"
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{price_history_table}` (
          `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
          `item_id` BIGINT NOT NULL,
          `sell_reference_price` DECIMAL(16,6),
          `sell_min_price` DECIMAL(16,6),
          `buy_max_price` DECIMAL(16,6),
          `sell_num` INT,
          `buy_num` INT,
          `transacted_num` INT,
          `recorded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_item_time` (`item_id`, `recorded_at`),
          INDEX `idx_recorded_at` (`recorded_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print(f'价格历史表 {price_history_table} 已准备就绪')

    insert_sql = (
        "INSERT INTO `{table}` (`id`,`appid`,`game`,`name`,`market_hash_name`,`steam_market_url`,`sell_reference_price`,`sell_min_price`,`buy_max_price`,`sell_num`,`buy_num`,`transacted_num`,`goods_info`,`updated_at`) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) "
        "ON DUPLICATE KEY UPDATE "
        "`appid`=VALUES(`appid`), "
        "`game`=VALUES(`game`), "
        "`name`=VALUES(`name`), "
        "`market_hash_name`=VALUES(`market_hash_name`), "
        "`steam_market_url`=VALUES(`steam_market_url`), "
        "`sell_reference_price`=VALUES(`sell_reference_price`), "
        "`sell_min_price`=VALUES(`sell_min_price`), "
        "`buy_max_price`=VALUES(`buy_max_price`), "
        "`sell_num`=VALUES(`sell_num`), "
        "`buy_num`=VALUES(`buy_num`), "
        "`transacted_num`=VALUES(`transacted_num`), "
        "`goods_info`=VALUES(`goods_info`), "
        "`updated_at`=NOW()"
    ).format(table=table)
    
    # 价格历史表插入SQL
    price_history_sql = None
    if enable_price_history:
        price_history_sql = f"""
        INSERT INTO `{price_history_table}` 
        (`item_id`, `sell_reference_price`, `sell_min_price`, `buy_max_price`, `sell_num`, `buy_num`, `transacted_num`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

    batch = []
    price_history_batch = []
    
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            
            # 检查是否为flush信号
            if isinstance(item, dict) and item.get('type') == 'flush':
                if batch:
                    try:
                        # 写入主表
                        cur.executemany(insert_sql, batch)
                        
                        # 写入价格历史表
                        if enable_price_history and price_history_batch:
                            cur.executemany(price_history_sql, price_history_batch)
                        
                        conn.commit()
                        print(f'writer: flush - writing {len(batch)} record' + (f', {len(price_history_batch)} price history' if enable_price_history else ''))
                    except Exception as e:
                        print('writer flush 写入错误', e)
                        conn.rollback()
                    batch = []
                    price_history_batch = []
                continue
            
            goods_json = json.dumps(item.get('goods_info') or {}, ensure_ascii=False)
            item_id = int(item.get('id'))
            
            # 主表数据 - 注意：updated_at由NOW()自动设置，不需要在tuple中包含
            main_tuple = (
                item_id, 
                int(item.get('appid') or 0), 
                item.get('game'), 
                item.get('name'), 
                item.get('market_hash_name'), 
                item.get('steam_market_url'), 
                float(item.get('sell_reference_price') or 0), 
                float(item.get('sell_min_price') or 0), 
                float(item.get('buy_max_price') or 0), 
                int(item.get('sell_num') or 0), 
                int(item.get('buy_num') or 0), 
                int(item.get('transacted_num') or 0), 
                goods_json
            )
            batch.append(main_tuple)
            
            # 价格历史数据
            if enable_price_history:
                price_tuple = (
                    item_id, 
                    float(item.get('sell_reference_price') or 0), 
                    float(item.get('sell_min_price') or 0), 
                    float(item.get('buy_max_price') or 0), 
                    int(item.get('sell_num') or 0), 
                    int(item.get('buy_num') or 0), 
                    int(item.get('transacted_num') or 0)
                )
                price_history_batch.append(price_tuple)
            
            if len(batch) >= 200:
                try:
                    # 写入主表
                    cur.executemany(insert_sql, batch)
                    
                    # 写入价格历史表
                    if enable_price_history and price_history_batch:
                        cur.executemany(price_history_sql, price_history_batch)
                    
                    conn.commit()
                    print(f'writer: writing {len(batch)} record' + (f', {len(price_history_batch)} price history' if enable_price_history else ''))
                except Exception as e:
                    print('writer 写入错误', e)
                    conn.rollback()
                batch = []
                price_history_batch = []
                
        # 处理剩余数据
        if batch:
            try:
                cur.executemany(insert_sql, batch)
                if enable_price_history and price_history_batch:
                    cur.executemany(price_history_sql, price_history_batch)
                conn.commit()
                print(f'writer: writing remaining {len(batch)} record' + (f', {len(price_history_batch)} price history' if enable_price_history else ''))
            except Exception as e:
                print('writer write remaining error', e)
                conn.rollback()
    finally:
        cur.close()
        conn.close()


def get_db_config_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """从配置字典中提取数据库配置"""
    return {
        'host': config.get('host', 'localhost'),
        'port': config.get('port', 3306),
        'user': config.get('user', 'root'),
        'password': config.get('password', '123456'),
        'database': config.get('database', 'buffotte'),
        'table': config.get('table', 'items'),
    }