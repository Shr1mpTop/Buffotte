import json
import time
from typing import List, Tuple, Optional
import pymysql
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz

# 加载环境变量
load_dotenv()

class KlineDataProcessor:
    def __init__(self):
        self.remote_config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('USER'),
            'password': os.getenv('PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }

    def get_db_connection(self):
        return pymysql.connect(**self.remote_config)

    def _timestamp_to_date_str(self, ts: int) -> str:
        """
        将 UTC+8 时间戳（秒）转换为 YYYY-MM-DD 格式的日期字符串。
        """
        tz = pytz.timezone('Asia/Shanghai')
        return datetime.fromtimestamp(ts, tz).strftime('%Y-%m-%d')

    def create_table_if_not_exists(self, conn):
        """
        如果表不存在，创建 kline_data_day 表。
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS kline_data_day (
            timestamp BIGINT PRIMARY KEY,
            date DATE,
            open_price DECIMAL(10,2),
            high_price DECIMAL(10,2),
            low_price DECIMAL(10,2),
            close_price DECIMAL(10,2),
            volume INT,
            turnover DECIMAL(15,2)
        )
        """
    def delete_latest_row(self, conn):
        """
        删除数据库中最新的（timestamp 最大的）一行数据。
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(timestamp) FROM kline_data_day")
                max_ts = cursor.fetchone()
                if max_ts and max_ts[0]:
                    cursor.execute("DELETE FROM kline_data_day WHERE timestamp = %s", (max_ts[0],))
                    conn.commit()
                    print(f"已删除最新行，timestamp: {max_ts[0]}")
                else:
                    print("数据库为空，无需删除")
        except Exception as e:
            print(f"删除最新行失败: {e}")
    def parse_kline_data(self, raw_json: dict) -> Tuple[List[dict], dict]:
        """
        解析日K数据 JSON。
        返回：(历史数据列表, 实时数据字典)
        """
        if not raw_json.get('success') or not raw_json.get('data'):
            raise ValueError("无效的 JSON 数据")

        data = raw_json['data']
        if len(data) < 1:
            raise ValueError("数据为空")

        # 分离最后一个为实时数据
        historical_data = data[:-1]  # 其余为历史数据
        real_time_data = data[-1]    # 最后一个为实时数据

        # 转换为字典格式，便于处理
        historical_list = []
        for item in historical_data:
            historical_list.append({
                'timestamp': int(item[0]),
                'open': float(item[1]),
                'high': float(item[3]),  # high 是 item[3]
                'low': float(item[4]),   # low 是 item[4]
                'close': float(item[2]), # close 是 item[2]
                'volume': int(item[5]) if item[5] else 0,
                'turnover': float(item[6]) if item[6] else 0.0
            })

        real_time_dict = {
            'timestamp': int(real_time_data[0]),
            'open': float(real_time_data[1]),
            'high': float(real_time_data[3]),  # high 是 item[3]
            'low': float(real_time_data[4]),   # low 是 item[4]
            'close': float(real_time_data[2]), # close 是 item[2]
            'volume': int(real_time_data[5]) if real_time_data[5] else 0,
            'turnover': float(real_time_data[6]) if real_time_data[6] else 0.0
        }

        return historical_list, real_time_dict

    def get_existing_timestamps(self, conn) -> set:
        """
        获取数据库中已存在的 timestamp 集合。
        """
        with conn.cursor() as cursor:
            cursor.execute("SELECT timestamp FROM kline_data_day")
            existing = cursor.fetchall()
            return {row[0] for row in existing}

    def insert_historical_data(self, conn, data_list: List[dict]):
        """
        插入历史数据，只插入新数据（避免重复）。
        """
        existing_timestamps = self.get_existing_timestamps(conn)
        new_data = [item for item in data_list if item['timestamp'] not in existing_timestamps]

        if not new_data:
            print("无新历史数据插入")
            return

        with conn.cursor() as cursor:
            sql = """
            INSERT INTO kline_data_day (timestamp, date, open_price, high_price, low_price, close_price, volume, turnover)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = [(
                d['timestamp'],
                self._timestamp_to_date_str(d['timestamp']),
                d['open'], d['high'], d['low'], d['close'], d['volume'], d['turnover']
            ) for d in new_data]
            cursor.executemany(sql, values)
            conn.commit()
            print(f"插入 {len(new_data)} 条新历史数据")

    def insert_real_time_data(self, conn, data: dict):
        """
        插入实时数据（可覆盖或标记为实时）。
        假设实时数据存储在同一表，或可扩展为单独表。
        """
        with conn.cursor() as cursor:
            # 先删除旧的实时数据（如果有），然后插入新实时数据
            cursor.execute("DELETE FROM kline_data_day WHERE timestamp = %s", (data['timestamp'],))
            sql = """
            INSERT INTO kline_data_day (timestamp, date, open_price, high_price, low_price, close_price, volume, turnover)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['timestamp'],
                self._timestamp_to_date_str(data['timestamp']),
                data['open'], data['high'], data['low'], data['close'], data['volume'], data['turnover']
            ))
            conn.commit()
            print("插入实时数据")

    def process_and_store(self, raw_json: dict):
        """
        主处理函数：解析数据并存储到数据库。
        """
        try:
            historical_data, real_time_data = self.parse_kline_data(raw_json)
            conn = self.get_db_connection()
            self.create_table_if_not_exists(conn)  # 确保表存在

            # 先删除数据库的最新一行数据
            self.delete_latest_row(conn)

            # 插入历史数据（只新数据）
            self.insert_historical_data(conn, historical_data)

            # 插入实时数据
            self.insert_real_time_data(conn, real_time_data)

            conn.close()
            print("数据处理完成")
        except Exception as e:
            print(f"处理失败: {e}")

if __name__ == "__main__":
    processor = KlineDataProcessor()
    from crawler.daily_crawler import DailyKlineCrawler
    crawler = DailyKlineCrawler()
    raw_data = crawler.fetch_daily_data()
    if raw_data:
        processor.process_and_store(raw_data)