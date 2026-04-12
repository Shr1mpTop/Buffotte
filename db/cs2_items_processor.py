"""
cs2_items_processor.py — 每日同步 CS2 饰品基础信息

通过 buff-tracker 服务调用 SteamDT /open/cs2/v1/base 接口，
将 API 返回的新增饰品插入 cs2_items 表。
注意：该接口每天只能调用一次，请勿重复调用。
"""

import logging
import os
from typing import Dict, List, Optional

import httpx
import pymysql
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _get_db_connection():
    return pymysql.connect(
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DATABASE"),
        charset=os.getenv("CHARSET", "utf8mb4"),
    )


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cs2_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) DEFAULT NULL COMMENT '饰品名称（中文）',
    market_hash_name VARCHAR(255) NOT NULL COMMENT 'Steam市场哈希名',
    buff_id VARCHAR(50) DEFAULT NULL COMMENT 'BUFF平台饰品ID',
    c5_id VARCHAR(50) DEFAULT NULL COMMENT 'C5平台饰品ID',
    youpin_id VARCHAR(50) DEFAULT NULL COMMENT '悠悠有品平台饰品ID',
    haloskins_id VARCHAR(50) DEFAULT NULL COMMENT 'HaloSkins平台饰品ID',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次录入时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    UNIQUE KEY uk_market_hash_name (market_hash_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CS2饰品基础信息表'
"""


class Cs2ItemsProcessor:
    """通过 SteamDT /open/cs2/v1/base 接口同步所有 CS2 饰品基础信息到 cs2_items 表。"""

    def __init__(self):
        self.bufftracker_url = os.getenv(
            "BUFFTRACKER_URL", "http://host.docker.internal:8001"
        )

    def get_db_connection(self):
        return _get_db_connection()

    def create_table_if_not_exists(self) -> None:
        """确保 cs2_items 表存在。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(_CREATE_TABLE_SQL)
            conn.commit()
            logger.info("cs2_items 表已确保存在")
        except Exception as e:
            logger.error(f"创建 cs2_items 表失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def fetch_base_items(self) -> List[Dict]:
        """
        调用 buff-tracker /api/cs2/base，转发 SteamDT GET /open/cs2/v1/base。
        返回原始 data 列表，每条格式:
          { "name": str, "marketHashName": str,
            "platformList": [{"name": str, "itemId": str}, ...] }
        """
        url = f"{self.bufftracker_url}/api/base"
        try:
            response = httpx.get(url, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                logger.error(
                    f"buff-tracker 返回失败: {data.get('errorMsg') or data.get('errorCodeStr', '')}"
                )
                return []
            items = data.get("data") or []
            logger.info(f"从 buff-tracker 获取 {len(items)} 个饰品基础信息")
            return items
        except Exception as e:
            logger.error(f"调用 buff-tracker 获取饰品基础信息失败: {e}")
            return []

    @staticmethod
    def _extract_platform_ids(platform_list: List[Dict]) -> Dict[str, Optional[str]]:
        """
        从 platformList 中提取各平台的饰品 ID。
        平台名称匹配规则（不区分大小写）：
          buff_id      : 名称含 'buff'
          c5_id        : 名称含 'c5'
          youpin_id    : 名称含 'youpin' 或 '悠悠'
          haloskins_id : 名称含 'halo'
        """
        ids: Dict[str, Optional[str]] = {
            "buff_id": None,
            "c5_id": None,
            "youpin_id": None,
            "haloskins_id": None,
        }
        for platform in platform_list or []:
            pname = (platform.get("name") or "").lower()
            item_id = platform.get("itemId") or None
            if not item_id:
                continue
            if "buff" in pname:
                ids["buff_id"] = item_id
            elif "c5" in pname:
                ids["c5_id"] = item_id
            elif "youpin" in pname or "悠悠" in pname:
                ids["youpin_id"] = item_id
            elif "halo" in pname:
                ids["haloskins_id"] = item_id
        return ids

    def _get_existing_market_hash_names(self, conn) -> set:
        """读取 cs2_items 表中已有的 market_hash_name 集合。"""
        with conn.cursor() as cursor:
            cursor.execute("SELECT market_hash_name FROM cs2_items")
            return {row[0] for row in cursor.fetchall()}

    def sync_new_items(self) -> Dict[str, int]:
        """
        同步新增饰品：仅将 cs2_items 表中尚不存在的条目批量插入。

        返回统计字典:
          { 'api_total': int, 'inserted': int, 'skipped': int }
        """
        items = self.fetch_base_items()
        if not items:
            logger.warning("未获取到任何饰品数据，跳过同步")
            return {"api_total": 0, "inserted": 0, "skipped": 0}

        conn = None
        try:
            conn = self.get_db_connection()
            self.create_table_if_not_exists()
            existing = self._get_existing_market_hash_names(conn)

            from datetime import datetime
            now = datetime.now()

            to_insert: List[tuple] = []
            for item in items:
                market_hash_name = (item.get("marketHashName") or "").strip()
                if not market_hash_name or market_hash_name in existing:
                    continue
                name = (item.get("name") or "").strip() or None
                pids = self._extract_platform_ids(item.get("platformList") or [])
                to_insert.append((
                    name,
                    market_hash_name,
                    pids["buff_id"],
                    pids["c5_id"],
                    pids["youpin_id"],
                    pids["haloskins_id"],
                    now,
                    now,
                ))

            if not to_insert:
                logger.info(
                    f"无新增饰品（cs2_items 已有 {len(existing)} 条，API 共返回 {len(items)} 条）"
                )
                return {"api_total": len(items), "inserted": 0, "skipped": len(items)}

            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO cs2_items "
                    "(name, market_hash_name, buff_id, c5_id, youpin_id, haloskins_id, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    to_insert,
                )
            conn.commit()

            inserted = len(to_insert)
            skipped = len(items) - inserted
            logger.info(
                f"同步完成: 新增 {inserted} 条, 跳过已有 {skipped} 条 (API 共 {len(items)} 条)"
            )
            return {"api_total": len(items), "inserted": inserted, "skipped": skipped}

        except Exception as e:
            logger.error(f"同步 cs2_items 失败: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    processor = Cs2ItemsProcessor()
    stats = processor.sync_new_items()
    print(f"同步结果: 总计={stats['api_total']}, 新增={stats['inserted']}, 跳过={stats['skipped']}")
