"""
Data Fetcher Module

Handles fetching and inserting K-line data into the database.
"""
import os
import json
from datetime import datetime, timezone, timedelta
import pandas as pd
from sqlalchemy import create_engine

from src.kline_crawler import KlineCrawler


def fetch_and_insert(db_config_path: str, days: int = 5) -> int:
    """
    Fetch kline data for the previous `days` days at 23:55 (Shanghai time) and insert into DB.

    Args:
        db_config_path: Path to the database configuration file
        days: Number of days to fetch (default: 5)

    Returns:
        Total number of rows inserted
    """
    crawler = KlineCrawler(db_config_path=db_config_path)
    total_inserted = 0

    # Read optional automation config from the same config file
    try:
        with open(db_config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    force_update = bool(cfg.get('force_update', False))
    history_days = int(cfg.get('history_days', days))

    now_ref = datetime.now(timezone.utc)

    try:
        crawler.connect_db()
        crawler.create_kline_table(ktype='day')

        for d in range(1, history_days + 1):
            target_date = (now_ref - timedelta(days=d)).date()
            # Construct 23:55:10 in Shanghai time (UTC+8), then convert to UTC for API
            shanghai_tz = timezone(timedelta(hours=8))
            target_dt_shanghai = datetime(
                target_date.year, target_date.month, target_date.day, 
                23, 55, 10, tzinfo=shanghai_tz
            )
            # API expects UTC timestamp; convert
            ts = int(target_dt_shanghai.astimezone(timezone.utc).timestamp())
            data = crawler.fetch_recent(timestamp_s=ts)
            
            # Write raw API response to logs for auditing
            try:
                os.makedirs('logs', exist_ok=True)
                log_path = os.path.join('logs', f'fetch_{target_date.isoformat()}_{ts}.json')
                with open(log_path, 'w', encoding='utf-8') as lf:
                    json.dump(data, lf, ensure_ascii=False, indent=2)
            except Exception as e:
                print('Failed to write fetch log:', e)
                
            rows = KlineCrawler.parse_data_rows(data) if data else []
            if not rows:
                print(f'No rows returned for {target_date.isoformat()} 23:55:10 Shanghai (ts={ts})')
                continue

            # Filter rows to only include those with Shanghai time 23:55:10
            filtered_rows = []
            for r in rows:
                ts_row = int(r[0])
                dt_utc = datetime.fromtimestamp(ts_row, tz=timezone.utc)
                dt_shanghai = dt_utc + timedelta(hours=8)
                if dt_shanghai.hour == 23 and dt_shanghai.minute == 55 and dt_shanghai.second == 10:
                    filtered_rows.append(r)

            if not filtered_rows:
                print(f'No rows with 23:55:10 Shanghai time for {target_date.isoformat()}')
                continue

            try:
                inserted = crawler.insert_rows(filtered_rows, ktype='day')
                print(f'Inserted {inserted} rows for {target_date.isoformat()} 23:55:10 Shanghai')
                total_inserted += inserted
            except Exception as e:
                print(f'DB insert failed for {target_date.isoformat()}:', e)
                
    except Exception as e:
        print('DB operation failed:', e)
    finally:
        try:
            crawler.disconnect_db()
        except Exception:
            pass

    return total_inserted


def load_recent_data(db_config_path: str, nrows: int = 60) -> pd.DataFrame:
    """
    Load recent kline data from database.

    Priority for DB connection:
    1. If env var BUFFOTTE_DB_URI is set, use it directly as SQLAlchemy engine URI.
    2. Else fall back to reading `db_config_path` JSON.

    Args:
        db_config_path: Path to the database configuration file
        nrows: Number of recent rows to load (default: 60)

    Returns:
        DataFrame with recent kline data
    """
    env_uri = os.getenv('BUFFOTTE_DB_URI')
    
    if env_uri:
        uri = env_uri
    else:
        with open(db_config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        user = cfg.get('user') or cfg.get('username')
        password = cfg.get('password')
        host = cfg.get('host', '127.0.0.1')
        port = cfg.get('port', 3306)
        db = cfg.get('db') or cfg.get('database')
        charset = cfg.get('charset', 'utf8mb4')
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset={charset}"

    engine = create_engine(uri)
    query = f'SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp DESC LIMIT {nrows}'
    df = pd.read_sql(query, engine)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df
