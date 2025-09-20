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


async def crawl_pages_range(start_page: int, end_page: int, config: dict, 
                           cookies: dict, data_queue: asyncio.Queue, failed_pages: list):
    """单线程异步爬取函数，负责指定范围的页面"""
    print(f'开始爬取页面 {start_page}-{end_page}')
    
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
                    items = await fetch_page(client, page)
                except PermissionError:
                    print(f'page {page}: Login Required - 记录为失败')
                    failed_pages.append(page)
                    return
                except Exception as e:
                    print(f'page {page}: 错误 {e} - 记录为失败')
                    failed_pages.append(page)
                    return
                
                # 保护性检查：如果 items 为空或为 None，跳过
                if not items:
                    print(f'page {page}: no items, skip')
                    return
                
                # 添加数据到队列
                for item in items:
                    await data_queue.put(item)
                print(f'page {page}: 获取到 {len(items)} 条记录')
                
                pages_processed += 1
                # 每50页写入一次数据库
                if pages_processed % 50 == 0:
                    print(f'已处理 {pages_processed} 页，正在写入数据库...')
                    # 发送flush信号
                    await data_queue.put({'type': 'flush'})
        
        # 创建所有页面的任务
        tasks = []
        for page in range(start_page, end_page + 1):
            tasks.append(asyncio.create_task(worker(page)))
            # 错开启动时间
            await asyncio.sleep(random.uniform(0.01, 0.2))
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f'完成爬取页面 {start_page}-{end_page}')


async def retry_failed_pages(failed_pages: list, config: dict, cookies: dict, data_queue: asyncio.Queue):
    """重新爬取失败的页面"""
    if not failed_pages:
        print('没有失败的页面需要重试')
        return
    
    print(f'开始重试 {len(failed_pages)} 个失败页面: {failed_pages}')
    
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    
    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0) as client:
        concurrency = config.get('concurrency', 6)
        sem = asyncio.Semaphore(concurrency)
        
        async def retry_worker(page: int):
            async with sem:
                try:
                    items = await fetch_page(client, page)
                except Exception as e:
                    print(f'重试 page {page}: 仍然失败 {e}')
                    return
                
                if not items:
                    print(f'重试 page {page}: no items')
                    return
                
                # 添加数据到队列
                for item in items:
                    await data_queue.put(item)
                print(f'重试 page {page}: 成功获取到 {len(items)} 条记录')
        
        tasks = [asyncio.create_task(retry_worker(page)) for page in failed_pages]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    print('失败页面重试完成')


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
            print(f'成功加载cookies: {len(cookies)} 个')
        except Exception as e:
            print(f'加载cookie文件失败: {e}')
    else:
        print(f'Cookie文件不存在，使用空cookies: {cookie_path}')

    db_conf = get_db_config_from_dict(CONFIG)

    # 创建异步队列用于数据库写入
    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

    # writer (可选)
    writer_task = None
    if not CONFIG.get('no_db'):
        writer_task = asyncio.create_task(writer_loop(queue, db_conf, CONFIG.get('table'), CONFIG.get('enable_price_history', True)))

    # 计算页面范围
    max_pages = CONFIG.get('max_pages')
    start_page = CONFIG.get('start_page')
    end_page = start_page + max_pages - 1
    
    failed_pages = []
    
    print(f'开始单线程爬取: 总共 {max_pages} 页 (页面 {start_page}-{end_page})')
    
    # 单线程爬取
    await crawl_pages_range(start_page, end_page, CONFIG, cookies, queue, failed_pages)
    
    print('主爬取完成')
    
    # 重试失败的页面
    await retry_failed_pages(failed_pages, CONFIG, cookies, queue)
    
    # 发送结束信号给 writer
    await queue.put(None)
    if writer_task:
        await writer_task
        print('数据库写入完成')


if __name__ == '__main__':
    asyncio.run(main())