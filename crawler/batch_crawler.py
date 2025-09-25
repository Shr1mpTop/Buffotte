"""
Buffotte 批量爬虫
用于批量爬取饰品数据的主程序
"""
import asyncio
import argparse
import os
import sys
import random
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawler.core import load_config_json, load_cookie_file, fetch_page, HEADERS, load_proxies, get_random_proxy
from crawler.database import writer_loop, get_db_config_from_dict

try:
    import httpx
except ImportError:
    print("错误: 未安装 httpx。请运行: pip install httpx")
    sys.exit(1)


# 全局进度计数器
progress_counter = {'completed': 0, 'total': 0}


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


async def crawl_concurrent(start_page: int, end_page: int, config: dict,
                          cookies_list: list, data_queue: asyncio.Queue, failed_pages: list, flush_manager: FlushManager):
    """并发爬取函数，使用智能任务分配"""
    print(f'start concurrent crawling pages {start_page}-{end_page} with {len(cookies_list)} accounts')

    # 设置进度计数器
    progress_counter['total'] = end_page - start_page + 1
    progress_counter['completed'] = 0

    # 加载代理池
    proxies = await load_proxies()
    print(f'loaded {len(proxies)} proxies')

    # 准备 cookies 列表
    if not cookies_list:
        print('no cookies available')
        return

    # 创建页面队列（按顺序）
    page_queue = asyncio.Queue()
    for page in range(start_page, end_page + 1):
        await page_queue.put(page)

    # 账户状态管理
    account_states = {}  # account_index -> {'status': 'idle'|'busy'|'cooldown', 'cooldown_until': timestamp}
    for i in range(len(cookies_list)):
        account_states[i] = {'status': 'idle', 'cooldown_until': 0}

    async def crawl_with_account(account_index: int, account_cookies: dict):
        """每个账户的智能爬取任务"""
        pages_processed = 0
        print(f'account {account_index}: starting crawl task')

        while True:
            # 检查账户状态
            current_time = time.time()
            state = account_states[account_index]

            if state['status'] == 'cooldown' and current_time < state['cooldown_until']:
                # 冷却中，等待1秒再检查
                await asyncio.sleep(1)
                continue
            elif state['status'] == 'cooldown':
                # 冷却结束
                state['status'] = 'idle'
                print(f'account {account_index}: cooldown finished')

            # 尝试获取页面任务
            try:
                page = page_queue.get_nowait()
                print(f'account {account_index}: got page {page}')
            except asyncio.QueueEmpty:
                # 没有更多页面，退出
                print(f'account {account_index}: no more pages, exiting')
                break

            # 标记账户为忙碌
            account_states[account_index]['status'] = 'busy'

            # 选择代理
            proxy = get_random_proxy(proxies)
            if not proxy:
                print(f'account {account_index}, page {page}: no proxy available (proxies count: {len(proxies)})')
                failed_pages.append(page)
                account_states[account_index]['status'] = 'idle'
                continue

            # HTTP客户端
            limits = httpx.Limits(max_keepalive_connections=1, max_connections=1)
            
            # 配置代理（如果有的话）
            transport = None
            # 暂时禁用代理，使用直连测试
            # if proxy:
            #     from httpx import AsyncHTTPTransport
            #     proxy_url = f'http://{proxy}'
            #     transport = AsyncHTTPTransport(proxy=proxy_url)
            
            try:
                async with httpx.AsyncClient(headers=HEADERS, cookies=account_cookies, limits=limits, timeout=30.0, transport=transport) as client:
                    items, status = await fetch_page(client, page, max_retries=1, proxy=None)  # proxy 已经在 transport 中配置

                    if status == 429:
                        # 遭遇429，立即冷却账户30秒
                        cooldown_time = 30
                        account_states[account_index]['status'] = 'cooldown'
                        account_states[account_index]['cooldown_until'] = current_time + cooldown_time
                        print(f'account {account_index}: 429 detected, cooldown {cooldown_time}s')
                        failed_pages.append(page)
                        continue

                    if status == 403:
                        # 遭遇403 Action Forbidden，冷却账户60秒
                        cooldown_time = 60
                        account_states[account_index]['status'] = 'cooldown'
                        account_states[account_index]['cooldown_until'] = current_time + cooldown_time
                        print(f'account {account_index}: 403 Action Forbidden detected, cooldown {cooldown_time}s')
                        failed_pages.append(page)
                        continue

                    if items is None:
                        failed_pages.append(page)
                        account_states[account_index]['status'] = 'idle'
                        continue

                    if isinstance(items, list) and len(items) == 0:
                        account_states[account_index]['status'] = 'idle'
                        continue

                    # 成功处理
                    await flush_manager.push_items(items)
                    pages_processed += 1
                    
                    # 更新全局进度
                    progress_counter['completed'] += 1
                    if progress_counter['completed'] % 10 == 0 or progress_counter['completed'] == progress_counter['total']:
                        print(f'进度: {progress_counter["completed"]}/{progress_counter["total"]} 页 ({progress_counter["completed"]/progress_counter["total"]*100:.1f}%)')

            except PermissionError:
                print(f'account {account_index}, page {page}: Login Required')
                failed_pages.append(page)
            except Exception as e:
                print(f'account {account_index}, page {page}: {e}')
                failed_pages.append(page)

            # 标记账户为空闲
            account_states[account_index]['status'] = 'idle'

            # 成功处理后短暂等待
            await asyncio.sleep(1)

        print(f'account {account_index}: processed {pages_processed} pages')

    # 创建并运行所有账户的任务
    tasks = []
    for i, cookies in enumerate(cookies_list):
        task = asyncio.create_task(crawl_with_account(i, cookies))
        tasks.append(task)

    # 等待所有任务完成
    await asyncio.gather(*tasks)

    print(f'finish concurrent crawl of {end_page - start_page + 1} pages')


