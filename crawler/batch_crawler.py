"""
Buffotte 批量爬虫
用于批量爬取饰品数据的主程序
"""
import asyncio
import argparse
import os
import sys
import threading
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawler.core import load_config_json, load_cookie_file, fetch_page, HEADERS
from crawler.database import writer_loop, get_db_config_from_dict

try:
    import httpx
except ImportError:
    print("错误: 未安装 httpx。请运行: pip install httpx")
    sys.exit(1)


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
                           cookies: dict, data_manager: ThreadSafeDataManager):
    """单个线程的异步爬取函数，负责指定范围的页面"""
    print(f'线程 {thread_id}: 开始爬取页面 {start_page}-{end_page}')
    
    # 每个线程使用独立的HTTP客户端
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    
    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        concurrency = config.get('concurrency', 6)
        sem = asyncio.Semaphore(concurrency)
        
        async def worker(page: int):
            async with sem:
                try:
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
            # 错开启动时间
            await asyncio.sleep(random.uniform(0.01, 0.2))
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f'线程 {thread_id}: 完成爬取页面 {start_page}-{end_page}')


def run_crawler_thread(thread_id: int, start_page: int, end_page: int, config: dict, 
                      cookies: dict, data_manager: ThreadSafeDataManager):
    """在线程中运行异步爬虫的包装函数"""
    # 为每个线程创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            crawl_pages_range(thread_id, start_page, end_page, config, cookies, data_manager)
        )
    finally:
        loop.close()


async def main():
    """批量爬虫主函数"""
    parser = argparse.ArgumentParser(description='Buffotte 批量爬虫')
    parser.add_argument('--max-pages', type=int, help='总共要爬取的页面数')
    parser.add_argument('--threads', type=int, help='爬虫线程数，每个线程负责一部分页面')
    parser.add_argument('--config', type=str, default='./config.json', help='配置文件路径')
    args = parser.parse_args()

    # 确定配置文件路径
    if not args.config.startswith('/') and not ':\\' in args.config:
        args.config = os.path.join(project_root, args.config)

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
        'cookie_file': env_str('BUFF_COOKIE_FILE', 'cookie_file', os.path.join(project_root, 'cookies', 'cookies.txt')),
        'no_db': env_bool('BUFF_NO_DB', 'no_db', False),
        'max_pages': env_int('BUFF_MAX_PAGES', 'max_pages', 2000),
        'enable_price_history': env_bool('BUFF_ENABLE_PRICE_HISTORY', 'enable_price_history', True),
    }

    # 从命令行参数覆盖配置（最高优先级，仅当用户明确指定时）
    if args.threads is not None:
        CONFIG['threads'] = args.threads
    if args.max_pages is not None:
        CONFIG['max_pages'] = args.max_pages

    # 从 CONFIG 读取 cookie
    cookies = {}
    cookie_path = CONFIG.get('cookie_file')
    if cookie_path and os.path.exists(cookie_path):
        try:
            cookies = await load_cookie_file(cookie_path)
            print(f'成功加载cookies: {len(cookies)} 个')
        except Exception as e:
            print(f'加载cookie文件失败: {e}')
    else:
        print(f'Cookie文件不存在，使用空cookies: {cookie_path}')

    db_conf = get_db_config_from_dict(CONFIG)

    # 创建线程安全的数据管理器
    data_manager = ThreadSafeDataManager()
    
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


if __name__ == '__main__':
    asyncio.run(main())