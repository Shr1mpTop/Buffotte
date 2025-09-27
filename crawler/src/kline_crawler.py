import requests
import time
import json
import pymysql


class KlineCrawler:
    def __init__(self, config_path="../api/config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.conn = None
        self.cursor = None

    def connect_db(self):
        self.conn = pymysql.connect(**self.config)
        self.cursor = self.conn.cursor()

    def disconnect_db(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_kline_table(self, kline_type='hour'):
        table_name = f'kline_data_{kline_type}'
        self.cursor.execute(f'''
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
        ''')

    def fetch_kline_data(self, timestamp=None, kline_type='hour', max_time=None):
        type_map = {'hour': 1, 'day': 2, 'week': 3}
        kline_type_num = type_map.get(kline_type, 1)
        
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # 当前时间戳（毫秒）

        url = f"https://api.steamdt.com/user/statistics/v1/kline?timestamp={timestamp}&type={kline_type_num}"
        if max_time:
            url += f"&maxTime={max_time}"

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5",
            "access-token": "undefined",  # 如果有真实 token，需要替换
            "language": "zh_CN",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "x-app-version": "1.0.0",
            "x-currency": "CNY",
            "x-device": "1",
            "x-device-id": "07a2f5d6-e3a0-45b3-8cbf-fed3767407da",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(f"{kline_type} Kline data fetched successfully")

            table_name = f'kline_data_{kline_type}'
            # 假设 data['data'] 是 list of lists
            if "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    if len(item) >= 7:
                        ts, open_p, high_p, low_p, close_p, vol, turn = item[:7]
                        self.cursor.execute(
                            f"""
                        INSERT IGNORE INTO {table_name} (timestamp, open_price, high_price, low_price, close_price, volume, turnover)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                            (int(ts), open_p, high_p, low_p, close_p, int(vol), turn),
                        )
                self.conn.commit()
                print(f"Inserted {len(data['data'])} records into {table_name}")
            else:
                print("Unexpected data format")
                print(json.dumps(data, indent=4, ensure_ascii=False))

            return data
        else:
            print(f"Failed to fetch {kline_type} data: {response.status_code}")
            return None

    def run(self):
        self.connect_db()
        for kline_type in ['hour', 'day', 'week']:
            self.create_kline_table(kline_type)
            self.fetch_kline_data(kline_type=kline_type)
        self.disconnect_db()


if __name__ == "__main__":
    crawler = KlineCrawler()
    crawler.run()
