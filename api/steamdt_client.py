"""
SteamDT API 客户端
用于获取CS2饰品价格数据
"""
import asyncio
import json
import time
import os
from typing import List, Dict, Any, Optional
import httpx
import pymysql

# SteamDT API配置
STEAMDT_BASE_URL = 'https://open.steamdt.com'
API_KEY = '5036288716b24b36963ef12593226613'

# 请求头
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'Buffotte/1.0'
}


class SteamDTClient:
    """SteamDT API客户端"""

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.client = None
        self.base_items = []  # 存储基础信息
        self.last_base_update = 0  # 最后更新基础信息的时间
        self.db_config = db_config or {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', 3306)),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', '123456'),
            'database': os.environ.get('DB_DATABASE', 'buffotte'),
            'charset': 'utf8mb4'
        }
        self.api_limits = {}  # 存储API限制信息
        self.call_history = {}  # 存储调用历史

    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)

    async def load_api_limits(self):
        """从数据库加载API限制信息"""
        if self.api_limits:
            return  # 已加载

        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT endpoint, limit_per_hour, limit_per_minute, limit_per_day FROM steamdt_api_limits')
                results = cursor.fetchall()

                for row in results:
                    endpoint, per_hour, per_minute, per_day = row
                    self.api_limits[endpoint] = {
                        'per_hour': per_hour,
                        'per_minute': per_minute,
                        'per_day': per_day
                    }

            conn.close()
            print(f'已加载 {len(self.api_limits)} 个API限制规则')

        except Exception as e:
            print(f'加载API限制失败: {e}')

    async def check_rate_limit(self, endpoint: str) -> bool:
        """检查API调用是否超过限制"""
        await self.load_api_limits()

        if endpoint not in self.api_limits:
            return True  # 没有限制信息，允许调用

        limits = self.api_limits[endpoint]
        current_time = time.time()

        # 初始化调用历史
        if endpoint not in self.call_history:
            self.call_history[endpoint] = []

        # 清理过期记录（超过1小时的记录）
        self.call_history[endpoint] = [
            call_time for call_time in self.call_history[endpoint]
            if current_time - call_time < 3600
        ]

        calls_last_hour = len(self.call_history[endpoint])
        calls_last_minute = len([t for t in self.call_history[endpoint] if current_time - t < 60])

        # 检查限制
        if limits['per_hour'] and calls_last_hour >= limits['per_hour']:
            print(f'API {endpoint} 超过每小时限制 ({calls_last_hour}/{limits["per_hour"]})')
            return False

        if limits['per_minute'] and calls_last_minute >= limits['per_minute']:
            print(f'API {endpoint} 超过每分钟限制 ({calls_last_minute}/{limits["per_minute"]})')
            return False

        # 对于每日限制，我们需要从数据库检查
        if limits['per_day']:
            try:
                conn = self.get_db_connection()
                with conn.cursor() as cursor:
                    # 检查今天的使用次数
                    cursor.execute('''
                        SELECT COUNT(*) FROM steamdt_api_calls
                        WHERE endpoint = %s AND DATE(created_at) = CURDATE()
                    ''', (endpoint,))
                    today_calls = cursor.fetchone()[0]

                    if today_calls >= limits['per_day']:
                        print(f'API {endpoint} 超过每日限制 ({today_calls}/{limits["per_day"]})')
                        conn.close()
                        return False

                conn.close()
            except Exception as e:
                print(f'检查每日限制失败: {e}')

        return True

    async def record_api_call(self, endpoint: str):
        """记录API调用"""
        current_time = time.time()
        self.call_history[endpoint].append(current_time)

        # 记录到数据库
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO steamdt_api_calls (endpoint, created_at)
                    VALUES (%s, NOW())
                ''', (endpoint,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f'记录API调用失败: {e}')

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=STEAMDT_BASE_URL,
            headers=HEADERS,
            timeout=30.0
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """统一的请求方法"""
        # 检查频率限制
        if not await self.check_rate_limit(endpoint):
            print(f'API {endpoint} 频率限制，跳过调用')
            return None

        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            data = response.json()
            if not data.get('success', False):
                print(f'API请求失败: {data.get("errorMsg", "未知错误")}')
                return None

            # 记录成功调用
            await self.record_api_call(endpoint)
            return data.get('data')

        except Exception as e:
            print(f'请求异常: {e}')
            return None

    async def get_base_items(self, force_update: bool = False) -> List[Dict[str, Any]]:
        """获取饰品基础信息（每天只能调用一次）"""
        current_time = time.time()

        # 如果不是强制更新，且距离上次更新不到24小时，使用缓存
        if not force_update and self.base_items and (current_time - self.last_base_update) < 24 * 3600:
            print(f'使用缓存的基础信息，共 {len(self.base_items)} 个饰品')
            return self.base_items

        # 检查本地文件缓存
        if os.path.exists('steamdt_base_items.json'):
            try:
                with open('steamdt_base_items.json', 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cached_time = cache_data.get('update_time', 0)

                    # 如果缓存文件在24小时内，使用缓存
                    if current_time - cached_time < 24 * 3600:
                        self.base_items = cache_data.get('items', [])
                        self.last_base_update = cached_time
                        print(f'使用本地文件缓存的基础信息，共 {len(self.base_items)} 个饰品')
                        return self.base_items
            except Exception as e:
                print(f'读取缓存文件失败: {e}')

        print('获取饰品基础信息...')
        data = await self._make_request('GET', '/open/cs2/v1/base')

        if data:
            self.base_items = data
            self.last_base_update = current_time
            print(f'成功获取 {len(self.base_items)} 个饰品的基础信息')

            # 保存到本地文件作为备份
            try:
                with open('steamdt_base_items.json', 'w', encoding='utf-8') as f:
                    json.dump({
                        'items': self.base_items,
                        'update_time': self.last_base_update
                    }, f, ensure_ascii=False, indent=2)
                print('基础信息已保存到本地文件')
            except Exception as e:
                print(f'保存基础信息失败: {e}')
        else:
            print('获取基础信息失败，可能是达到每日限制')

        return self.base_items or []

    async def get_item_prices_batch(self, market_hash_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """批量获取饰品价格"""
        if not market_hash_names:
            return {}

        # 由于批量API每分钟只能调用1次，我们需要等待
        print(f'准备批量查询 {len(market_hash_names)} 个饰品的价格')

        # 一次性查询所有饰品（API限制每分钟1次）
        payload = {
            'marketHashNames': market_hash_names
        }

        print('发送批量价格查询请求...')
        data = await self._make_request('POST', '/open/cs2/v1/price/batch', json=payload)

        all_prices = {}
        if data:
            for item in data:
                market_hash_name = item.get('marketHashName', '')
                if market_hash_name:
                    all_prices[market_hash_name] = item.get('dataList', [])

        print(f'批量查询完成，获取到 {len(all_prices)} 个饰品的价格数据')
        return all_prices

    async def get_all_prices(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有饰品的价格"""
        # 先获取基础信息
        base_items = await self.get_base_items()

        if not base_items:
            print('无法获取基础信息')
            return {}

        # 提取所有marketHashName
        market_hash_names = [item.get('marketHashName', '') for item in base_items if item.get('marketHashName')]

        print(f'开始获取 {len(market_hash_names)} 个饰品的价格')
        return await self.get_item_prices_batch(market_hash_names)


async def test_api():
    """测试API连接"""
    async with SteamDTClient() as client:
        print('测试获取基础信息...')
        base_items = await client.get_base_items()
        print(f'获取到 {len(base_items)} 个基础饰品')

        if base_items:
            # 测试获取前5个饰品的价格
            test_names = [item['marketHashName'] for item in base_items[:5] if item.get('marketHashName')]
            print(f'测试获取 {len(test_names)} 个饰品的价格...')
            prices = await client.get_item_prices_batch(test_names)

            for name, price_data in prices.items():
                print(f'{name}: {len(price_data)} 个平台的价格数据')


if __name__ == '__main__':
    asyncio.run(test_api())