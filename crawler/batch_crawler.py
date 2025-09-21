"""
Buffotte 批量爬虫
用于批量爬取饰品数据的主程序
"""
import asyncio
import argparse
import os
import sys
import random
from pathlib import Path

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


class FlushManager:
    def __init__(self, queue: asyncio.Queue, threshold: int = 200):
        self.queue = queue
        self.threshold = int(threshold or 200)
        self._count = 0
        self._lock = asyncio.Lock()

    async def push_items(self, items):
        # 将 items 放入队列，并根据阈值触发 flush 信号
        async with self._lock:
            for item in items:
                await self.queue.put(item)
            self._count += len(items)
            if self._count >= self.threshold:
                await self.queue.put({'type': 'flush'})
                self._count = 0


async def crawl_pages_range(start_page: int, end_page: int, config: dict, 
                           cookies: dict, data_queue: asyncio.Queue, failed_pages: list, flush_manager: FlushManager):
    """单线程异步爬取函数，负责指定范围的页面"""
    print(f'start crawling pages {start_page}-{end_page}')
    
    # 使用独立的HTTP客户端
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    
    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        concurrency = config.get('concurrency', 6)
        sem = asyncio.Semaphore(concurrency)
        pages_processed = 0
        
        async def worker(page: int):
            nonlocal pages_processed
            async with sem:
                try:
                    # 全局首次爬取阶段：只尝试一次（遇到429/其他错误时不反复重试）
                    items, status = await fetch_page(client, page, max_retries=1)
                except PermissionError:
                    print(f'page {page}: Login Required - 记录为失败')
                    failed_pages.append(page)
                    return
                except Exception as e:
                    print(f'page {page}: 错误 {e} - 记录为失败')
                    failed_pages.append(page)
                    return
                # 如果 fetch_page 返回 None，表示请求在重试后失败，需要记录以便在重试阶段再次尝试
                if items is None:
                    # items is None -> status may indicate HTTP code like 429, or None for generic failure
                    if status is not None:
                        print(f'page{page}: {status} failed')
                    else:
                        print(f'page{page}: failed')
                    failed_pages.append(page)
                    return

                # items 可能是空列表（表示该页确实没有数据），这不是错误
                if isinstance(items, list) and len(items) == 0:
                    print(f'page {page}: no items (空结果)')
                    return
                
                # 添加数据到队列（通过 flush_manager 保证每达到阈值触发一次写入）
                await flush_manager.push_items(items)
                # 简洁输出：pageX: N, done!
                print(f'page{page}: {len(items)}, done!')
                
                pages_processed += 1
                # 保留按页统计日志
                if pages_processed % 50 == 0:
                    print(f'已处理 {pages_processed} 页')
        
        # 创建所有页面的任务
        tasks = []
        for page in range(start_page, end_page + 1):
            tasks.append(asyncio.create_task(worker(page)))
            # 错开启动时间
            await asyncio.sleep(random.uniform(0.01, 0.2))
        
    # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f'finish main crawl of {end_page - start_page + 1} pages')


