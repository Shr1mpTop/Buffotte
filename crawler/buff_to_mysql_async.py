import argparse
import asyncio
import aiofiles
import json
import os
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import math

import httpx

try:
    import pymysql
except Exception:
    pymysql = None


@dataclass
class ProxyInfo:
    """代理信息类"""
    url: str
    success_count: int = 0
    error_count: int = 0
    last_used: float = 0.0
    is_healthy: bool = True
    last_health_check: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 1.0
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0


class ProxyPool:
    """代理池管理器"""
    
    def __init__(self, proxy_list: List[str], health_check_interval: float = 300.0):
        self.proxies = {url: ProxyInfo(url) for url in proxy_list}
        self.health_check_interval = health_check_interval
        self._lock = asyncio.Lock()
        self._last_proxy_index = 0
        print(f'代理池初始化完成，共 {len(self.proxies)} 个代理')
    
    async def get_proxy(self) -> Optional[str]:
        """获取一个健康的代理"""
        async with self._lock:
            healthy_proxies = [p for p in self.proxies.values() if p.is_healthy]
            if not healthy_proxies:
                print('警告: 没有可用的健康代理，返回None')
                return None
            
            # 按成功率和响应时间排序，选择最佳代理
            healthy_proxies.sort(key=lambda p: (-p.success_rate, p.avg_response_time))
            selected = healthy_proxies[0]
            selected.last_used = time.time()
            return selected.url
    
    async def record_success(self, proxy_url: str, response_time: float):
        """记录代理成功"""
        if proxy_url in self.proxies:
            proxy = self.proxies[proxy_url]
            proxy.success_count += 1
            proxy.response_times.append(response_time)
            # 只保留最近20次响应时间
            if len(proxy.response_times) > 20:
                proxy.response_times = proxy.response_times[-20:]
    
    async def record_error(self, proxy_url: str, error_type: str = "unknown"):
        """记录代理错误"""
        if proxy_url in self.proxies:
            proxy = self.proxies[proxy_url]
            proxy.error_count += 1
            
            # 如果错误率过高，标记为不健康
            if proxy.success_rate < 0.3 and proxy.error_count > 5:
                proxy.is_healthy = False
                print(f'代理 {proxy_url} 被标记为不健康 (成功率: {proxy.success_rate:.2%})')
    
    async def health_check(self, test_url: str = 'https://httpbin.org/ip'):
        """健康检查所有代理"""
        print('开始代理健康检查...')
        for proxy_url, proxy_info in self.proxies.items():
            try:
                start_time = time.time()
                async with httpx.AsyncClient(proxies=proxy_url, timeout=10.0) as client:
                    response = await client.get(test_url)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        proxy_info.is_healthy = True
                        proxy_info.last_health_check = time.time()
                        await self.record_success(proxy_url, response_time)
                        print(f'代理 {proxy_url} 健康检查通过 ({response_time:.2f}s)')
                    else:
                        proxy_info.is_healthy = False
                        await self.record_error(proxy_url, f"status_{response.status_code}")
            except Exception as e:
                proxy_info.is_healthy = False
                await self.record_error(proxy_url, str(e))
                print(f'代理 {proxy_url} 健康检查失败: {e}')
    
    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        healthy_count = sum(1 for p in self.proxies.values() if p.is_healthy)
        total_success = sum(p.success_count for p in self.proxies.values())
        total_errors = sum(p.error_count for p in self.proxies.values())
        
        return {
            'total_proxies': len(self.proxies),
            'healthy_proxies': healthy_count,
            'total_requests': total_success + total_errors,
            'total_success': total_success,
            'total_errors': total_errors,
            'overall_success_rate': total_success / (total_success + total_errors) if (total_success + total_errors) > 0 else 0
        }


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    initial_concurrency: int = 6
    min_concurrency: int = 1
    max_concurrency: int = 20
    backoff_factor: float = 0.7  # 遇到429时并发数乘以这个因子
    recovery_factor: float = 1.1  # 成功时并发数乘以这个因子
    max_delay: float = 60.0  # 最大延迟秒数
    recovery_threshold: int = 10  # 连续成功多少次后尝试恢复并发数


