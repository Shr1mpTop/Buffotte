#!/usr/bin/env python3
"""
SteamDT数据导出脚本
将缓存的SteamDT数据导出为CSV格式
"""

import json
import csv
import os
from datetime import datetime

def load_steamdt_cache(cache_file_path):
    """加载SteamDT缓存数据"""
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('items', [])
    except Exception as e:
        print(f"加载缓存文件失败: {e}")
        return []

def transform_item_for_csv(item):
    """将SteamDT物品数据转换为CSV格式"""
    # 从platformList中提取BUFF平台的itemId作为唯一标识符
    buff_item_id = None
    for platform in item.get('platformList', []):
        if platform.get('name') == 'BUFF':
            buff_item_id = platform.get('itemId')
            break

    # 如果没有BUFF ID，使用第一个平台的ID
    if not buff_item_id and item.get('platformList'):
        buff_item_id = item['platformList'][0].get('itemId')

    # 构造Steam市场URL
    market_hash_name = item.get('marketHashName', '')
    steam_url = f"https://steamcommunity.com/market/listings/730/{market_hash_name.replace(' ', '%20')}"

    return {
        'id': buff_item_id,  # 使用BUFF itemId作为主键
        'appid': 730,  # CS2的AppID
        'game': 'CS2',
        'name': item.get('name', ''),
        'market_hash_name': market_hash_name,
        'steam_market_url': steam_url,
        'sell_reference_price': None,  # 暂时为空
        'sell_min_price': None,  # 暂时为空
        'buy_max_price': None,  # 暂时为空
        'sell_num': None,  # 暂时为空
        'buy_num': None,  # 暂时为空
        'transacted_num': None,  # 暂时为空
        'goods_info': json.dumps(item.get('platformList', []), ensure_ascii=False),  # 存储平台信息
        'updated_at': datetime.now().isoformat()
    }

def export_to_csv(items, output_file_path):
    """将物品数据导出为CSV文件"""
    if not items:
        print("没有数据可导出")
        return False

    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # 获取字段名
        fieldnames = [
            'id', 'appid', 'game', 'name', 'market_hash_name', 'steam_market_url',
            'sell_reference_price', 'sell_min_price', 'buy_max_price',
            'sell_num', 'buy_num', 'transacted_num', 'goods_info', 'updated_at'
        ]

        with open(output_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in items:
                csv_row = transform_item_for_csv(item)
                writer.writerow(csv_row)

        print(f"成功导出 {len(items)} 个物品到 {output_file_path}")
        return True

    except Exception as e:
        print(f"导出CSV失败: {e}")
        return False

def main():
    """主函数"""
    # 文件路径
    cache_file = os.path.join(os.path.dirname(__file__), 'steamdt_base_items.json')
    output_file = os.path.join(os.path.dirname(__file__), 'steamdt_items_export.csv')

    print("开始导出SteamDT数据到CSV...")

    # 加载缓存数据
    items = load_steamdt_cache(cache_file)
    if not items:
        print("没有找到缓存数据")
        return

    print(f"加载了 {len(items)} 个物品")

    # 导出到CSV
    success = export_to_csv(items, output_file)

    if success:
        print("导出完成！")
        print(f"输出文件: {output_file}")
    else:
        print("导出失败！")

if __name__ == "__main__":
    main()