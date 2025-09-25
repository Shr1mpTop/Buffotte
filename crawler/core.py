"""
Buffotte 爬虫核心模块
提供基础的数据获取和处理功能
"""
import asyncio
import aiofiles
import json
import time
import random
import os
from typing import List, Dict, Any, Optional, Tuple
import httpx

# API配置
API_URL = 'https://buff.163.com/api/market/goods'
ITEM_DETAIL_URL = 'https://buff.163.com/api/market/goods/info'
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Referer': 'https://buff.163.com/market/csgo',
}


async def load_proxies(proxy_file: str = 'proxy_pool/proxy_pool_status.json') -> List[str]:
    """加载代理池"""
    proxies = []
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for proxy in data.get('proxies', []):
                if proxy.get('fail_count', 0) == 0:  # 只使用健康的代理
                    proxies.append(proxy['ip_port'])
    except Exception as e:
        print(f'加载代理文件失败: {e}')
    return proxies


def get_random_proxy(proxies: List[str]) -> Optional[str]:
    """随机选择一个代理"""
    if proxies:
        return random.choice(proxies)
    return None


async def load_cookie_file(path: str) -> Dict[str, str]:
    """加载cookie文件，支持单个文件或多个文件（用逗号分隔）"""
    cookies = {}
    try:
        # 支持多个文件路径，用逗号分隔
        paths = [p.strip() for p in path.split(',') if p.strip()]
        for cookie_path in paths:
            if os.path.exists(cookie_path):
                async with aiofiles.open(cookie_path, 'r', encoding='utf-8') as f:
                    async for line in f:
                        line = line.strip()
                        if not line or '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        cookies[k.strip()] = v.strip()
            else:
                print(f'Cookie文件不存在: {cookie_path}')
    except Exception as e:
        print(f'加载cookie文件失败: {e}')
        print(f'尝试加载路径: {path}')
    return cookies


async def fetch_page(client: httpx.AsyncClient, page: int, max_retries: int = 3, proxy: Optional[str] = None) -> Tuple[Optional[List[Dict[str, Any]]], Optional[int]]:
    """获取单页数据。

    返回值为 `(items, status_code)`:
    - 成功时返回 `(list, None)`（list 可能为空）
    - 请求失败并伴随 HTTP 状态码时返回 `(None, status_code)`（例如 429）
    - 其他异常或重试耗尽时返回 `(None, None)` 表示通用失败
    """
    print(f'fetch_page: starting request for page {page}')
    for attempt in range(1, max_retries + 1):
        try:
            params = {'game': 'csgo', 'page_num': str(page), 'use_suggestion': '0'}
            
            start_time = time.time()
            print(f'fetch_page: attempt {attempt}, sending request...')
            r = await client.get(API_URL, params=params, timeout=30.0)
            response_time = time.time() - start_time
            print(f'fetch_page: got response in {response_time:.2f}s, status: {r.status_code}')
            
            r.raise_for_status()
            j = r.json()

            if j.get('code') != 'OK':
                msg = j.get('msg')
                if isinstance(msg, str) and 'Login Required' in msg:
                    raise PermissionError('Login Required')

                # 对于Action Forbidden错误，返回特定的状态码让上层处理
                if j.get('code') == 'Action Forbidden':
                    return None, 403  # 403 Forbidden
                
                print(f'API返回错误: {j.get("code")} {msg}')
                raise RuntimeError(f"API 返回非 OK: {j.get('code')} {msg}")

            # 某些情况下 API 可能返回 "items": null
            items = j.get('data', {}).get('items')
            result = items or []
            print(f'fetch_page: success, got {len(result)} items')
            return result, None
            
        except httpx.HTTPStatusError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 429:
                # 当遭遇 429 时，内部短暂等待后重试（不打印中间 retrial 日志）
                wait_time = 1 + 2**attempt + random.random()
                await asyncio.sleep(wait_time)
                if attempt == max_retries:
                    return None, 429
                continue
            else:
                # 非429的HTTP错误视为失败，返回 (None, status)
                return None, status
                
        except Exception:
            # 遇到非HTTP异常时在内部进行短暂退避重试（不打印错误信息）
            if attempt < max_retries:
                wait_time = 0.5 + attempt + random.random()
                await asyncio.sleep(wait_time)
                continue
            # 重试耗尽，返回 (None, None) 由上层统一处理（全局重试阶段）
            return None, None
    
    return None, None