async def retry_failed_pages(failed_pages: list, config: dict, cookies: dict, data_queue: asyncio.Queue, flush_manager: FlushManager):
    """顺序重试失败的页面"""
    limits = httpx.Limits(max_keepalive_connections=1, max_connections=1)
    proxies = await load_proxies()

    attempt = 1
    while True:
        if not failed_pages:
            print('没有失败的页面需要重试，重试阶段结束')
            return

        current_pages = list(failed_pages)
        print(f'--- retry round {attempt}, remaining {len(current_pages)} pages ---')

        for page in current_pages:
            proxy = get_random_proxy(proxies)
            proxy_url = f'http://{proxy}' if proxy else None
            
            # 配置代理（如果有的话）
            transport = None
            if proxy_url:
                from httpx import AsyncHTTPTransport
                transport = AsyncHTTPTransport(proxy=proxy_url)
            
            async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, limits=limits, timeout=30.0, transport=transport) as client:
                try:
                    items, status = await fetch_page(client, page, max_retries=1, proxy=None)  # proxy 已经在 transport 中配置
                except Exception:
                    continue

                if items is None:
                    continue

                if isinstance(items, list) and len(items) == 0:
                    try:
                        failed_pages.remove(page)
                    except ValueError:
                        pass
                    continue

                await flush_manager.push_items(items)
                try:
                    failed_pages.remove(page)
                except ValueError:
                    pass

            # 重试间隔
            await asyncio.sleep(random.uniform(2, 5))

        if failed_pages:
            backoff = min(60, 5 + attempt * 2)
            await asyncio.sleep(backoff)
            attempt += 1
        else:
            print('retry finished, no failed pages')
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

    start_time = time.time()

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

    # 手动构建固定的三个 cookies
    cookies_list = [
        {
            '__snaker__id': 'VnoLSFGdYF8owjIF',
            '_gid': 'GA.2437815105.90655417858202',
            '_ga': 'GA.1.25d63be2a8903.daa0652b2ea732b5a7c5',
            'Device-Id': 'RW78OIODUfwonP3Fswlv',
            'Locale-Supported': 'zh-Hans',
            'game': 'csgo',
            'utid': 'GvSNodRAcgw6QnUHGOiAb7s6GsWartbY',
            'NTES_WEB_FP': 'e83a6109a9560fc8075a62ace8824481',
            'l_yd_s_netease_buffmUWknxk': '715994DB6318C68DA689CA2117BAE8D6E1139BF8CBA07EDDA7AEF9B6F09F32AEAEE66934EC668B6A0F51DCB259AE2A00A5838DEF1CC8B40E2E4F9095431E0DF2D8C64324A72288FB2AE3E22B98442418819A2F79DF697569F7AC324DC88DE62BC705656BF063CE69F6D8AAF6D0052EB1',
            'gdxidpyhxdE': 'aB9NgymahsHHcWhDzqImPTA0j0oLHOGIl%2FSytfI8UkHwh4xq5h1VR2sgIZbg7Jj6DEUwR6Xo%5Cv7X25ZeXEHjl10g8x%5COvJKjUtvRvAP7wefCXq3q0AfY4tng9x4QDhaG6y4EI%2F0g65kA4wZCso%2FlausXcdOW281V8WQ%2B963nY7VWcaOl%3A1758815880321',
            'qr_code_verify_ticket': '802nPET4ffdc43fa5c702de33e31418a3f81',
            'remember_me': 'U1083557623|hPpYBKoN8b7S5JfLwWZSmWibUFN0qcT6',
            'session': '1-l_eUOoylPVsc09rS63772ggdU_Cw90jIO-6OY9iGgB5k2019252655',
            'csrf_token': 'IjcyNWI2NzAzMzhkYzZjN2QzZGNjZDc3YjhkNzA0NTA4N2IzODkyZjMi.aNVjDQ.hGJC5uKX7ji_kdtxxhWWqsKeYtw'
        },
        {
            '__snaker__id': 'EozKQwjpoX8OmASW',
            '_gid': 'GA.1647811170.09273510258320',
            '_ga': 'GA.1.277b0572b26ed.04b44024359e36592248',
            'Device-Id': 'pFlYbDxvc7vCzChOhMGS',
            'Locale-Supported': 'zh-Hans',
            'game': 'csgo',
            'utid': 'eDIEFgMl27u006k8KWpmfdAfwzP0Oa5V',
            'NTES_WEB_FP': 'e83a6109a9560fc8075a62ace8824481',
            'l_yd_s_netease_buffmUWknxk': '715994DB6318C68DA689CA2117BAE8D6E1139BF8CBA07EDDA7AEF9B6F09F32AEAEE66934EC668B6A0F51DCB259AE2A00062D8FC0C0EADBB5071163FCF054E0AD6C5194762733173DC38E74EC6BB09096E01D753240C1800F5BFA559DA52F00FBF43B1A4830984991C1CCEEB34F53A939',
            'gdxidpyhxdE': 'liap%2FcGQ9o7MU4X4DXMgV2yi22Utu2PwhMSNep5%2F87u9665imD9SmBDNYan9Izgw7aSw00NwZPo44B9xkv%2BxQrZxUJpH9CUcMvN%2BwE3kST%5CCXhzfMN5QUfLKa5DzCEOZNf3waj1dMydZSl3sjGJfu7DTCGakjUyHCr7t3Piu1AAY0r1x%3A1758815922375',
            'qr_code_verify_ticket': '59cDHPOd9c63901208a6c1bd598c6d528cb3',
            'remember_me': 'U1099868849|tlWyxSa46L1xvxjbAUtefOlWpt34XULv',
            'session': '1-X-gjkZdwLp2GY8S24H-hOf8lpCIbYz2DQw_XMWILFvZH2034251241',
            'csrf_token': 'ImU1YTY5M2UyMzM5MzM1ODU3MzZjYjM3M2Q4NTg2NjZjYjc2ZWFhN2Ei.aNVjMg.wru15D7fvMFKcjGm9zknXvSD2V0'
        },
        {
            '__snaker__id': 'xlWRS1Ffgp6n15vu',
            '_gid': 'GA.6767812698.02959512458392',
            '_ga': 'GA.1.2572cf15bcc65.a020d5ef778a2e64f918',
            'Device-Id': '5slWPm9FYyLNXS9fYjKJ',
            'Locale-Supported': 'zh-Hans',
            'game': 'csgo',
            'utid': 'YlEsqwez3HLbkfWEtcHAT5VcaNHVqxma',
            'NTES_WEB_FP': 'e83a6109a9560fc8075a62ace8824481',
            'l_yd_s_netease_buffmUWknxk': '715994DB6318C68DA689CA2117BAE8D6E1139BF8CBA07EDDA7AEF9B6F09F32AEAEE66934EC668B6A0F51DCB259AE2A0092A133F151E1B24F2C51C0FDBC02313979E4C6A316A33B84501F658E397FC6A685D77B1DC99124D16014BB9EFBCFEA9235CC5A203FCB218E9100CD7B47A53EAD',
            'gdxidpyhxdE': 'I55%5Ce%2BMHkV%2FRMg70cPpEg88qH6b5lUcKSnQZoidcO9EIB%2FRNY8C32VCNtNyghGSW6nBW%5Ck98DDgY4OMZaMjl0B6wjOm3eQYpr0%2FIpX1UmVtuQMEgnYU3BmWO9vw6d%5CnpHnynzUDb%2FY%2BbR6Uq%2FbxRu0rj6My2xqmrzblwW17b6SZpfQ8b%3A1758815949434',
            'qr_code_verify_ticket': '6aewzOE105a136bae6c1f831802a7ceae705',
            'remember_me': 'U1096461211|sRcgnnOzOsjWiIp9Wx6Dh56w06oFQVuY',
            'session': '1-xcY62PEFR4xklUbitZqjOlRanKSeYo9WsYkEqsFwRKnd2039755971',
            'csrf_token': 'ImU5ODJiNjNiZTQxYzJlMjNiMGJjOGY4YzVjZmM1ZmMyOTYyMDAwOTIi.aNVjUA.UNWkE5h-gJn_XgAY9G1les5jIwE'
        }
    ]
    
    print(f'loaded {len(cookies_list)} fixed cookies')

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
    
    print(f'start sequential crawl: total {max_pages} pages (pages {start_page}-{end_page})')
    
    # 并发爬取（每个 cookies 一个并发任务）
    await crawl_concurrent(start_page, end_page, CONFIG, cookies_list, queue, failed_pages, flush_manager)
    
    print('main crawl finished')
    
    # 进入重试阶段：顺序重试 failed_pages
    if failed_pages and cookies_list:
        await retry_failed_pages(failed_pages, CONFIG, cookies_list[0], queue, flush_manager)
    
    # 发送结束信号给 writer
    await queue.put(None)
    if writer_task:
        await writer_task
    total_seconds = int(time.time() - start_time)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    print('database write finished')
    print(f'crawl_time: {minutes}min{seconds}s')


if __name__ == '__main__':
    asyncio.run(main())