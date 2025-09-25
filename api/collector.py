"""
SteamDT 数据收集器
定期从SteamDT API获取CS2饰品价格数据并存储到数据库
"""
import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pymysql
from steamdt_client import SteamDTClient


class SteamDTCollector:
    """SteamDT数据收集器"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.client = SteamDTClient(db_config)

    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)

    async def create_api_limits_table(self):
        """创建API限制信息表"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 创建API限制表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steamdt_api_limits (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        endpoint VARCHAR(255) UNIQUE NOT NULL,
                        description VARCHAR(500),
                        limit_per_hour INT,
                        limit_per_minute INT,
                        limit_per_day INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                ''')

                # 创建API调用记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steamdt_api_calls (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        endpoint VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_endpoint (endpoint),
                        INDEX idx_created_at (created_at)
                    )
                ''')

                # 插入API限制信息
                api_limits = [
                    ('/open/cs2/v1/base', '获取steam饰品基础信息', None, None, 1),
                    ('/open/cs2/v1/price/batch', '通过marketHashName批量查询饰品价格', None, 1, None),
                    ('/open/cs2/v1/price/single', '通过marketHashName查询饰品价格', None, 60, None),
                    ('/open/cs2/v1/wear', '通过检视链接查询磨损度相关数据', 36000, None, None),
                    ('/open/cs2/v2/wear', '通过ASMD参数查询磨损度相关数据', 36000, None, None),
                    ('/open/cs2/v1/inspect', '通过检视链接生成检视图', None, None, 100),
                    ('/open/cs2/v2/inspect', '通过ASMD参数生成检视图', None, None, 100),
                ]

                for endpoint, description, per_hour, per_minute, per_day in api_limits:
                    cursor.execute('''
                        INSERT INTO steamdt_api_limits (endpoint, description, limit_per_hour, limit_per_minute, limit_per_day)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        description = VALUES(description),
                        limit_per_hour = VALUES(limit_per_hour),
                        limit_per_minute = VALUES(limit_per_minute),
                        limit_per_day = VALUES(limit_per_day),
                        updated_at = CURRENT_TIMESTAMP
                    ''', (endpoint, description, per_hour, per_minute, per_day))

            conn.commit()
            print('API限制信息已保存到数据库')

        except Exception as e:
            print(f'创建API限制表失败: {e}')
            conn.rollback()
        finally:
            conn.close()

    async def save_base_items(self, base_items: List[Dict[str, Any]]):
        """保存基础饰品信息到数据库"""
        if not base_items:
            return

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 创建基础信息表（如果不存在）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steamdt_base_items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        market_hash_name VARCHAR(255) UNIQUE NOT NULL,
                        platform_list JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                ''')

                # 插入或更新基础信息
                for item in base_items:
                    cursor.execute('''
                        INSERT INTO steamdt_base_items (name, market_hash_name, platform_list)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        platform_list = VALUES(platform_list),
                        updated_at = CURRENT_TIMESTAMP
                    ''', (
                        item.get('name', ''),
                        item.get('marketHashName', ''),
                        json.dumps(item.get('platformList', []), ensure_ascii=False)
                    ))

            conn.commit()
            print(f'成功保存 {len(base_items)} 个基础饰品信息')

        except Exception as e:
            print(f'保存基础信息失败: {e}')
            conn.rollback()
        finally:
            conn.close()

    async def save_price_data(self, price_data: Dict[str, List[Dict[str, Any]]]):
        """保存价格数据到数据库"""
        if not price_data:
            return

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 创建价格历史表（如果不存在）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steamdt_price_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        market_hash_name VARCHAR(255) NOT NULL,
                        platform VARCHAR(100) NOT NULL,
                        platform_item_id VARCHAR(255),
                        sell_price DECIMAL(10,2),
                        sell_count INT,
                        bidding_price DECIMAL(10,2),
                        bidding_count INT,
                        update_time BIGINT,
                        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_market_hash_name (market_hash_name),
                        INDEX idx_platform (platform),
                        INDEX idx_update_time (update_time)
                    )
                ''')

                # 插入价格数据
                total_records = 0
                for market_hash_name, platforms in price_data.items():
                    for platform_data in platforms:
                        cursor.execute('''
                            INSERT INTO steamdt_price_history
                            (market_hash_name, platform, platform_item_id, sell_price, sell_count, bidding_price, bidding_count, update_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            market_hash_name,
                            platform_data.get('platform', ''),
                            platform_data.get('platformItemId', ''),
                            platform_data.get('sellPrice'),
                            platform_data.get('sellCount'),
                            platform_data.get('biddingPrice'),
                            platform_data.get('biddingCount'),
                            platform_data.get('updateTime')
                        ))
                        total_records += 1

            conn.commit()
            print(f'成功保存 {total_records} 条价格记录')

        except Exception as e:
            print(f'保存价格数据失败: {e}')
            conn.rollback()
        finally:
            conn.close()

    async def collect_data(self):
        """执行完整的数据收集流程"""
        print(f'开始数据收集 - {datetime.now()}')

        try:
            # 首先创建必要的表
            await self.create_api_limits_table()

            async with self.client:
                # 1. 获取基础信息
                print('步骤1: 获取基础信息')
                base_items = await self.client.get_base_items()

                if base_items:
                    await self.save_base_items(base_items)

                # 2. 获取价格数据
                print('步骤2: 获取价格数据')
                price_data = await self.client.get_all_prices()

                if price_data:
                    await self.save_price_data(price_data)

                print(f'数据收集完成 - {datetime.now()}')

        except Exception as e:
            print(f'数据收集失败: {e}')

    async def run_continuous(self, interval_hours: int = 1):
        """持续运行数据收集"""
        print(f'开始持续数据收集，间隔 {interval_hours} 小时')

        while True:
            await self.collect_data()

            # 等待下次收集
            print(f'等待 {interval_hours} 小时后进行下次收集...')
            await asyncio.sleep(interval_hours * 3600)


async def main():
    """主函数"""
    # 数据库配置（可以从环境变量或配置文件读取）
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '123456'),
        'database': os.environ.get('DB_DATABASE', 'buffotte'),
        'charset': 'utf8mb4'
    }

    collector = SteamDTCollector(db_config)

    # 检查命令行参数
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # 持续运行模式
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        await collector.run_continuous(interval)
    else:
        # 单次运行
        await collector.collect_data()


if __name__ == '__main__':
    asyncio.run(main())