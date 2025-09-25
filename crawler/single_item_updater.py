"""
单个饰品更新器
专门处理单个饰品的数据更新功能
"""
import asyncio
import os
import sys
import random
import subprocess
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawler.core import load_config_json, load_cookie_file, fetch_single_item_by_search, load_proxies, get_random_proxy
from crawler.database import writer_loop, get_db_config_from_dict


def is_batch_crawler_running() -> bool:
    """检查batch_crawler是否正在运行"""
    try:
        # 使用tasklist命令检查Python进程
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                              capture_output=True, text=True, encoding='gbk', errors='ignore')

        # 检查输出中是否包含batch_crawler.py
        if result.stdout and 'python.exe' in result.stdout:
            # 更精确的检查：查看是否有包含batch_crawler的Python进程
            try:
                # 使用wmic获取更详细的进程信息
                wmic_result = subprocess.run(['wmic', 'process', 'where', 'name="python.exe"', 'get', 'CommandLine', '/format:csv'],
                                           capture_output=True, text=True, encoding='gbk', errors='ignore')
                if wmic_result.stdout and 'batch_crawler' in wmic_result.stdout.lower():
                    print('检测到batch_crawler正在运行')
                    return True
            except Exception as e:
                print(f'WMIC检查失败: {e}')

        # 如果没有检测到batch_crawler，检查是否有其他明显的爬虫进程
        # 这里可以添加更多的检查逻辑，比如检查特定的进程名或参数

    except Exception as e:
        print(f'检查batch_crawler进程失败: {e}')

    return False


