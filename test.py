import time
import json
import requests
from typing import Optional

class DailyKlineCrawler:
    TYPE_MAP = {"hour": 1, "day": 2, "week": 3}
    BASE_URL = "https://api.steamdt.com/user/statistics/v1/kline"
    ITEM_DETAILS_URL = "https://api.steamdt.com/user/steam/type-trend/v2/item/details"

    def __init__(self):
        self.session = requests.Session()

    def _build_headers(self, access_token: str = "0de1a71e-2e31-4c4b-afba-24942aeff115") -> dict:
        return {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5",
            "access-token": access_token,
            "content-type": "application/json",
            "language": "zh_CN",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "x-app-version": "1.0.0",
            "x-currency": "CNY",
            "x-device": "1",
            "x-device-id": "07a2f5d6-e3a0-45b3-8cbf-fed3767407da",
        }

    def fetch_item_details(self, item_id: str, platform: str = "BUFF", type_day: str = "1", date_type: int = 3, access_token: str = "0de1a71e-2e31-4c4b-afba-24942aeff115") -> Optional[dict]:
        """抓取物品详情数据（POST 请求），复现 steamdt.com 的 API 调用。"""
        timestamp_ms = str(int(time.time() * 1000))  # 毫秒级时间戳
        params = {"timestamp": timestamp_ms}
        body = {
            "itemId": item_id,
            "platform": platform,
            "typeDay": type_day,
            "dateType": date_type,
            "timestamp": timestamp_ms
        }

        try:
            resp = self.session.post(
                self.ITEM_DETAILS_URL,
                params=params,
                json=body,
                headers=self._build_headers(access_token),
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