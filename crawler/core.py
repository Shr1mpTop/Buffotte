"""
Buffotte 爬虫核心模块
提供基础的数据获取和处理功能
"""
import asyncio
import aiofiles
import json
import time
import random
from typing import List, Dict, Any, Optional
import httpx

# API配置
API_URL = 'https://buff.163.com/api/market/goods'
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Referer': 'https://buff.163.com/market/csgo',
}


async def load_cookie_file(path: str) -> Dict[str, str]:
    """加载cookie文件"""
    cookies = {}
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            async for line in f:
                line = line.strip()
                if not line or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                cookies[k.strip()] = v.strip()
    except Exception as e:
        print(f'加载cookie文件失败: {e}')
        print(f'尝试加载路径: {path}')
    return cookies


async def fetch_page(client: httpx.AsyncClient, page: int, max_retries: int = 3) -> List[Dict[str, Any]]:
    """获取单页数据"""
    for attempt in range(1, max_retries + 1):
        try:
            params = {'game': 'csgo', 'page_num': str(page), 'use_suggestion': '0'}
            
            start_time = time.time()
            r = await client.get(API_URL, params=params, timeout=30.0)
            response_time = time.time() - start_time
            
            r.raise_for_status()
            j = r.json()
            
            if j.get('code') != 'OK':
                msg = j.get('msg')
                if isinstance(msg, str) and 'Login Required' in msg:
                    raise PermissionError('Login Required')
                
                print(f'API返回错误: {j.get("code")} {msg}')
                raise RuntimeError(f"API 返回非 OK: {j.get('code')} {msg}")
            
            # 某些情况下 API 可能返回 "items": null
            items = j.get('data', {}).get('items')
            result = items or []
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f'第 {page} 页遇到429速率限制 (尝试 {attempt}/{max_retries})')
                wait_time = 1 + 2**attempt + random.random()
                print(f'等待 {wait_time:.1f} 秒后重试...')
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f'第 {page} 页HTTP错误: {e.response.status_code}')
                raise
                
        except Exception as e:
            print(f'第 {page} 页请求异常: {e} (尝试 {attempt}/{max_retries})')
            
            if attempt < max_retries:
                wait_time = 0.5 + attempt + random.random()
                await asyncio.sleep(wait_time)
                continue
            raise
    
    print(f'第 {page} 页获取失败，已重试 {max_retries} 次')
    return []


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


async def fetch_single_item_by_search(item_id: str = None, item_name: str = None, cookies: dict = None) -> Optional[Dict[str, Any]]:
    """通过搜索API获取单个饰品的详细信息"""
    try:
        async with httpx.AsyncClient(headers=HEADERS, cookies=cookies or {}, timeout=30.0) as client:
            params = {
                'game': 'csgo',
                'page_num': '1',
                'use_suggestion': '0'
            }
            
            # 如果有名称，添加搜索参数
            if item_name:
                params['search'] = item_name
            
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 'OK':
                print(f'API返回错误: {data.get("code")} {data.get("msg")}')
                return None
            
            items = data.get('data', {}).get('items', [])
            
            # 查找目标饰品
            target_item = None
            if item_id:
                # 按ID查找
                for item in items:
                    if str(item.get('id')) == str(item_id):
                        target_item = item
                        break
            elif item_name:
                # 按名称查找
                for item in items:
                    if item.get('name') == item_name or item.get('market_hash_name') == item_name:
                        target_item = item
                        break
                # 如果没有精确匹配，取第一个
                if not target_item and items:
                    target_item = items[0]
            
            if not target_item:
                print(f'未找到饰品: ID={item_id}, Name={item_name}')
                return None
            
            print(f'找到饰品: {target_item.get("name", "未知")} (ID: {target_item.get("id")})')
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