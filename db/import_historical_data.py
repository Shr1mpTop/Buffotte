"""
已经可以归档了，完成了历史使命
"""
import requests
import time
from .kline_data_processor import KlineDataProcessor

def fetch_json_data(url: str):
    """
    从给定的 URL 获取 JSON 数据。
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果请求失败，则抛出 HTTPError
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取数据失败 (URL: {url}): {e}")
        return None

def main():
    """
    主函数，用于批量导入历史 K 线数据。
    """
    # 您提供的 URL 列表
    urls = [
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112906514&type=2&maxTime=1757257200",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112966295&type=2&maxTime=1749394800",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112967027&type=2&maxTime=1741532400",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112967915&type=2&maxTime=1733670000",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112968545&type=2&maxTime=1725807600",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112969388&type=2&maxTime=1717945200",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112970010&type=2&maxTime=1710082800",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112970683&type=2&maxTime=1702220400",
        "https://api.steamdt.com/user/statistics/v1/kline?timestamp=1765112971684&type=2&maxTime=1694358000",
    ]

    # 为了按时间顺序导入，我们颠倒列表，从最旧的数据开始处理
    urls.reverse()

    processor = KlineDataProcessor()
    
    print("开始批量导入历史 K 线数据...")

    for i, url in enumerate(urls):
        print(f"--- 处理第 {i + 1}/{len(urls)} 个数据文件 ---")
        print(f"URL: {url}")
        
        raw_data = fetch_json_data(url)
        
        if raw_data:
            processor.process_and_store(raw_data)
        
        # 增加一个小的延迟，避免对 API 造成过大压力
        time.sleep(1)

    print("--- 所有历史数据导入完成！ ---")

if __name__ == "__main__":
    main()
