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

import httpx

try:
    import pymysql
except Exception:
    pymysql = None

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


async def fetch_page(client: httpx.AsyncClient, page: int, max_retries: int = 3) -> List[Dict[str, Any]]:
    params = {'game': 'csgo', 'page_num': str(page), 'use_suggestion': '0'}
    for attempt in range(1, max_retries+1):
        try:
            r = await client.get(API_URL, params=params, timeout=30.0)
            r.raise_for_status()
            j = r.json()
            if j.get('code') != 'OK':
                msg = j.get('msg')
                if isinstance(msg, str) and 'Login Required' in msg:
                    raise PermissionError('Login Required')
                raise RuntimeError(f"API 返回非 OK: {j.get('code')} {msg}")
            # 某些情况下 API 可能返回 "items": null，确保返回空列表而不是 None
            items = j.get('data', {}).get('items')
            return items or []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                await asyncio.sleep(1 + 2**attempt + random.random())
                continue
            raise
        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(0.5 + attempt + random.random())
                continue
            raise


async def writer_loop(queue: asyncio.Queue, db_conf, table: str):
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

    insert_sql = (
        "INSERT INTO `{table}` (`id`,`appid`,`game`,`name`,`market_hash_name`,`steam_market_url`,`sell_reference_price`,`sell_min_price`,`buy_max_price`,`sell_num`,`buy_num`,`transacted_num`,`goods_info`) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE `appid`=VALUES(`appid`), `game`=VALUES(`game`), `name`=VALUES(`name`), `market_hash_name`=VALUES(`market_hash_name`), `steam_market_url`=VALUES(`steam_market_url`), `sell_reference_price`=VALUES(`sell_reference_price`), `sell_min_price`=VALUES(`sell_min_price`), `buy_max_price`=VALUES(`buy_max_price`), `sell_num`=VALUES(`sell_num`), `buy_num`=VALUES(`buy_num`), `transacted_num`=VALUES(`transacted_num`), `goods_info`=VALUES(`goods_info`)"
    ).format(table=table)

    batch = []
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            goods_json = json.dumps(item.get('goods_info') or {}, ensure_ascii=False)
            tup = (int(item.get('id')), int(item.get('appid') or 0), item.get('game'), item.get('name'), item.get('market_hash_name'), item.get('steam_market_url'), float(item.get('sell_reference_price') or 0), float(item.get('sell_min_price') or 0), float(item.get('buy_max_price') or 0), int(item.get('sell_num') or 0), int(item.get('buy_num') or 0), int(item.get('transacted_num') or 0), goods_json)
            batch.append(tup)
            if len(batch) >= 200:
                try:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    print(f'writer: 写入 {len(batch)} 条记录')
                except Exception as e:
                    print('writer 写入错误', e)
                    conn.rollback()
                batch = []
        if batch:
            cur.executemany(insert_sql, batch)
            conn.commit()
            print(f'writer: 写入剩余 {len(batch)} 条记录')
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
                           cookies: dict, proxies: list, data_manager: ThreadSafeDataManager):
    """单个线程的异步爬取函数，负责指定范围的页面"""
    print(f'线程 {thread_id}: 开始爬取页面 {start_page}-{end_page}')
    
    # 每个线程使用独立的HTTP客户端
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    
    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        sem = asyncio.Semaphore(config.get('concurrency', 6))
        
        async def worker(page: int):
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
                      cookies: dict, proxies: list, data_manager: ThreadSafeDataManager):
    """在线程中运行异步爬虫的包装函数"""
    # 为每个线程创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            crawl_pages_range(thread_id, start_page, end_page, config, cookies, proxies, data_manager)
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
    parser.add_argument('--max-pages', type=int, default=2000)
    parser.add_argument('--threads', type=int, default=5, help='爬虫线程数，每个线程负责一部分页面')
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
    }

    # 从命令行参数覆盖配置（最高优先级）
    if args.threads:
        CONFIG['threads'] = args.threads
    if args.max_pages:
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
    
    # 创建异步队列用于数据库写入
    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
    data_manager.set_db_queue(queue)

    # writer (可选)
    writer_task = None
    if not CONFIG.get('no_db'):
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table')))

    # 计算页面分配
    max_pages = args.max_pages if args.max_pages is not None else CONFIG.get('max_pages', 2000)
    start_page = CONFIG.get('start_page')
    end_page = start_page + max_pages - 1
    threads_count = CONFIG.get('threads')
    
    # 将页面平均分配给各个线程
    pages_per_thread = max_pages // threads_count
    remaining_pages = max_pages % threads_count
    
    print(f'开始多线程爬取: {threads_count} 个线程，总共 {max_pages} 页 (页面 {start_page}-{end_page})')
    
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
                data_manager
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
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table')))

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
