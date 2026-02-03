import time
import json
import requests
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class DailyKlineCrawler:
    TYPE_MAP = {"hour": 1, "day": 2, "week": 3}
    BASE_URL = "https://api.steamdt.com/user/statistics/v1/kline"

    def __init__(self):
        self.session = requests.Session()

    def _build_headers(self) -> dict:
        # 尝试从环境变量获取 API Key
        access_token = "undefined"
        api_keys = os.getenv('API_KEYS')
        if api_keys:
            access_token = api_keys.split(',')[0].strip()

        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9",
            "access-token": access_token,
            "language": "zh_CN",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "x-app-version": "1.0.0",
            "x-currency": "CNY",
            "x-device": "1",
        }

    def fetch_daily_data(self, timestamp_s: Optional[int] = None) -> Optional[dict]:
        """抓取每日数据（day 类型），并返回原始 JSON。"""
        if timestamp_s is None:
            timestamp_s = int(time.time())
        tnum = self.TYPE_MAP["day"] #所以这里就规定了我们是抓取的每日K线数据
        params = {"timestamp": timestamp_s, "type": tnum}

        try:
            resp = self.session.get(self.BASE_URL, params=params, headers=self._build_headers(), timeout=15)
            resp.raise_for_status()
            raw_data = resp.json()
            print("原始数据：")
            print(json.dumps(raw_data, indent=4, ensure_ascii=False))
            return raw_data
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return None

if __name__ == "__main__":
    crawler = DailyKlineCrawler()
    data = crawler.fetch_daily_data()
    if data:
        print("Success!")
    else:
        print("Failed!")