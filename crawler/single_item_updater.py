"""
单个饰品更新器
专门处理单个饰品的数据更新功能
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawler.core import load_config_json, load_cookie_file, fetch_single_item_by_search
from crawler.database import writer_loop, get_db_config_from_dict


async def update_single_item(item_id: str = None, item_name: str = None, config_path: str = None):
    """单个饰品更新函数"""
    if not item_id and not item_name:
        print('错误: 必须提供饰品ID或名称')
        return False
    
    print(f'开始更新单个饰品: ID={item_id}, Name={item_name}')
    
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
    
    # 加载cookies
    cookies = {}
    cookie_path = CONFIG.get('cookie_file')
    if cookie_path and os.path.exists(cookie_path):
        try:
            cookies = await load_cookie_file(cookie_path)
            print(f'成功加载cookies: {len(cookies)} 个')
        except Exception as e:
            print(f'加载cookie文件失败: {e}')
    else:
        print(f'Cookie文件不存在: {cookie_path}')
    
    # 数据库配置
    db_conf = get_db_config_from_dict(CONFIG)
    
    # 创建异步队列用于数据库写入
    queue = asyncio.Queue(maxsize=100)
    
    # 启动数据库写入任务
    writer_task = asyncio.create_task(
        writer_loop(queue, db_conf, CONFIG.get('table'), CONFIG.get('enable_price_history', True))
    )
    
    success = False
    try:
        # 获取饰品详细信息
        item_data = await fetch_single_item_by_search(item_id, item_name, cookies)
        if item_data:
            await queue.put(item_data)
            print(f'成功获取饰品数据: {item_data.get("name", "未知")} (¥{item_data.get("sell_min_price", 0)})')
            success = True
        else:
            print(f'获取饰品数据失败: ID={item_id}, Name={item_name}')
    except Exception as e:
        print(f'更新饰品失败: {e}')
    finally:
        # 发送结束信号
        await queue.put(None)
        await writer_task
        print('单个饰品更新完成')
    
    return success


async def main():
    """单个饰品更新器主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buffotte 单个饰品更新器')
    parser.add_argument('--item-id', type=str, help='要更新的饰品ID')
    parser.add_argument('--item-name', type=str, help='要更新的饰品名称')
    parser.add_argument('--config', type=str, help='配置文件路径')
    
    args = parser.parse_args()
    
    if not args.item_id and not args.item_name:
        print('错误: 必须提供 --item-id 或 --item-name')
        return
    
    success = await update_single_item(args.item_id, args.item_name, args.config)
    if success:
        print('✅ 饰品更新成功')
    else:
        print('❌ 饰品更新失败')


if __name__ == '__main__':
    asyncio.run(main())