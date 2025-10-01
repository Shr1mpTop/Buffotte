"""
kline_crawler.py

封装 Kline 爬虫工具：

- 类: KlineCrawler
- 方法:
    - fetch_recent(timestamp_ms=None, ktype='day') -> 调用 API 获取近三个月以内的数据（不传 maxTime）
    - fetch_historical(timestamp_ms=None, ktype='day', max_time_seconds=...) -> 获取更早历史数据（需要传 maxTime，单位为秒）
    - parse_data_rows(data) -> 将 API 返回转换为 [(ts, open, high, low, close, vol, turnover), ...]
    - connect_db/create_kline_table/insert_rows/disconnect_db -> 可选的 MySQL 插入支持（使用 pymysql）

CLI:
    - --mode recent|historical
    - --type hour|day|week
    - --maxTime <seconds>  (用于 historical 模式)
    - --config <path>      (可选，传入 db config json 后会将抓取结果插入数据库)

示例:
    python kline_crawler.py --mode recent --type day
    python kline_crawler.py --mode historical --type day --maxTime 1719759600 --config ./config.json

"""

import time
import json
import requests
from typing import Optional, List, Tuple

try:
    import pymysql
except Exception:
    pymysql = None  # DB 插入为可选依赖


class KlineCrawler:
    """封装 Kline 爬虫。

    - 支持 type_map: 'hour'->1, 'day'->2, 'week'->3
    - fetch_recent: 用于拉取近三个月以内的数据（不传 maxTime）
    - fetch_historical: 用于拉取更早的历史数据（需传 maxTime，单位为秒）
    - 可选数据库插入（如果传入 db_config，并且安装了 pymysql）
    """

    TYPE_MAP = {"hour": 1, "day": 2, "week": 3}
    BASE_URL = "https://api.steamdt.com/user/statistics/v1/kline"

    def __init__(self, db_config_path: str = None, session: Optional[requests.Session] = None):
        self.db_config = None
        self.conn = None
        self.cursor = None
        if db_config_path:
            with open(db_config_path, "r", encoding="utf-8") as f:
                full_config = json.load(f)
            # Only keep pymysql connection parameters
            db_keys = {'host', 'user', 'username', 'password', 'database', 'db', 'port', 'charset'}
            self.db_config = {k: v for k, v in full_config.items() if k in db_keys}
            # Handle username/user alias
            if 'username' in self.db_config and 'user' not in self.db_config:
                self.db_config['user'] = self.db_config.pop('username')
            if 'db' in self.db_config and 'database' not in self.db_config:
                self.db_config['database'] = self.db_config.pop('db')
        self.session = session or requests.Session()

    def _build_headers(self) -> dict:
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9",
            "access-token": "undefined",
            "language": "zh_CN",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "user-agent": "Mozilla/5.0",
            "x-app-version": "1.0.0",
            "x-currency": "CNY",
            "x-device": "1",
        }

    def connect_db(self):
        if not self.db_config:
            raise RuntimeError("db_config not provided")
        if pymysql is None:
            raise RuntimeError("pymysql not installed")
        self.conn = pymysql.connect(**self.db_config)
        self.cursor = self.conn.cursor()

    def disconnect_db(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def _request(self, timestamp_s: int, ktype: str, max_time_seconds: Optional[int] = None) -> Optional[dict]:
        """内部请求：所有时间参数均为秒（s）。
        timestamp_s: 请求使用的 timestamp（秒）
        max_time_seconds: optional maxTime（秒）
        """
        tnum = self.TYPE_MAP.get(ktype, 1)
        params = {"timestamp": timestamp_s, "type": tnum}
        # 当 max_time_seconds 为 None 时，API 只接收 timestamp 和 type（用于近三个月数据）
        if max_time_seconds is not None:
            params["maxTime"] = max_time_seconds

        resp = self.session.get(self.BASE_URL, params=params, headers=self._build_headers(), timeout=15)
        if resp.status_code != 200:
            print(f"Request failed: {resp.status_code} {resp.text[:200]}")
            return None
        try:
            return resp.json()
        except Exception as e:
            print(f"JSON decode failed: {e}")
            return None

    def fetch_recent(self, timestamp_s: Optional[int] = None, ktype: str = "day") -> Optional[dict]:
        """获取近三个月的数据（不传 maxTime）。

        timestamp_s: 秒时间戳。如果为 None 则使用当前时间（秒）。
        ktype: 'hour'|'day'|'week'
        返回解析后的 JSON（或 None）
        """
        if timestamp_s is None:
            timestamp_s = int(time.time())
        return self._request(timestamp_s, ktype, max_time_seconds=None)

    def fetch_historical(self, timestamp_s: Optional[int] = None, ktype: str = "day", max_time_seconds: Optional[int] = None) -> Optional[dict]:
        """获取历史数据（需要传 maxTime，单位为秒）

        - timestamp_s: 秒时间戳，作为请求参照点
        - max_time_seconds: 以秒为单位的 maxTime 用于请求更早的数据（API 示例中使用秒）
        """
        if timestamp_s is None:
            timestamp_s = int(time.time())
        return self._request(timestamp_s, ktype, max_time_seconds=max_time_seconds)

    @staticmethod
    def parse_data_rows(data: dict) -> List[Tuple[int, float, float, float, float, int, float]]:
        """从 API 返回解析出 rows：[(ts_seconds, open, high, low, close, vol, turnover), ...]

        注：API 有时会返回以毫秒为单位的时间戳（13 位），此方法会自动把毫秒转换为秒（除以 1000）。
        """
        out = []
        if not data or "data" not in data:
            return out
        rows = data["data"]
        if not isinstance(rows, list):
            return out
        for item in rows:
            if not isinstance(item, (list, tuple)) or len(item) < 7:
                continue
            ts = int(item[0])
            # 如果 ts 看起来像毫秒（大于 1e11），把它转为秒
            if ts > 1e11:
                ts = int(ts / 1000)
            open_p, high_p, low_p, close_p = item[1], item[2], item[3], item[4]
            vol = int(item[5])
            turnover = float(item[6])
            out.append((ts, open_p, high_p, low_p, close_p, vol, turnover))
        return out

    def insert_rows(self, rows: List[Tuple[int, float, float, float, float, int, float]], ktype: str = "day") -> int:
        """将解析后的 rows 插入数据库，返回插入计数（使用 INSERT IGNORE）。需要先 connect_db()。"""
        if not self.cursor or not self.conn:
            raise RuntimeError("DB not connected. Call connect_db() first.")
        table_name = f"kline_data_{ktype}"
        inserted = 0
        for r in rows:
            try:
                self.cursor.execute(
                    f"""
                    INSERT IGNORE INTO {table_name} (timestamp, open_price, high_price, low_price, close_price, volume, turnover)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    r,
                )
                inserted += 1
            except Exception as e:
                print(f"DB insert error for ts={r[0]}: {e}")
        self.conn.commit()
        return inserted

    def create_kline_table(self, ktype: str = "day"):
        """Create table if not exists for the kline type."""
        if not self.cursor or not self.conn:
            raise RuntimeError("DB not connected. Call connect_db() first.")
        table_name = f"kline_data_{ktype}"
        self.cursor.execute(
            f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            timestamp BIGINT PRIMARY KEY,
            open_price DECIMAL(10,2),
            high_price DECIMAL(10,2),
            low_price DECIMAL(10,2),
            close_price DECIMAL(10,2),
            volume BIGINT,
            turnover DECIMAL(15,2),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        )
        self.conn.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KlineCrawler: fetch recent or historical kline data")
    parser.add_argument('--config', '-c', default=None, help='db config json path (optional)')
    parser.add_argument('--mode', '-m', choices=['recent', 'historical'], default='recent')
    parser.add_argument('--type', '-t', choices=['hour', 'day', 'week'], default='day')
    parser.add_argument('--maxTime', help='maxTime (seconds) for historical requests', type=int)
    args = parser.parse_args()

    crawler = KlineCrawler(db_config_path=args.config)

    # 根据 mode 调用相应方法
    if args.mode == 'recent':
        data = crawler.fetch_recent(ktype=args.type)
    else:
        data = crawler.fetch_historical(ktype=args.type, max_time_seconds=args.maxTime)

    if data:
        rows = KlineCrawler.parse_data_rows(data)
        print(f"Fetched {len(rows)} rows")

        # 如果提供了 DB config，则插入
        if args.config:
            try:
                crawler.connect_db()
                crawler.create_kline_table(ktype=args.type)
                inserted = crawler.insert_rows(rows, ktype=args.type)
                print(f"Inserted {inserted} rows into DB table kline_data_{args.type}")
            except Exception as e:
                print(f"DB operation failed: {e}")
            finally:
                try:
                    crawler.disconnect_db()
                except Exception:
                    pass
    else:
        print("No data returned")