def get_random_account_cookie(cookie_files: list) -> Optional[dict]:
    """从多个cookie文件中随机选择一个"""
    if not cookie_files:
        return {}
    
    selected_file = random.choice(cookie_files)
    try:
        # 同步加载cookie（这里使用同步方式，因为是初始化阶段）
        cookies = {}
        if os.path.exists(selected_file):
            with open(selected_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    cookies[k.strip()] = v.strip()
            print(f'随机选择account: {selected_file} ({len(cookies)} cookies)')
            return cookies
        else:
            print(f'Cookie文件不存在: {selected_file}')
    except Exception as e:
        print(f'加载cookie文件失败: {e}')
    
    return {}


async def update_single_item(item_id: str = None, item_name: str = None, config_path: str = None):
    """单个饰品更新函数"""
    if not item_id and not item_name:
        print('错误: 必须提供饰品ID或名称')
        return False
    
    print(f'开始更新单个饰品: ID={item_id}, Name={item_name}')
    
    # 检查batch_crawler是否正在运行
    if is_batch_crawler_running():
        print('❌ 错误: 检测到batch_crawler正在运行！')
        print('⚠️  为了避免429错误和账号风险，单次更新与批量爬取不能同时运行')
        print('请等待batch_crawler完成后再运行单次更新')
        return False
    
    # 确定配置文件路径
    if not config_path:
        config_path = os.path.join(project_root, 'config.json')
    
    # 加载配置
    json_config = await load_config_json(config_path)
    
    def env_str(name, json_key=None, default=None):
        v = os.environ.get(name)
        if v is not None:
            return v
        elif json_key and json_key in json_config:
            return json_config[json_key]
        else:
            return default
    
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
    
    def env_bool(name, json_key=None, default=False):
        v = os.environ.get(name)
        if v is None:
            return json_config.get(json_key, default) if json_key else default
        return str(v).lower() in ('1', 'true', 'yes', 'on')
    
    CONFIG = {
        'host': env_str('BUFF_DB_HOST', None, json_config.get('db', {}).get('host', 'localhost')),
        'port': env_int('BUFF_DB_PORT', None, json_config.get('db', {}).get('port', 3306)),
        'user': env_str('BUFF_DB_USER', None, json_config.get('db', {}).get('user', 'root')),
        'password': env_str('BUFF_DB_PASSWORD', None, json_config.get('db', {}).get('password', '123456')),
        'database': env_str('BUFF_DB_DATABASE', None, json_config.get('db', {}).get('database', 'buffotte')),
        'table': env_str('BUFF_DB_TABLE', None, json_config.get('db', {}).get('table', 'items')),
        'cookie_file': env_str('BUFF_COOKIE_FILE', 'cookie_file', os.path.join(project_root, 'cookies', 'cookies.txt')),
        'enable_price_history': env_bool('BUFF_ENABLE_PRICE_HISTORY', 'enable_price_history', True),
    }
    
    # 加载所有可用的cookie文件作为account列表
    cookie_base_path = os.path.join(project_root, 'cookies')
    cookie_files = []
    if os.path.exists(cookie_base_path):
        for file in os.listdir(cookie_base_path):
            if file.endswith('.txt'):
                cookie_files.append(os.path.join(cookie_base_path, file))
    
    if not cookie_files:
        print('警告: 未找到任何cookie文件，将使用无账号模式')
        cookies = {}
    else:
        # 尝试不同的account，直到成功或全部尝试完
        success = False
        max_attempts = min(len(cookie_files), 3)  # 最多尝试3个不同的account
        
        for attempt in range(max_attempts):
            # 随机选择一个account
            cookies = get_random_account_cookie(cookie_files)
            
            # 加载代理池
            proxies = []
            proxy_file = os.path.join(project_root, 'proxy_pool', 'proxy_pool_status.json')
            if os.path.exists(proxy_file):
                try:
                    proxies = await load_proxies(proxy_file)
                    print(f'加载代理池: {len(proxies)} 个代理')
                except Exception as e:
                    print(f'加载代理池失败: {e}')
            
            # 随机选择一个代理
            selected_proxy = get_random_proxy(proxies)
            if selected_proxy:
                print(f'随机选择代理: {selected_proxy}')
            else:
                print('无可用代理，使用直连模式')
            
            # 数据库配置
            db_conf = get_db_config_from_dict(CONFIG)
            
            # 创建异步队列用于数据库写入
            queue = asyncio.Queue(maxsize=100)
            
            # 启动数据库写入任务
            writer_task = asyncio.create_task(
                writer_loop(queue, db_conf, CONFIG.get('table'), CONFIG.get('enable_price_history', True))
            )
            
            try:
                # 获取饰品详细信息（暂时不支持代理，因为httpx AsyncClient不支持）
                item_data = await fetch_single_item_by_search(item_id, item_name, cookies)
                if item_data:
                    await queue.put(item_data)
                    print(f'成功获取饰品数据: {item_data.get("name", "未知")} (¥{item_data.get("sell_min_price", 0)})')
                    success = True
                    break  # 成功了，跳出重试循环
                else:
                    print(f'第{attempt + 1}次尝试获取饰品数据失败: ID={item_id}, Name={item_name}')
                    if attempt < max_attempts - 1:
                        print('尝试更换account和proxy重试...')
                        await asyncio.sleep(1)  # 短暂等待后重试
            except Exception as e:
                print(f'第{attempt + 1}次尝试失败: {e}')
                if attempt < max_attempts - 1:
                    print('尝试更换account和proxy重试...')
                    await asyncio.sleep(1)  # 短暂等待后重试
            finally:
                # 发送结束信号
                await queue.put(None)
                await writer_task
        
        if not success:
            print('所有尝试均失败，单个饰品更新失败')
            return False
    
    print('单个饰品更新完成')
    return True


async def main():
    """单个饰品更新器主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buffotte 单个饰品更新器 v0.8.0')
    parser.add_argument('--item-id', type=str, help='要更新的饰品ID')
    parser.add_argument('--item-name', type=str, help='要更新的饰品名称')
    parser.add_argument('--config', type=str, help='配置文件路径')
    
    args = parser.parse_args()
    
    if not args.item_id and not args.item_name:
        print('❌ 错误: 必须提供 --item-id 或 --item-name')
        print('💡 使用示例:')
        print('  python single_item_updater.py --item-name "AK-47 | 红线 (Field-Tested)"')
        print('  python single_item_updater.py --item-id "33815"')
        sys.exit(1)
    
    # 检查batch_crawler是否正在运行
    if is_batch_crawler_running():
        print('❌ 错误: 检测到batch_crawler正在运行！')
        print('⚠️  为了避免429错误和账号风险，单次更新与批量爬取不能同时运行')
        print('请等待batch_crawler完成后再运行单次更新')
        sys.exit(1)
    
    success = await update_single_item(args.item_id, args.item_name, args.config)
    if success:
        print('✅ 饰品更新成功')
        sys.exit(0)
    else:
        print('❌ 饰品更新失败')
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())