class IntelligentRateLimiter:
    """智能速率限制器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.current_concurrency = config.initial_concurrency
        self.current_delay = 0.0
        self.consecutive_success = 0
        self.consecutive_errors = 0
        self.rate_limit_count = 0
        self._lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(self.current_concurrency)
        self.stats = defaultdict(int)
        
        print(f'智能速率限制器初始化: 初始并发数={self.current_concurrency}')
    
    async def acquire(self):
        """获取信号量"""
        await self.semaphore.acquire()
        if self.current_delay > 0:
            await asyncio.sleep(self.current_delay)
    
    def release(self):
        """释放信号量"""
        self.semaphore.release()
    
    async def record_success(self):
        """记录成功请求"""
        async with self._lock:
            self.consecutive_success += 1
            self.consecutive_errors = 0
            self.stats['success'] += 1
            
            # 连续成功达到阈值，尝试恢复并发数
            if (self.consecutive_success >= self.config.recovery_threshold and 
                self.current_concurrency < self.config.max_concurrency):
                
                old_concurrency = self.current_concurrency
                self.current_concurrency = min(
                    math.ceil(self.current_concurrency * self.config.recovery_factor),
                    self.config.max_concurrency
                )
                
                if self.current_concurrency != old_concurrency:
                    # 重新创建信号量
                    self.semaphore = asyncio.Semaphore(self.current_concurrency)
                    self.consecutive_success = 0
                    print(f'速率限制恢复: 并发数 {old_concurrency} -> {self.current_concurrency}')
            
            # 逐渐减少延迟
            if self.current_delay > 0:
                self.current_delay = max(0, self.current_delay * 0.9)
    
    async def record_rate_limit(self):
        """记录429速率限制"""
        async with self._lock:
            self.consecutive_errors += 1
            self.consecutive_success = 0
            self.rate_limit_count += 1
            self.stats['rate_limit'] += 1
            
            # 降低并发数
            old_concurrency = self.current_concurrency
            self.current_concurrency = max(
                math.ceil(self.current_concurrency * self.config.backoff_factor),
                self.config.min_concurrency
            )
            
            # 增加延迟
            self.current_delay = min(
                self.current_delay + random.uniform(1, 3) * self.consecutive_errors,
                self.config.max_delay
            )
            
            if self.current_concurrency != old_concurrency:
                # 重新创建信号量
                self.semaphore = asyncio.Semaphore(self.current_concurrency)
                print(f'遇到429限制: 并发数 {old_concurrency} -> {self.current_concurrency}, 延迟 {self.current_delay:.1f}s')
    
    async def record_error(self, error_type: str = "unknown"):
        """记录其他错误"""
        async with self._lock:
            self.consecutive_errors += 1
            self.consecutive_success = 0
            self.stats[f'error_{error_type}'] += 1
            
            # 如果连续错误过多，也降低并发数
            if self.consecutive_errors >= 5:
                old_concurrency = self.current_concurrency
                self.current_concurrency = max(
                    self.current_concurrency - 1,
                    self.config.min_concurrency
                )
                if self.current_concurrency != old_concurrency:
                    self.semaphore = asyncio.Semaphore(self.current_concurrency)
                    print(f'连续错误过多: 并发数 {old_concurrency} -> {self.current_concurrency}')
                
                self.consecutive_errors = 0
    
    def get_stats(self) -> Dict:
        """获取速率限制统计"""
        total_requests = sum(self.stats.values())
        return {
            'current_concurrency': self.current_concurrency,
            'current_delay': self.current_delay,
            'rate_limit_hits': self.rate_limit_count,
            'total_requests': total_requests,
            'success_rate': self.stats['success'] / total_requests if total_requests > 0 else 0,
            'stats': dict(self.stats)
        }


API_URL = 'https://buff.163.com/api/market/goods'
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Referer': 'https://buff.163.com/market/csgo',
}

# === 配置区（默认写死）
CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'buffotte',
    'table': 'items',
    'start_page': 1,
    'concurrency': 6,
    'threads': 5,  # 线程数，每个线程负责一部分页面
    # 如果需要登录请在此处指定 cookie 文件路径（每行 k=v）
    'cookie_file': './cookies/cookies.txt',
    # 如果不想写入数据库，设置为 True
    'no_db': False,
    # 可选：代理文件，每行一个 proxy URL
    'proxy_file': None,
}


async def load_cookie_file(path: str) -> Dict[str, str]:
    cookies = {}
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        async for line in f:
            line=line.strip()
            if not line or '=' not in line:
                continue
            k,v = line.split('=',1)
            cookies[k.strip()]=v.strip()
    return cookies


async def load_proxy_file(path: str) -> List[str]:
    proxies = []
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        async for line in f:
            line=line.strip()
            if line:
                proxies.append(line)
    return proxies


async def fetch_page(client: httpx.AsyncClient, page: int, max_retries: int = 3, 
                    thread_id: int = None, proxy_pool: ProxyPool = None, 
                    rate_limiter: IntelligentRateLimiter = None) -> List[Dict[str, Any]]:
    """获取单页数据，支持代理池和智能速率限制"""
    for attempt in range(1, max_retries + 1):
        proxy_url = None
        if rate_limiter:
            await rate_limiter.acquire()
        
        try:
            # 获取代理
            if proxy_pool:
                proxy_url = await proxy_pool.get_proxy()
                if proxy_url:
                    # 为这次请求设置代理
                    client._mounts.clear()
                    client._proxies = {"http://": proxy_url, "https://": proxy_url}
            
            params = {'game': 'csgo', 'page_num': str(page), 'use_suggestion': '0'}
            
            start_time = time.time()
            r = await client.get(API_URL, params=params, timeout=30.0)
            response_time = time.time() - start_time
            
            r.raise_for_status()
            j = r.json()
            
            if j.get('code') != 'OK':
                msg = j.get('msg')
                if isinstance(msg, str) and 'Login Required' in msg:
                    if rate_limiter:
                        await rate_limiter.record_error("login_required")
                    raise PermissionError('Login Required')
                
                print(f'[线程-{thread_id}] 第 {page} 页API返回错误: {j.get("code")} {msg}')
                if rate_limiter:
                    await rate_limiter.record_error("api_error")
                raise RuntimeError(f"API 返回非 OK: {j.get('code')} {msg}")
            
            # 记录成功
            if proxy_pool and proxy_url:
                await proxy_pool.record_success(proxy_url, response_time)
            if rate_limiter:
                await rate_limiter.record_success()
            
            # 某些情况下 API 可能返回 "items": null，确保返回空列表而不是 None
            items = j.get('data', {}).get('items')
            result = items or []
            print(f'[线程-{thread_id}] 获取第 {page} 页数据成功，包含 {len(result)} 件物品 (耗时: {response_time:.2f}s)')
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f'[线程-{thread_id}] 第 {page} 页遇到429速率限制 (尝试 {attempt}/{max_retries})')
                if proxy_pool and proxy_url:
                    await proxy_pool.record_error(proxy_url, "rate_limit")
                if rate_limiter:
                    await rate_limiter.record_rate_limit()
                
                # 429错误时使用指数退避
                wait_time = 1 + 2**attempt + random.random()
                print(f'[线程-{thread_id}] 等待 {wait_time:.1f} 秒后重试...')
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f'[线程-{thread_id}] 第 {page} 页HTTP错误: {e.response.status_code}')
                if proxy_pool and proxy_url:
                    await proxy_pool.record_error(proxy_url, f"http_{e.response.status_code}")
                if rate_limiter:
                    await rate_limiter.record_error(f"http_{e.response.status_code}")
                raise
                
        except Exception as e:
            error_type = type(e).__name__
            print(f'[线程-{thread_id}] 第 {page} 页请求异常: {e} (尝试 {attempt}/{max_retries})')
            
            if proxy_pool and proxy_url:
                await proxy_pool.record_error(proxy_url, error_type)
            if rate_limiter:
                await rate_limiter.record_error(error_type)
            
            if attempt < max_retries:
                wait_time = 0.5 + attempt + random.random()
                await asyncio.sleep(wait_time)
                continue
            raise
        finally:
            if rate_limiter:
                rate_limiter.release()
    
    # 如果所有重试都失败了
    print(f'[线程-{thread_id}] 第 {page} 页获取失败，已重试 {max_retries} 次')
    return []


async def writer_loop(queue: asyncio.Queue, db_conf, table: str, enable_price_history: bool = True):
    if pymysql is None:
        print('未安装 pymysql，写入数据库不可用')
        return
    try:
        conn = pymysql.connect(host=db_conf['host'], port=db_conf['port'], user=db_conf['user'], password=db_conf['password'], charset='utf8mb4', autocommit=False)
    except Exception as e:
        print('无法连接到 MySQL，writer 线程退出:', e)
        return
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;" % db_conf['database'])
    conn.select_db(db_conf['database'])
    
    # 创建主表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS `%s` (
      `id` BIGINT PRIMARY KEY,
      `appid` INT,
      `game` VARCHAR(50),
      `name` TEXT,
      `market_hash_name` TEXT,
      `steam_market_url` TEXT,
      `sell_reference_price` DECIMAL(16,6),
      `sell_min_price` DECIMAL(16,6),
      `buy_max_price` DECIMAL(16,6),
      `sell_num` INT,
      `buy_num` INT,
      `transacted_num` INT,
      `goods_info` JSON,
      `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """ % table)
    
    # 创建价格历史表
    if enable_price_history:
        price_history_table = f"{table}_price_history"
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{price_history_table}` (
          `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
          `item_id` BIGINT NOT NULL,
          `sell_reference_price` DECIMAL(16,6),
          `sell_min_price` DECIMAL(16,6),
          `buy_max_price` DECIMAL(16,6),
          `sell_num` INT,
          `buy_num` INT,
          `transacted_num` INT,
          `recorded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_item_time` (`item_id`, `recorded_at`),
          INDEX `idx_recorded_at` (`recorded_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print(f'价格历史表 {price_history_table} 已准备就绪')

    insert_sql = (
        "INSERT INTO `{table}` (`id`,`appid`,`game`,`name`,`market_hash_name`,`steam_market_url`,`sell_reference_price`,`sell_min_price`,`buy_max_price`,`sell_num`,`buy_num`,`transacted_num`,`goods_info`) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE `appid`=VALUES(`appid`), `game`=VALUES(`game`), `name`=VALUES(`name`), `market_hash_name`=VALUES(`market_hash_name`), `steam_market_url`=VALUES(`steam_market_url`), `sell_reference_price`=VALUES(`sell_reference_price`), `sell_min_price`=VALUES(`sell_min_price`), `buy_max_price`=VALUES(`buy_max_price`), `sell_num`=VALUES(`sell_num`), `buy_num`=VALUES(`buy_num`), `transacted_num`=VALUES(`transacted_num`), `goods_info`=VALUES(`goods_info`)"
    ).format(table=table)
    
    # 价格历史表插入SQL
    price_history_sql = None
    if enable_price_history:
        price_history_sql = f"""
        INSERT INTO `{price_history_table}` 
        (`item_id`, `sell_reference_price`, `sell_min_price`, `buy_max_price`, `sell_num`, `buy_num`, `transacted_num`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

    batch = []
    price_history_batch = []
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            goods_json = json.dumps(item.get('goods_info') or {}, ensure_ascii=False)
            item_id = int(item.get('id'))
            
            # 主表数据
            main_tuple = (item_id, int(item.get('appid') or 0), item.get('game'), item.get('name'), item.get('market_hash_name'), item.get('steam_market_url'), float(item.get('sell_reference_price') or 0), float(item.get('sell_min_price') or 0), float(item.get('buy_max_price') or 0), int(item.get('sell_num') or 0), int(item.get('buy_num') or 0), int(item.get('transacted_num') or 0), goods_json)
            batch.append(main_tuple)
            
            # 价格历史数据
            if enable_price_history:
                price_tuple = (item_id, float(item.get('sell_reference_price') or 0), float(item.get('sell_min_price') or 0), float(item.get('buy_max_price') or 0), int(item.get('sell_num') or 0), int(item.get('buy_num') or 0), int(item.get('transacted_num') or 0))
                price_history_batch.append(price_tuple)
            
            if len(batch) >= 200:
                try:
                    # 写入主表
                    cur.executemany(insert_sql, batch)
                    
                    # 写入价格历史表
                    if enable_price_history and price_history_batch:
                        cur.executemany(price_history_sql, price_history_batch)
                    
                    conn.commit()
                    print(f'writer: 写入 {len(batch)} 条记录' + (f'，{len(price_history_batch)} 条价格历史' if enable_price_history else ''))
                except Exception as e:
                    print('writer 写入错误', e)
                    conn.rollback()
                batch = []
                price_history_batch = []
                
        # 处理剩余数据
        if batch:
            try:
                cur.executemany(insert_sql, batch)
                if enable_price_history and price_history_batch:
                    cur.executemany(price_history_sql, price_history_batch)
                conn.commit()
                print(f'writer: 写入剩余 {len(batch)} 条记录' + (f'，{len(price_history_batch)} 条价格历史' if enable_price_history else ''))
            except Exception as e:
                print('writer 写入剩余数据错误', e)
                conn.rollback()
    finally:
        cur.close()
        conn.close()


# 线程安全的数据队列管理器
class ThreadSafeDataManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._data_buffer = []
        self._db_queue = None
    
    def set_db_queue(self, queue):
        self._db_queue = queue
    
    async def add_items(self, items):
        """添加爬取到的数据"""
        if self._db_queue:
            for item in items:
                await self._db_queue.put(item)
    
    def add_items_sync(self, items):
        """线程安全的同步添加方法"""
        with self._lock:
            self._data_buffer.extend(items)
    
    async def flush_buffer(self):
        """将缓冲区数据刷新到异步队列"""
        with self._lock:
            if self._data_buffer and self._db_queue:
                for item in self._data_buffer:
                    await self._db_queue.put(item)
                count = len(self._data_buffer)
                self._data_buffer.clear()
                return count
        return 0


async def crawl_pages_range(thread_id: int, start_page: int, end_page: int, config: dict, 
                           cookies: dict, proxies: list, data_manager: ThreadSafeDataManager,
                           proxy_pool: ProxyPool = None, rate_limiter: IntelligentRateLimiter = None):
    """单个线程的异步爬取函数，负责指定范围的页面，支持代理池和智能速率限制"""
    print(f'线程 {thread_id}: 开始爬取页面 {start_page}-{end_page}')
    
    # 每个线程使用独立的HTTP客户端
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    
    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        # 使用速率限制器的并发数，否则使用配置的并发数
        concurrency = rate_limiter.current_concurrency if rate_limiter else config.get('concurrency', 6)
        sem = asyncio.Semaphore(concurrency)
        
        async def worker(page: int):
            async with sem:
                try:
                    # 使用新的fetch_page函数，支持代理池和速率限制
                    items = await fetch_page(client, page, 3, thread_id, proxy_pool, rate_limiter)
                except PermissionError:
                    print(f'线程 {thread_id} - page {page}: Login Required - 跳过')
                    return
                except Exception as e:
                    print(f'线程 {thread_id} - page {page}: 错误 {e}')
                    return
                
                # 保护性检查：如果 items 为空或为 None，跳过
                if not items:
                    print(f'线程 {thread_id} - page {page}: no items, skip')
                    return
                
                # 使用数据管理器添加数据
                await data_manager.add_items(items)
                print(f'线程 {thread_id} - page {page}: 获取到 {len(items)} 条记录')
        
        # 创建所有页面的任务
        tasks = []
        for page in range(start_page, end_page + 1):
            tasks.append(asyncio.create_task(worker(page)))
            # stagger start a bit to avoid一波并发发送
            await asyncio.sleep(random.uniform(0.01, 0.2))
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f'线程 {thread_id}: 完成爬取页面 {start_page}-{end_page}')


def run_crawler_thread(thread_id: int, start_page: int, end_page: int, config: dict, 
                      cookies: dict, proxies: list, data_manager: ThreadSafeDataManager,
                      proxy_pool: ProxyPool = None, rate_limiter: IntelligentRateLimiter = None):
    """在线程中运行异步爬虫的包装函数"""
    # 为每个线程创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            crawl_pages_range(thread_id, start_page, end_page, config, cookies, proxies, 
                            data_manager, proxy_pool, rate_limiter)
        )
    finally:
        loop.close()


async def load_config_json(config_path: str = './config.json') -> Dict[str, Any]:
    """加载config.json配置文件"""
    try:
        if os.path.exists(config_path):
            async with aiofiles.open(config_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                config = json.loads(content)
                print(f'已加载配置文件: {config_path}')
                return config
    except Exception as e:
        print(f'加载配置文件失败: {e}')
    return {}


async def main_async():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, help='总共要爬取的页面数')
    parser.add_argument('--threads', type=int, help='爬虫线程数，每个线程负责一部分页面')
    parser.add_argument('--config', type=str, default='./config.json', help='配置文件路径')
    args = parser.parse_args()

    # 首先加载config.json配置
    json_config = await load_config_json(args.config)
    
    # 从环境变量读取配置（环境变量优先于config.json）
    def env_bool(name, json_key=None, default=False):
        v = os.environ.get(name)
        if v is None:
            return json_config.get(json_key, default) if json_key else default
        return str(v).lower() in ('1', 'true', 'yes', 'on')

    def env_int(name, json_key=None, default=0):
        v = os.environ.get(name)
        try:
            if v is not None:
                return int(v)
            elif json_key and json_key in json_config:
                return int(json_config[json_key])
            else:
                return int(default)
        except Exception:
            return int(default)

    def env_str(name, json_key=None, default=None):
        v = os.environ.get(name)
        if v is not None:
            return v
        elif json_key and json_key in json_config:
            return json_config[json_key]
        else:
            return default

    # 配置优先级：命令行参数 > 环境变量 > config.json > 默认值
    CONFIG = {
        'host': env_str('BUFF_DB_HOST', None, json_config.get('db', {}).get('host', 'localhost')),
        'port': env_int('BUFF_DB_PORT', None, json_config.get('db', {}).get('port', 3306)),
        'user': env_str('BUFF_DB_USER', None, json_config.get('db', {}).get('user', 'root')),
        'password': env_str('BUFF_DB_PASSWORD', None, json_config.get('db', {}).get('password', '123456')),
        'database': env_str('BUFF_DB_DATABASE', None, json_config.get('db', {}).get('database', 'buffotte')),
        'table': env_str('BUFF_DB_TABLE', None, json_config.get('db', {}).get('table', 'items')),
        'start_page': env_int('BUFF_START_PAGE', 'start_page', 1),
        'concurrency': env_int('BUFF_CONCURRENCY', 'concurrency', 6),
        'threads': env_int('BUFF_THREADS', 'threads', 5),
        'cookie_file': env_str('BUFF_COOKIE_FILE', 'cookie_file', './cookies/cookies.txt'),
        'no_db': env_bool('BUFF_NO_DB', 'no_db', False),
        'proxy_file': env_str('BUFF_PROXY_FILE', 'proxy_file', None),
        'max_pages': env_int('BUFF_MAX_PAGES', 'max_pages', 2000),
        'enable_price_history': env_bool('BUFF_ENABLE_PRICE_HISTORY', 'enable_price_history', True),
        # 新增代理池和速率限制配置
        'enable_proxy_pool': env_bool('BUFF_ENABLE_PROXY_POOL', 'enable_proxy_pool', False),
        'enable_rate_limiting': env_bool('BUFF_ENABLE_RATE_LIMITING', 'enable_rate_limiting', True),
        'initial_concurrency': env_int('BUFF_INITIAL_CONCURRENCY', 'initial_concurrency', 6),
        'min_concurrency': env_int('BUFF_MIN_CONCURRENCY', 'min_concurrency', 1),
        'max_concurrency': env_int('BUFF_MAX_CONCURRENCY', 'max_concurrency', 20),
        'proxy_health_check_interval': env_int('BUFF_PROXY_HEALTH_CHECK_INTERVAL', 'proxy_health_check_interval', 300),
    }

    # 从命令行参数覆盖配置（最高优先级，仅当用户明确指定时）
    if args.threads is not None:
        CONFIG['threads'] = args.threads
    if args.max_pages is not None:
        CONFIG['max_pages'] = args.max_pages

    # 从 CONFIG 读取 cookie/proxy
    cookies = {}
    if CONFIG.get('cookie_file'):
        cookies = await load_cookie_file(CONFIG.get('cookie_file'))

    proxies = []
    if CONFIG.get('proxy_file'):
        proxies = await load_proxy_file(CONFIG.get('proxy_file'))

    db_conf = {'host': CONFIG.get('host'), 'port': CONFIG.get('port'), 'user': CONFIG.get('user'), 
               'password': CONFIG.get('password'), 'database': CONFIG.get('database')}

    # 创建线程安全的数据管理器
    data_manager = ThreadSafeDataManager()
    
    # 初始化代理池（如果启用且有代理文件）
    proxy_pool = None
    if CONFIG.get('enable_proxy_pool') and proxies:
        proxy_pool = ProxyPool(proxies, CONFIG.get('proxy_health_check_interval', 300))
        # 执行初始健康检查
        await proxy_pool.health_check()
        print(f'代理池状态: {proxy_pool.get_stats()}')
    elif CONFIG.get('enable_proxy_pool'):
        print('警告: 启用了代理池但没有提供代理文件，将不使用代理池')
    
    # 初始化智能速率限制器（如果启用）
    rate_limiter = None
    if CONFIG.get('enable_rate_limiting'):
        rate_limit_config = RateLimitConfig(
            initial_concurrency=CONFIG.get('initial_concurrency', 6),
            min_concurrency=CONFIG.get('min_concurrency', 1),
            max_concurrency=CONFIG.get('max_concurrency', 20)
        )
        rate_limiter = IntelligentRateLimiter(rate_limit_config)
        print(f'智能速率限制器已启用，初始并发数: {rate_limiter.current_concurrency}')
    
    # 创建异步队列用于数据库写入
    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
    data_manager.set_db_queue(queue)

    # writer (可选)
    writer_task = None
    if not CONFIG.get('no_db'):
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table'), CONFIG.get('enable_price_history', True)))

    # 计算页面分配
    max_pages = CONFIG.get('max_pages')
    start_page = CONFIG.get('start_page')
    end_page = start_page + max_pages - 1
    threads_count = CONFIG.get('threads')
    
    # 将页面平均分配给各个线程
    pages_per_thread = max_pages // threads_count
    remaining_pages = max_pages % threads_count
    
    print(f'开始多线程爬取: {threads_count} 个线程，总共 {max_pages} 页 (页面 {start_page}-{end_page})')
    print(f'配置来源: config.json (max_pages={json_config.get("max_pages", "未设置")})')
    if args.max_pages is not None:
        print(f'命令行覆盖: --max-pages {args.max_pages}')
    if args.threads is not None:
        print(f'命令行覆盖: --threads {args.threads}')
    
    # 创建线程池并分配任务
    with ThreadPoolExecutor(max_workers=threads_count) as executor:
        futures = []
        current_start = start_page
        
        for thread_id in range(threads_count):
            # 计算当前线程负责的页面范围
            current_pages = pages_per_thread + (1 if thread_id < remaining_pages else 0)
            current_end = current_start + current_pages - 1
            
            print(f'线程 {thread_id + 1}: 负责页面 {current_start}-{current_end} (共 {current_pages} 页)')
            
            # 提交线程任务
            future = executor.submit(
                run_crawler_thread, 
                thread_id + 1, 
                current_start, 
                current_end, 
                CONFIG, 
                cookies, 
                proxies, 
                data_manager,
                proxy_pool,
                rate_limiter
            )
            futures.append(future)
            
            current_start = current_end + 1
        
        # 等待所有线程完成
        completed_threads = 0
        for future in as_completed(futures):
            try:
                future.result()  # 获取结果，如果有异常会抛出
                completed_threads += 1
                print(f'已完成 {completed_threads}/{threads_count} 个线程')
            except Exception as e:
                print(f'线程执行出错: {e}')
                completed_threads += 1

    print('所有爬取线程已完成')
    
    # 输出代理池和速率限制器的统计信息
    if proxy_pool:
        proxy_stats = proxy_pool.get_stats()
        print(f'\n代理池统计信息:')
        print(f'  总代理数: {proxy_stats["total_proxies"]}')
        print(f'  健康代理数: {proxy_stats["healthy_proxies"]}')
        print(f'  总请求数: {proxy_stats["total_requests"]}')
        print(f'  成功请求数: {proxy_stats["total_success"]}')
        print(f'  失败请求数: {proxy_stats["total_errors"]}')
        print(f'  整体成功率: {proxy_stats["overall_success_rate"]:.2%}')
    
    if rate_limiter:
        rate_stats = rate_limiter.get_stats()
        print(f'\n速率限制器统计信息:')
        print(f'  最终并发数: {rate_stats["current_concurrency"]}')
        print(f'  当前延迟: {rate_stats["current_delay"]:.1f}秒')
        print(f'  429限制次数: {rate_stats["rate_limit_hits"]}')
        print(f'  总请求数: {rate_stats["total_requests"]}')
        print(f'  成功率: {rate_stats["success_rate"]:.2%}')
        print(f'  详细统计: {rate_stats["stats"]}')
    
    # 发送结束信号给 writer
    await queue.put(None)
    if writer_task:
        await writer_task
        print('数据库写入完成')


def main():
    """主入口函数，兼容旧版本调用方式"""
    asyncio.run(main_async())


async def main_async_single_thread():
    """保留单线程版本作为备选"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, default=2000)
    args = parser.parse_args()

    # 从环境变量读取配置（环境变量优先于代码内默认）
    def env_bool(name, default=False):
        v = os.environ.get(name)
        if v is None:
            return default
        return str(v).lower() in ('1', 'true', 'yes', 'on')

    def env_int(name, default):
        v = os.environ.get(name)
        try:
            return int(v) if v is not None else int(default)
        except Exception:
            return int(default)

    CONFIG = {
        'host': os.environ.get('BUFF_DB_HOST', 'localhost'),
        'port': env_int('BUFF_DB_PORT', 3306),
        'user': os.environ.get('BUFF_DB_USER', 'root'),
        'password': os.environ.get('BUFF_DB_PASSWORD', '123456'),
        'database': os.environ.get('BUFF_DB_DATABASE', 'buffotte'),
        'table': os.environ.get('BUFF_DB_TABLE', 'items'),
        'start_page': env_int('BUFF_START_PAGE', 1),
        'concurrency': env_int('BUFF_CONCURRENCY', 6),
        'cookie_file': os.environ.get('BUFF_COOKIE_FILE', './cookies/cookies.txt'),
        'no_db': env_bool('BUFF_NO_DB', False),
        'proxy_file': os.environ.get('BUFF_PROXY_FILE', None),
        'max_pages': env_int('BUFF_MAX_PAGES', 2000),
    }

    # 从 CONFIG 读取 cookie/proxy
    cookies = {}
    if CONFIG.get('cookie_file'):
        cookies = await load_cookie_file(CONFIG.get('cookie_file'))

    proxies = []
    if CONFIG.get('proxy_file'):
        proxies = await load_proxy_file(CONFIG.get('proxy_file'))

    db_conf = {'host': CONFIG.get('host'), 'port': CONFIG.get('port'), 'user': CONFIG.get('user'), 'password': CONFIG.get('password'), 'database': CONFIG.get('database')}

    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

    # writer (可选)
    writer_task = None
    if not CONFIG.get('no_db'):
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table'), True))  # 单线程版本默认启用价格历史

    # HTTP client pool
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        sem = asyncio.Semaphore(CONFIG.get('concurrency'))

        async def worker(page:int):
            async with sem:
                proxy = None
                if proxies:
                    proxy = random.choice(proxies)
                try:
                    if proxy:
                        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, proxies=proxy, timeout=30.0) as c2:
                            items = await fetch_page(c2, page)
                    else:
                        items = await fetch_page(client, page)
                except PermissionError:
                    print('page', page, 'Login Required - 跳过')
                    return
                except Exception as e:
                    print('page', page, '错误', e)
                    return
                # 保护性检查：如果 items 为空或为 None，跳过
                if not items:
                    print('page', page, 'no items, skip')
                    return
                for it in items:
                    await queue.put(it)
                print('page', page, 'fetched', len(items))

        tasks = []
        # max_pages: CLI 优先，随后读取 CONFIG 中的 max_pages
        max_pages = args.max_pages if args.max_pages is not None else CONFIG.get('max_pages', 2000)
        for p in range(CONFIG.get('start_page'), CONFIG.get('start_page') + max_pages):
            tasks.append(asyncio.create_task(worker(p)))
            # stagger start a bit to avoid一波并发发送
            await asyncio.sleep(random.uniform(0.01, 0.2))

        await asyncio.gather(*tasks)

    # send sentinel to writer
    await queue.put(None)
    if writer_task:
        await writer_task


if __name__ == '__main__':
    main()
