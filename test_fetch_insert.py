from datetime import datetime, timezone, timedelta
from kline_crawler import KlineCrawler
from run_daily_report import fetch_and_insert

# Monkeypatch DB methods to avoid touching real DB
KlineCrawler.connect_db = lambda self: None
KlineCrawler.create_kline_table = lambda self, ktype='day': None
KlineCrawler.insert_rows = lambda self, rows, ktype='day': (print("mock insert rows:", len(rows)) or len(rows))
KlineCrawler.disconnect_db = lambda self: None

def make_api_data_for_ts(ts_seconds):
    return {'data': [[int(ts_seconds), 100.0, 101.0, 99.0, 100.5, 1000, 1000.0]]}

def fake_fetch(self, timestamp_s=None, ktype='day', max_time_seconds=None):
    return make_api_data_for_ts(timestamp_s)

KlineCrawler.fetch_recent = fake_fetch

if __name__ == '__main__':
    print('Running simulated fetch_and_insert (1 day)')
    print('Result:', fetch_and_insert('config.json', days=1))
