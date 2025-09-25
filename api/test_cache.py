"""
SteamDT API 缓存测试
验证缓存机制是否正常工作，避免不必要的API调用
"""
import asyncio
import os
from steamdt_client import SteamDTClient


async def test_cache():
    """测试缓存功能"""
    print("=== SteamDT API 缓存测试 ===\n")

    async with SteamDTClient() as client:
        print("1. 首次获取基础信息（应该调用API）:")
        base_items = await client.get_base_items()
        print(f"   获取到 {len(base_items)} 个饰品\n")

        print("2. 再次获取基础信息（应该使用缓存）:")
        base_items = await client.get_base_items()
        print(f"   获取到 {len(base_items)} 个饰品\n")

        print("3. 强制更新基础信息（应该调用API，但会因为限制失败）:")
        base_items = await client.get_base_items(force_update=True)
        print(f"   获取到 {len(base_items)} 个饰品\n")

        print("4. 检查本地缓存文件:")
        if os.path.exists('steamdt_base_items.json'):
            print("   缓存文件存在")
            # 显示文件大小
            size = os.path.getsize('steamdt_base_items.json')
            print(f"   文件大小: {size} bytes")
        else:
            print("   缓存文件不存在")

    print("\n=== 测试完成 ===")


if __name__ == '__main__':
    asyncio.run(test_cache())