async def retry_failed_pages(failed_pages: list, config: dict, cookies: dict, data_queue: asyncio.Queue, flush_manager: FlushManager):
    """重新爬取失败的页面（直接修改传入的 failed_pages 列表）

    行为：
    - 进入死循环，轮询当前 failed_pages 的快照进行重试
    - 某页重试成功则从 failed_pages 中删除该页
    - 每轮失败后退避等待，直到 failed_pages 为空为止（或手动中断）
    """
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)

    attempt = 1

    while True:
        if not failed_pages:
            print('没有失败的页面需要重试，重试阶段结束')
            return

        current_pages = list(failed_pages)  # 快照
        print('\n---retry---')

        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
            concurrency = config.get('concurrency', 6)
            sem = asyncio.Semaphore(concurrency)

            async def retry_worker(page: int):
                async with sem:
                    try:
                        # 在重试阶段允许内部重试策略，fetch_page 返回 (items, status)
                        items, status = await fetch_page(client, page)
                    except Exception:
                        print(f'page{page}: failed')
                        return

                    if items is None:
                        # 重试仍失败，若有 status 则显示
                        if status is not None:
                            print(f'page{page}: {status} failed')
                        else:
                            print(f'page{page}: failed')
                        return

                    if isinstance(items, list) and len(items) == 0:
                        print(f'page{page}: 0, done!')
                        try:
                            failed_pages.remove(page)
                        except ValueError:
                            pass
                        return

                    # 成功获取到数据，将数据写入并从 failed_pages 中移除
                    await flush_manager.push_items(items)
                    print(f'page{page}: {len(items)}, done!')
                    try:
                        failed_pages.remove(page)
                    except ValueError:
                        pass

            tasks = [asyncio.create_task(retry_worker(page)) for page in current_pages]
            await asyncio.gather(*tasks, return_exceptions=True)

        # 如果仍有失败页，继续重试（不在调试台打印退避等待）
        if failed_pages:
            print(f'retry page{failed_pages}')
            backoff = min(60, 2 ** attempt + random.random())
            await asyncio.sleep(backoff)
            attempt += 1
            continue

    print('all failed pages retried successfully')
    return


async def main():
    """批量爬虫主函数"""
    parser = argparse.ArgumentParser(description='Buffotte 批量爬虫')
    parser.add_argument('--max-pages', type=int, help='总共要爬取的页面数')
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
        'cookie_file': env_str('BUFF_COOKIE_FILE', 'cookie_file', os.path.join(project_root, 'cookies', 'cookies.txt')),
        'no_db': env_bool('BUFF_NO_DB', 'no_db', False),
        'max_pages': env_int('BUFF_MAX_PAGES', 'max_pages', 2000),
        'enable_price_history': env_bool('BUFF_ENABLE_PRICE_HISTORY', 'enable_price_history', True),
    }

    # 从命令行参数覆盖配置（最高优先级，仅当用户明确指定时）
    if args.max_pages is not None:
        CONFIG['max_pages'] = args.max_pages

    # 从 CONFIG 读取 cookie
    cookies = {}
    cookie_path = CONFIG.get('cookie_file')
    if cookie_path and os.path.exists(cookie_path):
        try:
            cookies = await load_cookie_file(cookie_path)
            print(f'loaded cookies: {len(cookies)}')
        except Exception as e:
            print(f'load cookie failed: {e}')
    else:
        print(f'cookie file not found, using empty cookies: {cookie_path}')

    db_conf = get_db_config_from_dict(CONFIG)

    # 创建异步队列用于数据库写入
    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

    # flush 管理器，控制每达到阈值触发一次数据库写入
    flush_every = env_int('BUFF_FLUSH_EVERY', 'flush_every', 200)
    flush_manager = FlushManager(queue, threshold=flush_every)

    # writer (可选)
    writer_task = None
    if not CONFIG.get('no_db'):
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table'), CONFIG.get('enable_price_history', True)))

    # 计算页面范围
    max_pages = CONFIG.get('max_pages')
    start_page = CONFIG.get('start_page')
    end_page = start_page + max_pages - 1
    
    failed_pages = []
    
    print(f'start single-thread crawl: total {max_pages} pages (pages {start_page}-{end_page})')
    
    # 单线程爬取（全局阶段：每页仅尝试一次，失败记录到 failed_pages）
    await crawl_pages_range(start_page, end_page, CONFIG, cookies, queue, failed_pages, flush_manager)
    
    print('main crawl finished')
    
    # 进入重试阶段：死循环重试 failed_pages，直到清空
    await retry_failed_pages(failed_pages, CONFIG, cookies, queue, flush_manager)
    
    # 发送结束信号给 writer
    await queue.put(None)
    if writer_task:
        await writer_task
    print('database write finished')


if __name__ == '__main__':
    asyncio.run(main())