async def search_item_by_name(item_name: str, cookies: dict) -> Optional[str]:
    """通过名称搜索饰品ID"""
    try:
        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, timeout=30.0) as client:
            # 使用搜索API
            params = {
                'game': 'csgo',
                'page_num': '1',
                'search': item_name,
                'use_suggestion': '0'
            }
            
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 'OK':
                print(f'搜索API返回错误: {data.get("code")} {data.get("msg")}')
                return None
            
            items = data.get('data', {}).get('items', [])
            if not items:
                return None
            
            # 查找精确匹配的饰品
            for item in items:
                if item.get('name') == item_name or item.get('market_hash_name') == item_name:
                    return str(item.get('id'))
            
            # 如果没有精确匹配，返回第一个结果
            return str(items[0].get('id'))
            
    except Exception as e:
        print(f'搜索饰品失败: {e}')
        return None


async def fetch_item_by_id(item_id: str, cookies: dict = None) -> Optional[Dict[str, Any]]:
    """直接通过物品ID获取详细信息"""
    try:
        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies or {}, timeout=30.0) as client:
            params = {
                'goods_id': item_id,
                'game': 'csgo'
            }
            
            print(f'直接获取物品详情: ID={item_id}')
            response = await client.get(ITEM_DETAIL_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 'OK':
                print(f'获取物品详情失败: {data.get("code")} {data.get("msg")}')
                return None
            
            item_data = data.get('data')
            if item_data:
                print(f'成功获取物品详情: {item_data.get("name", "未知")} (ID: {item_id})')
                return item_data
            else:
                print(f'物品不存在: ID={item_id}')
                return None
                
    except Exception as e:
        print(f'获取物品详情异常: {e}')
        return None


async def fetch_single_item_by_search(item_id: str = None, item_name: str = None, cookies: dict = None) -> Optional[Dict[str, Any]]:
    """通过ID或搜索API获取单个饰品的详细信息"""
    
    # 优先通过ID直接获取
    if item_id:
        print(f'尝试通过ID直接获取: {item_id}')
        item_data = await fetch_item_by_id(item_id, cookies)
        if item_data:
            return item_data
        else:
            print(f'通过ID获取失败，尝试搜索方式: {item_name or "未提供名称"}')
    
    # 如果ID获取失败或未提供ID，使用搜索方式
    if not item_name:
        print('错误: 没有可用的搜索条件')
        return None
        
    try:
        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies or {}, timeout=30.0) as client:
            params = {
                'game': 'csgo',
                'page_num': '1',
                'use_suggestion': '0',
                'page_size': 20,
                'search': item_name
            }
            
            print(f'搜索参数: {params}')
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 'OK':
                print(f'API返回错误: {data.get("code")} {data.get("msg")}')
                return None
            
            items = data.get('data', {}).get('items', [])
            print(f'搜索到 {len(items)} 个结果')
            
            # 查找目标饰品
            target_item = None
            
            # 如果指定了ID，优先找到匹配ID的物品
            if item_id:
                for item in items:
                    if str(item.get('id')) == str(item_id):
                        target_item = item
                        print(f'ID匹配找到: {item.get("name")} (ID: {item.get("id")})')
                        break
            
            # 如果没有通过ID找到，或者没有提供ID，使用名称匹配
            if not target_item:
                # 优先进行精确匹配
                for item in items:
                    if (item.get('name') == item_name or 
                        item.get('market_hash_name') == item_name):
                        target_item = item
                        print(f'精确匹配找到: {item.get("name")}')
                        break
                
                # 如果没有精确匹配，进行模糊匹配
                if not target_item:
                    search_lower = item_name.lower()
                    for item in items:
                        item_name_lower = item.get('name', '').lower()
                        market_name_lower = item.get('market_hash_name', '').lower()
                        if (search_lower in item_name_lower or 
                            search_lower in market_name_lower):
                            target_item = item
                            print(f'模糊匹配找到: {item.get("name")}')
                            break
                
                # 如果还没找到，取第一个
                if not target_item and items:
                    target_item = items[0]
                    print(f'使用第一个结果: {target_item.get("name")}')
            
            if not target_item:
                print(f'未找到饰品: ID={item_id}, Name={item_name}')
                return None
            
            print(f'最终选择: {target_item.get("name", "未知")} (ID: {target_item.get("id")})')
            return target_item
            
    except Exception as e:
        print(f'获取饰品详情失败: {e}')
        return None


async def load_config_json(config_path: str) -> Dict[str, Any]:
    """加载config.json配置文件"""
    try:
        async with aiofiles.open(config_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            config = json.loads(content)
            print(f'已加载配置文件: {config_path}')
            return config
    except Exception as e:
        print(f'加载配置文件失败: {e}')
    return {}