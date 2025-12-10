import pymysql
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pytz
from fastapi import HTTPException # 新增导入
import asyncio

# 加载环境变量
load_dotenv()

class ItemKlineProcessor:
    def __init__(self):
        self.config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET', 'utf8mb4')
        }
        self.create_tracked_items_table()

    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.config)
    
    def get_item_id_from_db(self, market_hash_name: str) -> Optional[str]:
        """
        从 cs2_items 表中查询饰品的 c5_id (即 item_id)
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT c5_id FROM cs2_items WHERE market_hash_name = %s LIMIT 1",
                    (market_hash_name,)
                )
                result = cursor.fetchone()
                if result:
                    return str(result[0])
                return None
        except Exception as e:
            print(f"从数据库查询 item_id 失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def parse_item_kline_data(self, raw_data: dict, market_hash_name: str, item_id: str) -> List[Dict]:
        """
        解析API返回的饰品K线数据。

        API数据格式: [timestamp, price, sell_count, buy_price, buy_count, turnover, volume, total_count]
        """
        if not raw_data or not raw_data.get("success"):
            print("❌ API返回数据无效")
            return []

        data_points = raw_data.get("data", [])
        if not data_points:
            print("❌ 无数据点")
            return []

        parsed_data = []
        for point in data_points:
            try:
                # 验证数据点长度
                if len(point) < 8:
                    print(f"⚠️ 数据点格式不完整: {point}")
                    continue

                # 解析数据点
                timestamp = int(point[0])
                price = float(point[1])
                sell_count = int(point[2])
                buy_price = float(point[3])
                buy_count = int(point[4])
                turnover = float(point[5]) if point[5] is not None else 0.0
                volume = int(point[6]) if point[6] is not None else 0
                total_count = str(point[7]) if point[7] is not None else "0"

                parsed_point = {
                    'market_hash_name': market_hash_name,
                    'timestamp': timestamp,
                    'item_id': item_id,
                    'price': price,
                    'sell_count': sell_count,
                    'buy_price': buy_price,
                    'buy_count': buy_count,
                    'turnover': turnover,
                    'volume': volume,
                    'total_count': total_count
                }
                parsed_data.append(parsed_point)

            except (ValueError, TypeError, IndexError) as e:
                print(f"⚠️ 解析数据点失败: {point}, 错误: {e}")
                continue

        print(f"✅ 成功解析 {len(parsed_data)} 个数据点")
        return parsed_data

    def get_existing_records(self, conn, market_hash_name: str) -> set:
        """
        获取数据库中已存在的记录 (market_hash_name, timestamp) 集合。
        """
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT timestamp FROM item_kline_day WHERE market_hash_name = %s",
                (market_hash_name,)
            )
            existing = cursor.fetchall()
            return {row[0] for row in existing}

    def insert_item_kline_data(self, conn, data_list: List[Dict]):
        """
        插入饰品K线数据，避免重复插入。
        """
        if not data_list:
            print("ℹ️ 无数据需要插入")
            return

        # 按饰品分组处理
        grouped_data = {}
        for item in data_list:
            market_hash_name = item['market_hash_name']
            if market_hash_name not in grouped_data:
                grouped_data[market_hash_name] = []
            grouped_data[market_hash_name].append(item)

        total_inserted = 0

        for market_hash_name, items in grouped_data.items():
            print(f"📊 处理饰品: {market_hash_name}")

            # 获取已存在的记录
            existing_timestamps = self.get_existing_records(conn, market_hash_name)
            new_data = [item for item in items if item['timestamp'] not in existing_timestamps]

            if not new_data:
                print(f"  ℹ️ 无新数据插入 ({len(items)} 条记录已存在)")
                continue

            print(f"  📥 准备插入 {len(new_data)} 条新记录")

            # 批量插入新数据
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO item_kline_day (
                    market_hash_name, timestamp, item_id, price, sell_count,
                    buy_price, buy_count, turnover, volume, total_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = [(
                    d['market_hash_name'], d['timestamp'], d['item_id'], d['price'], d['sell_count'],
                    d['buy_price'], d['buy_count'], d['turnover'], d['volume'], d['total_count']
                ) for d in new_data]

                try:
                    cursor.executemany(sql, values)
                    conn.commit()
                    print(f"  ✅ 成功插入 {len(new_data)} 条记录")
                    total_inserted += len(new_data)
                except Exception as e:
                    print(f"  ❌ 插入失败: {e}")
                    conn.rollback()

        print(f"🎯 总共插入 {total_inserted} 条新记录")

    def process_and_store_item_kline(self, market_hash_name: str, item_id: str):
        """
        主处理函数：获取饰品数据并存储到数据库。
        成功时返回解析后的数据列表，失败时返回空列表。
        """
        print(f"🚀 开始处理饰品K线数据: {market_hash_name} (ID: {item_id})")

        try:
            # 导入爬虫 (修复导入路径)
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from crawler.item_price import DailyKlineCrawler

            # 创建爬虫实例并获取数据
            print("📡 正在获取API数据...")
            crawler = DailyKlineCrawler()
            raw_data = crawler.fetch_item_details(item_id)

            if not raw_data:
                print("❌ 获取API数据失败")
                return []

            # 解析数据
            print("🔍 正在解析数据...")
            parsed_data = self.parse_item_kline_data(raw_data, market_hash_name, item_id)

            if not parsed_data:
                print("❌ 无有效数据可处理")
                return []

            # 连接数据库并处理
            conn = self.get_db_connection()
            try:
                # 确保表存在
                self.create_item_kline_day_table()

                # 插入数据
                self.insert_item_kline_data(conn, parsed_data)

                print("🎉 饰品K线数据处理完成！")
                return parsed_data

            finally:
                conn.close()

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def create_item_kline_day_table(self):
        """创建饰品日K线数据表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS item_kline_day (
            market_hash_name VARCHAR(255) NOT NULL COMMENT '饰品标识',
            timestamp BIGINT NOT NULL COMMENT '时间戳',
            item_id VARCHAR(50) COMMENT '饰品ID',
            price DECIMAL(10,2) COMMENT '当前价',
            sell_count INT DEFAULT 0 COMMENT '在售数量',
            buy_price DECIMAL(10,2) COMMENT '求购价',
            buy_count INT DEFAULT 0 COMMENT '求购数量',
            turnover DECIMAL(15,2) COMMENT '成交额',
            volume INT DEFAULT 0 COMMENT '成交量',
            total_count VARCHAR(50) COMMENT '存世量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            PRIMARY KEY (market_hash_name, timestamp),
            INDEX idx_market_timestamp (market_hash_name, timestamp),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='饰品日K线数据表'
        """

        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                print("表 'item_kline_day' 创建成功！")
        except Exception as e:
            print(f"创建表失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_tracked_items_table(self):
        """创建被追踪的饰品表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tracked_items (
            market_hash_name VARCHAR(255) NOT NULL,
            PRIMARY KEY (market_hash_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='被追踪的饰品列表';
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                print("表 'tracked_items' 初始化检查完成！")
        except Exception as e:
            print(f"创建表 'tracked_items' 失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def batch_insert_item_kline_data(self, data_list):
        """批量插入饰品K线数据"""
        if not data_list:
            print("没有数据需要插入")
            return False

        insert_sql = """
        INSERT INTO item_kline_day
        (market_hash_name, timestamp, item_id, price, sell_count, buy_price, buy_count,
         turnover, volume, total_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            item_id = VALUES(item_id),
            price = VALUES(price),
            sell_count = VALUES(sell_count),
            buy_price = VALUES(buy_price),
            buy_count = VALUES(buy_count),
            turnover = VALUES(turnover),
            volume = VALUES(volume),
            total_count = VALUES(total_count),
            updated_at = CURRENT_TIMESTAMP
        """

        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.executemany(insert_sql, data_list)
                conn.commit()
                print(f"✅ 批量插入成功，共处理 {len(data_list)} 条数据")
                return True
        except Exception as e:
            print(f"❌ 批量插入失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_item_kline_data(self, market_hash_name, start_timestamp=None, end_timestamp=None, limit=100):
        """查询饰品K线数据"""
        select_sql = """
        SELECT market_hash_name, timestamp, item_id, price, sell_count, buy_price, buy_count,
               turnover, volume, total_count, created_at, updated_at
        FROM item_kline_day
        WHERE market_hash_name = %s
        """
        params = [market_hash_name]

        if start_timestamp is not None:
            select_sql += " AND timestamp >= %s"
            params.append(start_timestamp)

        if end_timestamp is not None:
            select_sql += " AND timestamp <= %s"
            params.append(end_timestamp)

        select_sql += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(select_sql, params)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"查询数据失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    async def get_item_kline_data_for_chart(self, market_hash_name: str):
        """
        获取饰品K线数据用于图表展示，不保存到数据库。
        """
        print(f"🚀 准备为图表获取饰品K线数据: {market_hash_name}")

        try:
            # 导入爬虫
            import sys
            import os
            # 确保父目录在sys.path中，以便正确导入crawler
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.append(project_root)
            
            from crawler.item_price import DailyKlineCrawler

            # 从数据库获取 item_id
            item_id = self.get_item_id_from_db(market_hash_name)
            if not item_id:
                print(f"❌ 数据库中未找到饰品 {market_hash_name} 的 c5_id")
                raise HTTPException(status_code=404, detail=f"数据库中未找到饰品 '{market_hash_name}' 的ID,请确认饰品名称是否正确")
            
            # 创建爬虫实例并获取数据
            print("📡 正在获取API数据...")
            crawler = DailyKlineCrawler()
            raw_data = crawler.fetch_item_details(item_id) # 默认 type_day="3" (周数据)

            if not raw_data:
                print("❌ 获取API数据失败")
                return []

            # 解析数据
            print("🔍 正在解析数据...")
            parsed_data = self.parse_item_kline_data(raw_data, market_hash_name, item_id)

            if not parsed_data:
                print("❌ 无有效数据可处理")
                return []

            print(f"🎉 成功为图表获取并解析 {len(parsed_data)} 条饰品K线数据！")
            return parsed_data

        except Exception as e:
            print(f"❌ 为图表获取饰品K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def is_item_tracked(self, market_hash_name: str) -> bool:
        """
        检查饰品是否在被追踪列表中。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM tracked_items WHERE market_hash_name = %s LIMIT 1",
                    (market_hash_name,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"查询饰品追踪状态失败: {e}")
            return False  # 发生错误时，默认为不追踪
        finally:
            if conn:
                conn.close()

    async def handle_item_kline_request(self, market_hash_name: str):
        """
        根据饰品是否被追踪，决定是获取数据用于图表展示还是存入数据库。
        这个方法是处理前端请求的主要入口点。
        """
        print(f"收到K线数据请求: {market_hash_name}")

        if self.is_item_tracked(market_hash_name):
            print(f"✅ 饰品 '{market_hash_name}' 在追踪列表中，将获取并存储数据。")

            item_id = self.get_item_id_from_db(market_hash_name)
            if not item_id:
                raise HTTPException(status_code=404, detail=f"数据库中未找到饰品 '{market_hash_name}' 的ID。")

            # 在异步环境中间接调用同步方法
            loop = asyncio.get_running_loop()
            # process_and_store_item_kline 是一个IO密集型和CPU密集型（少量）的操作, 在默认的executor中运行
            result_data = await loop.run_in_executor(
                None, self.process_and_store_item_kline, market_hash_name, item_id
            )
            return result_data
        else:
            print(f"ℹ️ 饰品 '{market_hash_name}' 不在追踪列表中，仅获取数据用于图表展示。")
            return await self.get_item_kline_data_for_chart(market_hash_name)


def main():
    """主函数：演示完整的数据处理流程"""
    processor = ItemKlineProcessor()

    print("🎯 开始饰品K线数据处理流程...")

    # 示例饰品数据 (可以从搜索API获取)
    test_items = [
        {
            "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "item_id": "22499"  # 示例ID，需要从实际搜索结果获取
        },
        {
            "market_hash_name": "StatTrak™ Galil AR | Stone Cold (Battle-Scarred)",
            "item_id": "22349"  # 示例ID
        }
    ]

    success_count = 0

    for item in test_items:
        print(f"\n{'='*60}")
        try:
            success = processor.process_and_store_item_kline(
                item["market_hash_name"],
                item["item_id"]
            )
            if success:
                success_count += 1

        except Exception as e:
            print(f"❌ 处理饰品失败: {item['market_hash_name']}, 错误: {e}")

    print(f"\n{'='*60}")
    print(f"📊 处理完成! 成功: {success_count}/{len(test_items)} 个饰品")

    # 查询示例数据
    if success_count > 0:
        print("\n🔍 查询最新插入的数据...")
        try:
            results = processor.get_item_kline_data("AK-47 | Redline (Field-Tested)", limit=3)
            if results:
                print(f"✅ 查询到 {len(results)} 条记录:")
                for row in results:
                    print(f"  🏷️ 饰品: {row[0]}")
                    print(f"  ⏰ 时间戳: {row[1]}")
                    print(f"  💰 价格: {row[3]}")
                    print(f"  📦 在售: {row[4]}")
                    print(f"  🛒 求购: {row[5]}")
                    print(f"  📊 成交量: {row[8]}")
                    print("  " + "-"*40)
            else:
                print("ℹ️ 无查询结果")
        except Exception as e:
            print(f"❌ 查询失败: {e}")

    return success_count > 0


if __name__ == "__main__":
    main()