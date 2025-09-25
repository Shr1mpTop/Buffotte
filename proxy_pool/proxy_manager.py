import requests
import warnings
import asyncio
import time
import json

# 抑制SSL警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class ProxyManager:
    def __init__(self):
        self.proxies = []  # 代理列表，每个元素是 {'ip_port': 'ip:port', 'fail_count': 0, 'last_test': 0}
        self.max_fail_count = 1
        self.test_interval = 30  # 30秒测试一次
        self.fetch_interval = 180  # 5分钟获取一次新代理（如果需要）
        self.target_pool_size = 20  # 目标代理池大小
        self.test_url = 'http://httpbin.org/ip'
        self.status_file = 'proxy_pool/proxy_pool_status.json'

    async def fetch_proxies(self, count=20):
        """异步获取代理列表"""
        url = 'https://proxy.scdn.io/api/get_proxy.php'
        params = {
            'protocol': 'https',
            'count': count
        }
        try:
            # 使用asyncio.to_thread运行同步requests
            response = await asyncio.to_thread(requests.get, url, params=params)
            data = response.json()
            if data.get('code') == 200:
                return data['data']['proxies']
        except Exception as e:
            pass
        return []

    async def test_proxy(self, proxy_info):
        """测试单个代理"""
        proxy_str = proxy_info['ip_port']
        try:
            proxies = {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }
            response = await asyncio.to_thread(requests.get, self.test_url, proxies=proxies, timeout=10, verify=False)
            if response.status_code == 200:
                proxy_info['fail_count'] = 0
                proxy_info['last_test'] = time.time()
                return True
        except Exception as e:
            pass
        proxy_info['fail_count'] += 1
        proxy_info['last_test'] = time.time()
        return False

    async def add_new_proxies(self):
        """补充代理到目标池大小"""
        current_size = len(self.proxies)
        needed = max(0, self.target_pool_size - current_size)
        if needed > 0:
            new_proxies = await self.fetch_proxies(count=needed)
            added = 0
            for proxy_str in new_proxies:
                if not any(p['ip_port'] == proxy_str for p in self.proxies):
                    self.proxies.append({'ip_port': proxy_str, 'fail_count': 0, 'last_test': 0})
                    added += 1
            if added > 0:
                print(f"补充了 {added} 个代理")
                self.write_status_to_file()

    async def test_all_proxies(self):
        """测试所有代理，失败则剔除"""
        print(f"开始测试代理池，大小: {len(self.proxies)}")
        tasks = [self.test_proxy(proxy) for proxy in self.proxies]
        await asyncio.gather(*tasks)
        # 移除失败次数过多的代理
        before = len(self.proxies)
        self.proxies = [p for p in self.proxies if p['fail_count'] < self.max_fail_count]
        after = len(self.proxies)
        print(f"测试完成，剩余代理: {after}")
        # 补充代理
        await self.add_new_proxies()
        self.write_status_to_file()

    def get_pool_status(self):
        """获取代理池状态的dict"""
        status = {
            'total_proxies': len(self.proxies),
            'healthy_proxies': len([p for p in self.proxies if p['fail_count'] == 0]),
            'failed_proxies': len([p for p in self.proxies if p['fail_count'] >= self.max_fail_count]),
            'target_pool_size': self.target_pool_size,
            'last_update': time.time(),
            'proxies': [
                {
                    'ip_port': p['ip_port'],
                    'fail_count': p['fail_count'],
                    'last_test': p['last_test']
                } for p in self.proxies
            ]
        }
        return status

    def write_status_to_file(self):
        """将代理池状态写入JSON文件"""
        status = self.get_pool_status()
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)

    async def run(self):
        """主循环"""
        print("启动代理管理器...")
        await self.add_new_proxies()  # 初始加载到目标大小
        while True:
            await self.test_all_proxies()
            await asyncio.sleep(self.test_interval)

async def main():
    manager = ProxyManager()
    try:
        await manager.run()
    except KeyboardInterrupt:
        print("停止代理管理器")

if __name__ == '__main__':
    asyncio.run(main())