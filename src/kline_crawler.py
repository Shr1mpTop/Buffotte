"""
kline_crawler_enhanced.py

增强版 Kline 爬虫工具：

新增功能:
1. 支持时线数据爬取和过滤（只保留 xx:55:10 的数据点）
2. 自动计算多个技术指标（MA, EMA, MACD, RSI, KDJ, 布林带）
3. 技术指标随 K线数据一起存入数据库

使用示例:
    # 爬取最新时线数据
    python kline_crawler_enhanced.py --mode recent --type hour --config ./config.json
    
    # 爬取历史时线数据
    python kline_crawler_enhanced.py --mode historical --type hour --maxTime 1719414000 --config ./config.json
    
    # 批量爬取多个历史时间点
    python kline_crawler_enhanced.py --mode batch --type hour --config ./config.json
"""

import time
import json
import requests
from typing import Optional, List, Tuple
from datetime import datetime

try:
    import pymysql
except Exception:
    pymysql = None

try:
    import pandas as pd
    import numpy as np
except Exception:
    pd = None
    np = None


class KlineCrawlerEnhanced:
    """增强版 Kline 爬虫
    
    支持:
    - 时线/日线/周线数据爬取
    - 时线数据过滤（xx:55:10）
    - 技术指标自动计算
    - 数据库批量插入
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
        """内部请求：所有时间参数均为秒（s）"""
        tnum = self.TYPE_MAP.get(ktype, 1)
        params = {"timestamp": timestamp_s, "type": tnum}
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
        """获取近三个月的数据（不传 maxTime）"""
        if timestamp_s is None:
            timestamp_s = int(time.time())
        return self._request(timestamp_s, ktype, max_time_seconds=None)

    def fetch_historical(self, timestamp_s: Optional[int] = None, ktype: str = "day", 
                        max_time_seconds: Optional[int] = None) -> Optional[dict]:
        """获取历史数据（需要传 maxTime，单位为秒）"""
        if timestamp_s is None:
            timestamp_s = int(time.time())
        return self._request(timestamp_s, ktype, max_time_seconds=max_time_seconds)

    @staticmethod
    def parse_data_rows(data: dict, ktype: str = "day", filter_hour: bool = False) -> List[Tuple]:
        """从 API 返回解析出 rows
        
        Args:
            data: API 返回的数据
            ktype: K线类型 (hour/day/week)
            filter_hour: 如果为 True 且 ktype='hour'，则只保留 xx:55:10 的数据
            
        Returns:
            [(ts_seconds, open, high, low, close, vol, turnover), ...]
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
            
            # 时线数据过滤：只保留 xx:55:10 的数据
            if filter_hour and ktype == "hour":
                dt = datetime.fromtimestamp(ts)
                # 检查是否为 xx:55:10
                if not (dt.minute == 55 and dt.second == 10):
                    continue
            
            open_p, close_p, high_p, low_p = item[1], item[2], item[3], item[4]
            vol = int(item[5])
            turnover = float(item[6])
            out.append((ts, open_p, high_p, low_p, close_p, vol, turnover))
        
        return out

    @staticmethod
    def calculate_indicators(rows: List[Tuple]):
        """计算技术指标
        
        Args:
            rows: [(timestamp, open, high, low, close, volume, turnover), ...]
            
        Returns:
            DataFrame with all indicators
        """
        if pd is None or np is None:
            raise RuntimeError("pandas and numpy are required for indicator calculation")
        
        if not rows:
            return pd.DataFrame()
        
        # 创建 DataFrame
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 1. 移动平均线 (MA)
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma30'] = df['close'].rolling(window=30, min_periods=1).mean()
        
        # 2. 指数移动平均线 (EMA)
        df['ema12'] = df['close'].ewm(span=12, adjust=False, min_periods=1).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False, min_periods=1).mean()
        
        # 3. MACD
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False, min_periods=1).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 4. RSI (相对强弱指标)
        for period in [6, 12, 24]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
            rs = gain / loss.replace(0, 1e-10)
            df[f'rsi{period}'] = 100 - (100 / (1 + rs))
        
        # 5. KDJ 指标
        low_list = df['low'].rolling(window=9, min_periods=1).min()
        high_list = df['high'].rolling(window=9, min_periods=1).max()
        rsv = (df['close'] - low_list) / (high_list - low_list).replace(0, 1e-10) * 100
        df['k_value'] = rsv.ewm(com=2, adjust=False, min_periods=1).mean()
        df['d_value'] = df['k_value'].ewm(com=2, adjust=False, min_periods=1).mean()
        df['j_value'] = 3 * df['k_value'] - 2 * df['d_value']
        
        # 6. 布林带 (Bollinger Bands)
        df['bollinger_middle'] = df['close'].rolling(window=20, min_periods=1).mean()
        std = df['close'].rolling(window=20, min_periods=1).std()
        df['bollinger_upper'] = df['bollinger_middle'] + (std * 2)
        df['bollinger_lower'] = df['bollinger_middle'] - (std * 2)
        
        # 填充 NaN 值 - 使用新的方法
        df = df.bfill().ffill().fillna(0)
        
        return df

    def create_kline_table(self, ktype: str = "day"):
        """创建 K线数据表（包含技术指标字段）"""
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
            ma5 DECIMAL(10,2),
            ma10 DECIMAL(10,2),
            ma20 DECIMAL(10,2),
            ma30 DECIMAL(10,2),
            ema12 DECIMAL(10,2),
            ema26 DECIMAL(10,2),
            macd DECIMAL(10,4),
            macd_signal DECIMAL(10,4),
            macd_hist DECIMAL(10,4),
            rsi6 DECIMAL(10,4),
            rsi12 DECIMAL(10,4),
            rsi24 DECIMAL(10,4),
            k_value DECIMAL(10,4),
            d_value DECIMAL(10,4),
            j_value DECIMAL(10,4),
            bollinger_upper DECIMAL(10,2),
            bollinger_middle DECIMAL(10,2),
            bollinger_lower DECIMAL(10,2),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_timestamp (timestamp)
        )
        '''
        )
        self.conn.commit()

    def insert_rows_with_indicators(self, rows: List[Tuple], ktype: str = "day") -> int:
        """计算技术指标并插入数据库
        
        Args:
            rows: 原始 K线数据
            ktype: K线类型
            
        Returns:
            插入的行数
        """
        if not self.cursor or not self.conn:
            raise RuntimeError("DB not connected. Call connect_db() first.")
        
        if not rows:
            return 0
            
        if pd is None:
            print("Warning: pandas not available, inserting without indicators")
            return self._insert_rows_simple(rows, ktype)
        
        table_name = f"kline_data_{ktype}"
        inserted = 0
        
        try:
            # 计算技术指标
            df = self.calculate_indicators(rows)
            
            # 批量插入
            for _, row in df.iterrows():
                try:
                    self.cursor.execute(
                        f"""
                        INSERT IGNORE INTO {table_name} (
                            timestamp, open_price, high_price, low_price, close_price, volume, turnover,
                            ma5, ma10, ma20, ma30, ema12, ema26,
                            macd, macd_signal, macd_hist,
                            rsi6, rsi12, rsi24,
                            k_value, d_value, j_value,
                            bollinger_upper, bollinger_middle, bollinger_lower
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s
                        )
                        """,
                        (
                            int(row['timestamp']), float(row['open']), float(row['high']), 
                            float(row['low']), float(row['close']), int(row['volume']), float(row['turnover']),
                            float(row['ma5']), float(row['ma10']), float(row['ma20']), float(row['ma30']),
                            float(row['ema12']), float(row['ema26']),
                            float(row['macd']), float(row['macd_signal']), float(row['macd_hist']),
                            float(row['rsi6']), float(row['rsi12']), float(row['rsi24']),
                            float(row['k_value']), float(row['d_value']), float(row['j_value']),
                            float(row['bollinger_upper']), float(row['bollinger_middle']), float(row['bollinger_lower'])
                        )
                    )
                    if self.cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    print(f"DB insert error for ts={int(row['timestamp'])}: {e}")
        except Exception as e:
            print(f"Indicator calculation failed: {e}")
            import traceback
            traceback.print_exc()
        
        self.conn.commit()
        return inserted

    def _insert_rows_simple(self, rows: List[Tuple], ktype: str = "day") -> int:
        """简单插入（不计算指标）"""
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
                if self.cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"DB insert error for ts={r[0]}: {e}")
        self.conn.commit()
        return inserted


def batch_fetch_historical_hours(crawler, max_times, ktype='hour', delay=2.0):
    """批量获取历史时线数据
    
    Args:
        crawler: KlineCrawlerEnhanced 实例
        max_times: maxTime 列表（秒时间戳）
        ktype: K线类型
        delay: 每次请求之间的延迟（秒），默认2秒
    
    注意：历史数据不过滤 xx:55:10，因为旧数据不是严格按这个时间点记录的
    """
    all_rows = []
    retry_count = 0
    max_retries = 3
    
    for i, max_time in enumerate(max_times):
        print(f"Fetching batch {i+1}/{len(max_times)}, maxTime={max_time}")
        
        # 重试逻辑
        for attempt in range(max_retries):
            data = crawler.fetch_historical(ktype=ktype, max_time_seconds=max_time)
            
            if data:
                # 检查是否有错误码
                if isinstance(data, dict) and data.get('success') == False:
                    error_msg = data.get('errorMsg', 'Unknown error')
                    print(f"  ⚠ API Error: {error_msg}")
                    if data.get('errorCode') == 102:  # 速率限制
                        wait_time = delay * (2 ** attempt)  # 指数退避
                        print(f"  ⏳ Rate limited, waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        break  # 其他错误不重试
                
                # 成功获取数据 - 历史数据不过滤
                rows = KlineCrawlerEnhanced.parse_data_rows(data, ktype=ktype, filter_hour=False)
                print(f"  ✓ Fetched {len(rows)} rows (no filter for historical data)")
                all_rows.extend(rows)
                break
            else:
                print(f"  ✗ No data returned (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        
        # 请求之间的延迟
        if i < len(max_times) - 1:  # 不是最后一个
            print(f"  ⏳ Waiting {delay}s before next request...")
            time.sleep(delay)
    
    return all_rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced KlineCrawler with technical indicators")
    parser.add_argument('--config', '-c', default=None, help='db config json path (optional)')
    parser.add_argument('--mode', '-m', choices=['recent', 'historical', 'batch'], default='recent')
    parser.add_argument('--type', '-t', choices=['hour', 'day', 'week'], default='hour')
    parser.add_argument('--maxTime', help='maxTime (seconds) for historical requests', type=int)
    args = parser.parse_args()

    crawler = KlineCrawlerEnhanced(db_config_path=args.config)

    if args.mode == 'batch':
        # 批量模式：爬取所有历史数据
        historical_max_times = [
            1756911600, 1754233200, 1751554800, 1748876400, 1746198000,
            1743519600, 1740841200, 1738162800, 1735484400, 1732806000,
            1730127600, 1727449200, 1724770800, 1722092400, 1719414000,
            1716735600, 1714057200, 1711378800, 1708700400, 1706022000,
            1703343600, 1700665200, 1697986800, 1695308400, 1692626400,
            1689951600, 1687273200, 1684594800, 1681916400, 1679238000,
            1676559600, 1673881200, 1671202800, 1668524400, 1665846000,
            1663167600, 1660489200, 1657810800]
        
        print(f"Batch mode: fetching {len(historical_max_times)} historical periods for {args.type}")
        print("⚠ Note: Using 2-second delay between requests to avoid rate limiting")
        
        # 先获取最新数据（需要过滤 xx:55:10）
        print("Fetching recent data (with xx:55:10 filter)...")
        recent_data = crawler.fetch_recent(ktype=args.type)
        all_rows = []
        if recent_data:
            # 最新数据需要过滤 xx:55:10
            recent_rows = KlineCrawlerEnhanced.parse_data_rows(
                recent_data, ktype=args.type, filter_hour=(args.type == 'hour')
            )
            print(f"Recent data: {len(recent_rows)} rows (filtered)")
            all_rows.extend(recent_rows)
        
        # 再获取历史数据（不过滤，因为历史数据不严格按 xx:55:10 记录）
        print("\nFetching historical data (no time filter)...")
        historical_rows = batch_fetch_historical_hours(crawler, historical_max_times, ktype=args.type)
        all_rows.extend(historical_rows)
        
        print(f"\nTotal fetched: {len(all_rows)} rows")
        
        # 去重（基于时间戳）
        unique_rows = {}
        for row in all_rows:
            unique_rows[row[0]] = row
        all_rows = list(unique_rows.values())
        print(f"After deduplication: {len(all_rows)} rows")
        
        # 插入数据库
        if args.config and all_rows:
            try:
                crawler.connect_db()
                crawler.create_kline_table(ktype=args.type)
                inserted = crawler.insert_rows_with_indicators(all_rows, ktype=args.type)
                print(f"Inserted {inserted} rows into DB table kline_data_{args.type}")
            except Exception as e:
                print(f"DB operation failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                crawler.disconnect_db()
    
    elif args.mode == 'recent':
        data = crawler.fetch_recent(ktype=args.type)
        if data:
            rows = KlineCrawlerEnhanced.parse_data_rows(
                data, ktype=args.type, filter_hour=(args.type == 'hour')
            )
            print(f"Fetched {len(rows)} rows")
            
            if args.config and rows:
                try:
                    crawler.connect_db()
                    crawler.create_kline_table(ktype=args.type)
                    inserted = crawler.insert_rows_with_indicators(rows, ktype=args.type)
                    print(f"Inserted {inserted} rows into DB table kline_data_{args.type}")
                except Exception as e:
                    print(f"DB operation failed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    crawler.disconnect_db()
    
    else:  # historical
        if args.maxTime is None:
            print("Error: --maxTime is required for historical mode")
            exit(1)
        
        data = crawler.fetch_historical(ktype=args.type, max_time_seconds=args.maxTime)
        if data:
            rows = KlineCrawlerEnhanced.parse_data_rows(
                data, ktype=args.type, filter_hour=(args.type == 'hour')
            )
            print(f"Fetched {len(rows)} rows")
            
            if args.config and rows:
                try:
                    crawler.connect_db()
                    crawler.create_kline_table(ktype=args.type)
                    inserted = crawler.insert_rows_with_indicators(rows, ktype=args.type)
                    print(f"Inserted {inserted} rows into DB table kline_data_{args.type}")
                except Exception as e:
                    print(f"DB operation failed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    crawler.disconnect_db()
