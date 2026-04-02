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
    ITEM_DETAILS_URL = "https://api.steamdt.com/user/steam/category/v1/kline"

    def __init__(self):
        self.session = requests.Session()
        # 配置代理（如果环境变量中有代理设置）
        self.proxies = {}
        proxy_url = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        if proxy_url:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

    def _build_headers(self, access_token: str = None) -> dict:
        if access_token is None:
            # 尝试从环境变量获取 API Key
            api_keys = os.getenv('API_KEYS')
            if api_keys:
                # 使用第一个key，如果无效则尝试其他
                access_token = "e0cac434-0dc2-40bb-bc79-7d62d9db65df"  # 使用用户提供的有效key
            else:
                # 默认 fallback token
                access_token = "0de1a71e-2e31-4c4b-afba-24942aeff115"

        return {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5",
            "access-token": access_token,
            "content-type": "application/json",
            "language": "zh_CN",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
            "x-app-version": "1.0.0",
            "x-currency": "CNY",
            "x-device": "1",
            "x-device-id": "8a429029-ad08-467c-a457-d4e41ee27c99",  # 使用用户请求中的device-id
        }

    def fetch_item_details(self, item_id: str, platform: str = "ALL", type_day: str = "2", date_type: int = 2, access_token: str = None) -> Optional[dict]:
        """抓取物品详情数据（GET 请求），复现 steamdt.com 的 API 调用。"""
        timestamp_ms = str(int(time.time() * 1000))  # 毫秒级时间戳
        params = {
            "timestamp": timestamp_ms,
            "type": type_day,  # 1=hour, 2=day, 3=week
            "maxTime": "0",  # 0表示获取所有历史数据
            "typeVal": item_id,
            "platform": platform,
            "specialStyle": ""  # 空值
        }

        try:
            resp = self.session.get(
                self.ITEM_DETAILS_URL,
                params=params,
                headers=self._build_headers(access_token),
                proxies=self.proxies,
                timeout=15
            )
            resp.raise_for_status()
            raw_data = resp.json()
            print("物品详情原始数据：")
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
    # 抓取物品详情
    item_id = "22349"
    item_data = crawler.fetch_item_details(item_id)
    if item_data:
        print("物品详情抓取成功!")
    else:
        print("物品详情抓取失败!")