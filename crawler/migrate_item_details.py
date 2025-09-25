import pymysql
import json
from datetime import datetime

def migrate_item_details():
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'buffotte',
        'charset': 'utf8mb4'
    }

    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 查询所有items
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()

        print(f"找到 {len(items)} 个饰品，开始迁移...")

        # 准备插入语句
        insert_query = """
        INSERT INTO item_details (
            item_id, name, market_hash_name, goods_info, icon_url, steam_price,
            steam_price_cny, original_icon_url, type_id, type_category,
            type_internal_name, type_localized_name, rarity_id, rarity_category,
            rarity_internal_name, rarity_localized_name, weapon_id, weapon_category,
            weapon_internal_name, weapon_localized_name, quality_id, quality_category,
            quality_internal_name, quality_localized_name, category_id, category_category,
            category_internal_name, category_localized_name, exterior_id, exterior_category,
            exterior_internal_name, exterior_localized_name
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        migrated_count = 0
        for item in items:
            try:
                # 解析goods_info JSON
                goods_info = item['goods_info']
                if goods_info:
                    data = json.loads(goods_info)
                else:
                    data = {}

                # 提取基本字段
                icon_url = data.get('icon_url')
                steam_price = data.get('steam_price')
                steam_price_cny = data.get('steam_price_cny')
                original_icon_url = data.get('original_icon_url')

                # 提取tags信息
                info = data.get('info', {})
                tags = info.get('tags', {})

                # type
                type_info = tags.get('type', {})
                type_id = type_info.get('id')
                type_category = type_info.get('category')
                type_internal_name = type_info.get('internal_name')
                type_localized_name = type_info.get('localized_name')

                # rarity
                rarity_info = tags.get('rarity', {})
                rarity_id = rarity_info.get('id')
                rarity_category = rarity_info.get('category')
                rarity_internal_name = rarity_info.get('internal_name')
                rarity_localized_name = rarity_info.get('localized_name')

                # weapon
                weapon_info = tags.get('weapon', {})
                weapon_id = weapon_info.get('id')
                weapon_category = weapon_info.get('category')
                weapon_internal_name = weapon_info.get('internal_name')
                weapon_localized_name = weapon_info.get('localized_name')

                # quality
                quality_info = tags.get('quality', {})
                quality_id = quality_info.get('id')
                quality_category = quality_info.get('category')
                quality_internal_name = quality_info.get('internal_name')
                quality_localized_name = quality_info.get('localized_name')

                # category
                category_info = tags.get('category', {})
                category_id = category_info.get('id')
                category_category = category_info.get('category')
                category_internal_name = category_info.get('internal_name')
                category_localized_name = category_info.get('localized_name')

                # exterior
                exterior_info = tags.get('exterior', {})
                exterior_id = exterior_info.get('id')
                exterior_category = exterior_info.get('category')
                exterior_internal_name = exterior_info.get('internal_name')
                exterior_localized_name = exterior_info.get('localized_name')

                # 准备插入数据
                values = (
                    item['id'],  # item_id
                    item['name'],
                    item['market_hash_name'],
                    goods_info,  # 存储完整的JSON
                    icon_url,
                    steam_price,
                    steam_price_cny,
                    original_icon_url,
                    type_id, type_category, type_internal_name, type_localized_name,
                    rarity_id, rarity_category, rarity_internal_name, rarity_localized_name,
                    weapon_id, weapon_category, weapon_internal_name, weapon_localized_name,
                    quality_id, quality_category, quality_internal_name, quality_localized_name,
                    category_id, category_category, category_internal_name, category_localized_name,
                    exterior_id, exterior_category, exterior_internal_name, exterior_localized_name
                )

                cursor.execute(insert_query, values)
                migrated_count += 1

                if migrated_count % 100 == 0:
                    print(f"已迁移 {migrated_count} 个饰品...")

            except Exception as e:
                print(f"迁移饰品 ID {item['id']} 时出错: {str(e)}")
                continue

        conn.commit()
        print(f"迁移完成！共迁移 {migrated_count} 个饰品。")

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_item_details()