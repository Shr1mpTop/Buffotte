import logging
import pymysql
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pytz
from fastapi import HTTPException
import asyncio

from app.integrations.bufftracker import BuffTrackerClient

logger = logging.getLogger(__name__)

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
            logger.error(f"从数据库查询 item_id 失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def parse_item_kline_data(self, raw_data: dict, market_hash_name: str, item_id: str) -> List[Dict]:
        """
        解析API返回的饰品K线数据。

        bufftracker API 数据格式 (8元素):
        [timestamp, price, sell_count, buy_price, buy_count, turnover, volume, total_count]
        """
        if not raw_data or not raw_data.get("success"):
            logger.error("API返回数据无效")
            return []

        data_points = raw_data.get("data", [])
        if not data_points:
            logger.error("无数据点")
            return []

        parsed_data = []
        for point in data_points:
            try:
                # 验证数据点长度
                if len(point) < 7:
                    logger.warning(f"数据点格式不完整: {point}")
                    continue

                timestamp = int(point[0])
                price = float(point[1])
                sell_count = int(point[2]) if point[2] is not None else 0
                buy_price = float(point[3])
                buy_count = int(point[4]) if point[4] is not None else 0
                turnover = float(point[5]) if point[5] is not None else 0.0
                volume = int(point[6]) if point[6] is not None else 0
                total_count = str(int(point[7])) if len(point) > 7 and point[7] is not None else '0'

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
                    'total_count': total_count,
                }
                parsed_data.append(parsed_point)

            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"解析数据点失败: {point}, 错误: {e}")
                continue

        logger.info(f"成功解析 {len(parsed_data)} 个数据点")
        return parsed_data

    def get_existing_records(self, conn, market_hash_name: str) -> set:
        """
        获取数据库中指定饰品已存在的 timestamp 集合。
        """
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT timestamp FROM item_kline_day WHERE market_hash_name = %s",
                (market_hash_name,)
            )
            existing = cursor.fetchall()
            return {row[0] for row in existing}

    def delete_latest_row_for_item(self, conn, market_hash_name: str):
        """
        删除指定饰品数据库中最新的（timestamp 最大的）一行数据。
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(timestamp) FROM item_kline_day WHERE market_hash_name = %s",
                    (market_hash_name,)
                )
                max_ts = cursor.fetchone()
                if max_ts and max_ts[0]:
                    cursor.execute(
                        "DELETE FROM item_kline_day WHERE market_hash_name = %s AND timestamp = %s",
                        (market_hash_name, max_ts[0])
                    )
                    conn.commit()
                    logger.info(f"已删除饰品 {market_hash_name} 的最新行，timestamp: {max_ts[0]}")
                else:
                    logger.info(f"饰品 {market_hash_name} 数据库为空，无需删除")
        except Exception as e:
            logger.error(f"删除饰品 {market_hash_name} 最新行失败: {e}")

    def insert_item_kline_data(self, conn, data_list: List[Dict]):
        """
        插入饰品K线数据，避免重复插入。
        """
        if not data_list:
            logger.info("无数据需要插入")
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
            logger.info(f"处理饰品: {market_hash_name}")

            # 获取已存在的记录
            existing_timestamps = self.get_existing_records(conn, market_hash_name)
            new_data = [item for item in items if item['timestamp'] not in existing_timestamps]

            if not new_data:
                logger.info(f"无新数据插入 ({len(items)} 条记录已存在)")
                continue

            logger.info(f"准备插入 {len(new_data)} 条新记录")

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
                    logger.info(f"成功插入 {len(new_data)} 条记录")
                    total_inserted += len(new_data)
                except Exception as e:
                    logger.error(f"插入失败: {e}")
                    conn.rollback()

        logger.info(f"总共插入 {total_inserted} 条新记录")

    def _store_parsed_kline(self, market_hash_name: str, parsed_data: List[Dict]):
        """将已解析的K线数据存入数据库（使用 UPSERT 确保时间戳更新）。"""
        try:
            self.create_item_kline_day_table()
            values = [(
                d['market_hash_name'], d['timestamp'], d['item_id'], d['price'], d['sell_count'],
                d['buy_price'], d['buy_count'], d['turnover'], d['volume'], d['total_count']
            ) for d in parsed_data]
            self.batch_insert_item_kline_data(values)
            logger.info(f"成功存储 {len(parsed_data)} 条K线数据: {market_hash_name}")
        except Exception as e:
            logger.error(f"存储K线数据失败: {e}")

    def process_and_store_item_kline(
        self,
        market_hash_name: str,
        item_id: str,
        platform: str = "BUFF",
        type_day: str = "1",
        date_type: int = 3,
    ):
        """
        主处理函数：获取饰品数据并存储到数据库。
        成功时返回解析后的数据列表，失败时返回空列表。
        """
        logger.info(f"开始处理饰品K线数据: {market_hash_name} (ID: {item_id})")

        try:
            # 导入爬虫 (修复导入路径)
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from crawler.item_price import DailyKlineCrawler

            # 创建爬虫实例并获取数据
            logger.info("正在获取API数据...")
            crawler = DailyKlineCrawler()
            raw_data = crawler.fetch_item_details(
                item_id,
                platform=platform,
                type_day=type_day,
                date_type=date_type,
                hashname=market_hash_name,
            )

            if not raw_data:
                logger.error("获取API数据失败")
                return []

            # 解析数据
            logger.info("正在解析数据...")
            parsed_data = self.parse_item_kline_data(raw_data, market_hash_name, item_id)

            if not parsed_data:
                logger.error("无有效数据可处理")
                return []

            # 连接数据库并处理
            conn = self.get_db_connection()
            try:
                # 确保表存在
                self.create_item_kline_day_table()

                # 先删除数据库的最新一行数据
                self.delete_latest_row_for_item(conn, market_hash_name)

                # 插入数据
                self.insert_item_kline_data(conn, parsed_data)

                logger.info("饰品K线数据处理完成！")
                return parsed_data

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
                logger.info("表 'item_kline_day' 创建成功！")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise
        finally:
            if conn:
                conn.close()



    def batch_insert_item_kline_data(self, data_list):
        """批量插入饰品K线数据"""
        if not data_list:
            logger.info("没有数据需要插入")
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
                logger.info(f"批量插入成功，共处理 {len(data_list)} 条数据")
                return True
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
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
            logger.error(f"查询数据失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    async def get_item_kline_data_for_chart(
        self,
        market_hash_name: str,
        platform: str = "BUFF",
        type_day: str = "1",
        date_type: int = 3,
    ):
        """
        获取饰品K线数据用于图表展示，不保存到数据库。
        """
        logger.info(f"准备为图表获取饰品K线数据: {market_hash_name}")

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
                logger.error(f"数据库中未找到饰品 {market_hash_name} 的 c5_id")
                raise HTTPException(status_code=404, detail=f"数据库中未找到饰品 '{market_hash_name}' 的ID,请确认饰品名称是否正确")
            
            # 创建爬虫实例并获取数据
            logger.info("正在获取API数据...")
            crawler = DailyKlineCrawler()
            raw_data = crawler.fetch_item_details(
                item_id,
                platform=platform,
                type_day=type_day,
                date_type=date_type,
                hashname=market_hash_name,
            )

            if not raw_data:
                logger.error("获取API数据失败")
                return []

            # 解析数据
            logger.info("正在解析数据...")
            parsed_data = self.parse_item_kline_data(raw_data, market_hash_name, item_id)

            if not parsed_data:
                logger.error("无有效数据可处理")
                return []

            logger.info(f"成功为图表获取并解析 {len(parsed_data)} 条饰品K线数据！")
            return parsed_data

        except Exception as e:
            logger.error(f"为图表获取饰品K线数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
                    "SELECT 1 FROM track WHERE market_hash_name = %s LIMIT 1",
                    (market_hash_name,)
                )
                result = cursor.fetchone()
                logger.debug(f"is_item_tracked for '{market_hash_name}': {result is not None}")
                return result is not None
        except Exception as e:
            logger.error(f"查询饰品追踪状态失败: {e}")
            return False  # 发生错误时，默认为不追踪
        finally:
            if conn:
                conn.close()

    def get_cached_kline_data(self, market_hash_name: str, limit: int = 365) -> Tuple[List[Dict], Optional[str]]:
        """
        从 item_kline_day 表读取缓存的K线数据。
        返回 (data_list, last_updated_str)，ASC 排序以适配前端图表。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """SELECT timestamp, item_id, price, sell_count,
                              buy_price, buy_count, turnover, volume, total_count
                       FROM item_kline_day
                       WHERE market_hash_name = %s
                       ORDER BY timestamp ASC
                       LIMIT %s""",
                    (market_hash_name, limit)
                )
                rows = cursor.fetchall()

                # 获取最后更新时间
                cursor.execute(
                    "SELECT MAX(updated_at) AS last_updated FROM item_kline_day WHERE market_hash_name = %s",
                    (market_hash_name,)
                )
                last_updated_row = cursor.fetchone()
                last_updated = None
                if last_updated_row:
                    val = list(last_updated_row.values())[0]
                    if val:
                        last_updated = val.isoformat() if hasattr(val, 'isoformat') else str(val)

                return rows, last_updated
        except Exception as e:
            logger.error(f"读取缓存K线数据失败: {e}")
            return [], None
        finally:
            if conn:
                conn.close()

    def is_cache_fresh(self, market_hash_name: str, max_age_hours: int = 1) -> bool:
        """检查缓存是否在指定时间内更新过，避免频繁抓取。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(updated_at) FROM item_kline_day WHERE market_hash_name = %s",
                    (market_hash_name,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    from datetime import datetime as dt
                    age = dt.now() - result[0]
                    return age.total_seconds() < max_age_hours * 3600
                return False
        except Exception as e:
            logger.error(f"检查缓存新鲜度失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_tracked_items(self) -> List[Dict]:
        """查询所有追踪中的饰品 (DISTINCT market_hash_name + c5_id)。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """SELECT DISTINCT t.market_hash_name, c.c5_id as item_id
                       FROM track t
                       LEFT JOIN cs2_items c
                           ON t.market_hash_name COLLATE utf8mb4_unicode_ci = c.market_hash_name
                       WHERE c.c5_id IS NOT NULL"""
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取所有追踪饰品失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def refresh_kline_for_all_tracked(self):
        """通过 buff-tracker API 批量刷新所有追踪饰品的K线数据。"""
        items = self.get_all_tracked_items()
        if not items:
            logger.info("没有追踪中的饰品，跳过刷新。")
            return

        bufftracker_client = BuffTrackerClient()
        success_count = 0
        fail_count = 0
        total = len(items)

        for idx, item in enumerate(items, 1):
            name = item['market_hash_name']
            item_id = str(item['item_id'])
            logger.info(f"[{idx}/{total}] 刷新: {name}")
            try:
                data = bufftracker_client.get_item_kline_data_sync(
                    name,
                    platform="BUFF",
                    type_day="1",
                    date_type=3,
                )

                if not data.get("success") or not data.get("data"):
                    fail_count += 1
                    logger.warning(f"饰品 {name} 返回无效数据")
                    continue

                parsed = self.parse_item_kline_data(data, name, item_id)
                if parsed:
                    self._store_parsed_kline(name, parsed)
                    success_count += 1
                else:
                    fail_count += 1
                    logger.warning(f"饰品 {name} 解析数据为空")
            except Exception as e:
                fail_count += 1
                logger.error(f"饰品 {name} 刷新失败: {e}")
            # 延迟避免触发限制
            if idx < total:
                time.sleep(2)

        logger.info(f"批量刷新完成: 成功 {success_count}, 失败 {fail_count}, 总计 {total}")

    async def handle_item_kline_request(
        self,
        market_hash_name: str,
        platform: str = "BUFF",
        type_day: str = "1",
        date_type: int = 3,
    ):
        """
        根据饰品是否被追踪，决定是获取数据用于图表展示还是存入数据库。
        这个方法是处理前端请求的主要入口点。
        """
        logger.info(f"收到K线数据请求: {market_hash_name}")

        if self.is_item_tracked(market_hash_name):
            logger.info(f"饰品 '{market_hash_name}' 在追踪列表中，将获取并存储数据。")

            item_id = self.get_item_id_from_db(market_hash_name)
            if not item_id:
                raise HTTPException(status_code=404, detail=f"数据库中未找到饰品 '{market_hash_name}' 的ID。")

            # 在异步环境中间接调用同步方法
            loop = asyncio.get_running_loop()
            # process_and_store_item_kline 是一个IO密集型和CPU密集型（少量）的操作, 在默认的executor中运行
            result_data = await loop.run_in_executor(
                None,
                self.process_and_store_item_kline,
                market_hash_name,
                item_id,
                platform,
                type_day,
                date_type,
            )
            return result_data
        else:
            logger.info(f"饰品 '{market_hash_name}' 不在追踪列表中，仅获取数据用于图表展示。")
            return await self.get_item_kline_data_for_chart(
                market_hash_name,
                platform=platform,
                type_day=type_day,
                date_type=date_type,
            )


def main():
    """主函数：演示完整的数据处理流程"""
    processor = ItemKlineProcessor()

    logger.info("开始饰品K线数据处理流程...")

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
            logger.error(f"处理饰品失败: {item['market_hash_name']}, 错误: {e}")

    print(f"\n{'='*60}")
    logger.info(f"处理完成! 成功: {success_count}/{len(test_items)} 个饰品")

    # 查询示例数据
    if success_count > 0:
        logger.info("查询最新插入的数据...")
        try:
            results = processor.get_item_kline_data("AK-47 | Redline (Field-Tested)", limit=3)
            if results:
                logger.info(f"查询到 {len(results)} 条记录:")
                for row in results:
                    logger.info(f"  饰品: {row[0]}, 时间戳: {row[1]}, 价格: {row[3]}, 在售: {row[4]}, 求购: {row[5]}, 成交量: {row[8]}")
            else:
                logger.info("无查询结果")
        except Exception as e:
            logger.error(f"查询失败: {e}")

    return success_count > 0


if __name__ == "__main__":
    import sys
    processor = ItemKlineProcessor()
    if "--refresh-tracked" in sys.argv:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        processor.refresh_kline_for_all_tracked()
    else:
        main()
