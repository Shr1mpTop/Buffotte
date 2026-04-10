import pymysql
from dotenv import load_dotenv
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def get_db_connection():
    """建立并返回数据库连接。"""
    try:
        config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }
        return pymysql.connect(**config)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None


class SkinEntityProcessor:
    """饰品实体处理器：管理 skin_entities 表的 CRUD 操作。"""

    def __init__(self):
        self.conn = get_db_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn and self.conn.open:
            self.conn.close()

    def create_table_if_not_exists(self):
        """创建 skin_entities 表（如果不存在）。"""
        sql = """
        CREATE TABLE IF NOT EXISTS skin_entities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            skin_name VARCHAR(255) NOT NULL COMMENT '饰品中文名称，如 蝴蝶刀（虎牙）',
            market_hash_name VARCHAR(512) DEFAULT NULL COMMENT 'Steam市场哈希名，如 Karambit | Doppler',
            weapon_type VARCHAR(64) DEFAULT NULL COMMENT '武器类型：knife/glove/rifle/pistol/smg/shotgun/machinegun/other',
            rarity VARCHAR(64) DEFAULT NULL COMMENT '稀有度：消费级/工业级/军规级/受限/保密/隐秘/非凡',
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '首次发现时间',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
            mention_count INT DEFAULT 1 COMMENT '被提及次数',
            UNIQUE KEY uk_skin_name (skin_name),
            UNIQUE KEY uk_market_hash_name (market_hash_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logger.error(f"创建 skin_entities 表失败: {e}")

    def upsert_skin_entity(self, skin_name: str, market_hash_name: str = None,
                           weapon_type: str = None, rarity: str = None) -> int | None:
        """
        插入新饰品实体，若已存在则更新 mention_count 和其他字段。
        返回实体 ID。
        """
        sql = """
        INSERT INTO skin_entities (skin_name, market_hash_name, weapon_type, rarity)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            mention_count = mention_count + 1,
            market_hash_name = COALESCE(VALUES(market_hash_name), market_hash_name),
            weapon_type = COALESCE(VALUES(weapon_type), weapon_type),
            rarity = COALESCE(VALUES(rarity), rarity)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (skin_name, market_hash_name, weapon_type, rarity))
            self.conn.commit()
            # 获取 ID
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT id FROM skin_entities WHERE skin_name = %s", (skin_name,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"插入/更新 skin_entity 失败: {e}")
            self.conn.rollback()
            return None

    def get_skin_entity_by_name(self, skin_name: str) -> dict | None:
        """根据中文名称查询饰品实体。"""
        sql = "SELECT * FROM skin_entities WHERE skin_name = %s"
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (skin_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"查询 skin_entity 失败: {e}")
            return None

    def get_skin_entity_by_id(self, entity_id: int) -> dict | None:
        """根据 ID 查询饰品实体。"""
        sql = "SELECT * FROM skin_entities WHERE id = %s"
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (entity_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"查询 skin_entity 失败: {e}")
            return None

    def search_skins(self, keyword: str, limit: int = 20) -> list:
        """模糊搜索饰品实体（按中文名或英文名）。"""
        sql = """
        SELECT * FROM skin_entities
        WHERE skin_name LIKE %s OR market_hash_name LIKE %s
        ORDER BY mention_count DESC, last_updated DESC
        LIMIT %s
        """
        pattern = f"%{keyword}%"
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (pattern, pattern, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"搜索 skin_entity 失败: {e}")
            return []

    def get_trending_skins(self, limit: int = 20) -> list:
        """获取热门饰品（按提及次数和最近更新排序）。"""
        sql = """
        SELECT se.*, sd.current_price, sd.price_change_24h, sd.price_change_7d
        FROM skin_entities se
        LEFT JOIN skin_details sd ON se.id = sd.skin_entity_id
        ORDER BY se.mention_count DESC, se.last_updated DESC
        LIMIT %s
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取热门饰品失败: {e}")
            return []


class SkinSearchTaskProcessor:
    """搜索任务处理器：管理 skin_search_tasks 表的 CRUD 操作。"""

    def __init__(self):
        self.conn = get_db_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn and self.conn.open:
            self.conn.close()

    def create_table_if_not_exists(self):
        """创建 skin_search_tasks 表（如果不存在）。"""
        sql = """
        CREATE TABLE IF NOT EXISTS skin_search_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            skin_entity_id INT NOT NULL COMMENT '关联的饰品实体ID',
            source_url VARCHAR(768) DEFAULT NULL COMMENT '来源新闻URL',
            source_annotation_json JSON DEFAULT NULL COMMENT '来源标注原始JSON',
            priority INT DEFAULT 0 COMMENT '优先级：3=价格事件, 2=新皮肤发布, 1=一般提及',
            status ENUM('pending', 'running', 'done', 'failed') DEFAULT 'pending' COMMENT '任务状态',
            assigned_agent VARCHAR(64) DEFAULT NULL COMMENT '执行任务的代理标识',
            result_json JSON DEFAULT NULL COMMENT '爬取结果JSON',
            error_message TEXT DEFAULT NULL COMMENT '错误信息',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_skin_entity_id (skin_entity_id),
            FOREIGN KEY (skin_entity_id) REFERENCES skin_entities(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logger.error(f"创建 skin_search_tasks 表失败: {e}")

    def create_task(self, skin_entity_id: int, source_url: str = None,
                    source_annotation_json: dict = None, priority: int = 0) -> int | None:
        """创建新的搜索任务，返回任务 ID。"""
        sql = """
        INSERT INTO skin_search_tasks (skin_entity_id, source_url, source_annotation_json, priority)
        VALUES (%s, %s, %s, %s)
        """
        annotation_str = json.dumps(source_annotation_json, ensure_ascii=False) if source_annotation_json else None
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (skin_entity_id, source_url, annotation_str, priority))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"创建搜索任务失败: {e}")
            self.conn.rollback()
            return None

    def get_pending_tasks(self, limit: int = 10) -> list:
        """获取待处理的任务（按优先级降序）。"""
        sql = """
        SELECT * FROM skin_search_tasks
        WHERE status = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT %s
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            return []

    def update_task_status(self, task_id: int, status: str,
                           assigned_agent: str = None, result_json: dict = None,
                           error_message: str = None):
        """更新任务状态。"""
        parts = ["status = %s"]
        params = [status]

        if assigned_agent is not None:
            parts.append("assigned_agent = %s")
            params.append(assigned_agent)
        if result_json is not None:
            parts.append("result_json = %s")
            params.append(json.dumps(result_json, ensure_ascii=False))
        if error_message is not None:
            parts.append("error_message = %s")
            params.append(error_message)

        params.append(task_id)
        sql = f"UPDATE skin_search_tasks SET {', '.join(parts)} WHERE id = %s"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            self.conn.rollback()

    def get_tasks_by_skin_entity(self, skin_entity_id: int) -> list:
        """获取指定饰品实体的所有任务。"""
        sql = """
        SELECT * FROM skin_search_tasks
        WHERE skin_entity_id = %s
        ORDER BY created_at DESC
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (skin_entity_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return []

    def has_recent_task(self, skin_entity_id: int, hours: int = 4) -> bool:
        """检查指定饰品实体在最近 N 小时内是否已有任务（用于去重）。"""
        sql = """
        SELECT COUNT(*) as cnt FROM skin_search_tasks
        WHERE skin_entity_id = %s
          AND status IN ('pending', 'running', 'done')
          AND created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (skin_entity_id, hours))
                row = cursor.fetchone()
                return row[0] > 0
        except Exception as e:
            logger.error(f"检查最近任务失败: {e}")
            return False


class SkinDetailProcessor:
    """饰品详情处理器：管理 skin_details 表的 CRUD 操作。"""

    def __init__(self):
        self.conn = get_db_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn and self.conn.open:
            self.conn.close()

    def create_table_if_not_exists(self):
        """创建 skin_details 表（如果不存在）。"""
        sql = """
        CREATE TABLE IF NOT EXISTS skin_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            skin_entity_id INT NOT NULL COMMENT '关联的饰品实体ID',
            platform VARCHAR(32) NOT NULL COMMENT '平台：steamdt/buff/csqaq',
            current_price DECIMAL(12, 2) DEFAULT NULL COMMENT '当前价格',
            price_change_24h DECIMAL(8, 4) DEFAULT NULL COMMENT '24小时价格变化率',
            price_change_7d DECIMAL(8, 4) DEFAULT NULL COMMENT '7天价格变化率',
            volume INT DEFAULT NULL COMMENT '交易量',
            supply_count INT DEFAULT NULL COMMENT '在售数量',
            kline_data_json JSON DEFAULT NULL COMMENT 'K线数据JSON',
            extra_data_json JSON DEFAULT NULL COMMENT '额外数据（平台特有字段）',
            last_crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后爬取时间',
            UNIQUE KEY uk_skin_entity_platform (skin_entity_id, platform),
            FOREIGN KEY (skin_entity_id) REFERENCES skin_entities(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logger.error(f"创建 skin_details 表失败: {e}")

    def upsert_skin_detail(self, skin_entity_id: int, platform: str,
                           current_price: float = None, price_change_24h: float = None,
                           price_change_7d: float = None, volume: int = None,
                           supply_count: int = None, kline_data_json: dict = None,
                           extra_data_json: dict = None) -> int | None:
        """
        插入或更新饰品详情（按 skin_entity_id + platform 去重）。
        返回记录 ID。
        """
        sql = """
        INSERT INTO skin_details
            (skin_entity_id, platform, current_price, price_change_24h, price_change_7d,
             volume, supply_count, kline_data_json, extra_data_json, last_crawled_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            current_price = VALUES(current_price),
            price_change_24h = VALUES(price_change_24h),
            price_change_7d = VALUES(price_change_7d),
            volume = VALUES(volume),
            supply_count = VALUES(supply_count),
            kline_data_json = VALUES(kline_data_json),
            extra_data_json = VALUES(extra_data_json),
            last_crawled_at = NOW()
        """
        kline_str = json.dumps(kline_data_json, ensure_ascii=False) if kline_data_json else None
        extra_str = json.dumps(extra_data_json, ensure_ascii=False) if extra_data_json else None

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (
                    skin_entity_id, platform, current_price, price_change_24h,
                    price_change_7d, volume, supply_count, kline_str, extra_str
                ))
            self.conn.commit()
            # 获取 ID
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM skin_details WHERE skin_entity_id = %s AND platform = %s",
                    (skin_entity_id, platform)
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"插入/更新 skin_detail 失败: {e}")
            self.conn.rollback()
            return None

    def get_skin_detail(self, skin_entity_id: int, platform: str = None) -> dict | list | None:
        """获取饰品详情，可指定平台或获取所有平台数据。"""
        if platform:
            sql = "SELECT * FROM skin_details WHERE skin_entity_id = %s AND platform = %s"
            params = (skin_entity_id, platform)
        else:
            sql = "SELECT * FROM skin_details WHERE skin_entity_id = %s"
            params = (skin_entity_id,)

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params)
                if platform:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询 skin_detail 失败: {e}")
            return None

    def get_stale_details(self, hours: int = 4, limit: int = 20) -> list:
        """获取超过 N 小时未更新的饰品详情（用于定时刷新）。"""
        sql = """
        SELECT sd.*, se.skin_name, se.market_hash_name
        FROM skin_details sd
        JOIN skin_entities se ON sd.skin_entity_id = se.id
        WHERE sd.last_crawled_at < DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY sd.last_crawled_at ASC
        LIMIT %s
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (hours, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取过期详情失败: {e}")
            return []


class NewsSkinAssociationProcessor:
    """新闻-饰品关联处理器：管理 news_skin_association 表。"""

    def __init__(self):
        self.conn = get_db_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn and self.conn.open:
            self.conn.close()

    def create_table_if_not_exists(self):
        """创建 news_skin_association 表（如果不存在）。"""
        sql = """
        CREATE TABLE IF NOT EXISTS news_skin_association (
            news_id INT NOT NULL COMMENT '新闻ID',
            skin_entity_id INT NOT NULL COMMENT '饰品实体ID',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (news_id, skin_entity_id),
            FOREIGN KEY (news_id) REFERENCES news(id),
            FOREIGN KEY (skin_entity_id) REFERENCES skin_entities(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logger.error(f"创建 news_skin_association 表失败: {e}")

    def create_association(self, news_id: int, skin_entity_id: int):
        """创建新闻-饰品关联（忽略重复）。"""
        sql = """
        INSERT IGNORE INTO news_skin_association (news_id, skin_entity_id)
        VALUES (%s, %s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (news_id, skin_entity_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"创建新闻-饰品关联失败: {e}")
            self.conn.rollback()

    def create_associations_batch(self, news_id: int, skin_entity_ids: list[int]):
        """批量创建新闻-饰品关联。"""
        if not skin_entity_ids:
            return
        sql = """
        INSERT IGNORE INTO news_skin_association (news_id, skin_entity_id)
        VALUES (%s, %s)
        """
        values = [(news_id, sid) for sid in skin_entity_ids]
        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(sql, values)
            self.conn.commit()
        except Exception as e:
            logger.error(f"批量创建新闻-饰品关联失败: {e}")
            self.conn.rollback()

    def get_skins_by_news(self, news_id: int) -> list:
        """获取指定新闻关联的所有饰品实体。"""
        sql = """
        SELECT se.* FROM skin_entities se
        JOIN news_skin_association nsa ON se.id = nsa.skin_entity_id
        WHERE nsa.news_id = %s
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (news_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询新闻关联饰品失败: {e}")
            return []

    def get_news_by_skin(self, skin_entity_id: int) -> list:
        """获取指定饰品实体关联的所有新闻。"""
        sql = """
        SELECT n.* FROM news n
        JOIN news_skin_association nsa ON n.id = nsa.news_id
        WHERE nsa.skin_entity_id = %s
        ORDER BY n.publish_time DESC
        """
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, (skin_entity_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询饰品关联新闻失败: {e}")
            return []


def create_all_tables():
    """创建所有新表（如果不存在）。"""
    logger.info("正在创建饰品相关数据表...")
    processors = [
        SkinEntityProcessor(),
        SkinSearchTaskProcessor(),
        SkinDetailProcessor(),
        NewsSkinAssociationProcessor(),
    ]
    for processor in processors:
        processor.create_table_if_not_exists()
        if processor.conn and processor.conn.open:
            processor.conn.close()
    logger.info("所有饰品相关数据表创建完成。")


if __name__ == "__main__":
    create_all_tables()
