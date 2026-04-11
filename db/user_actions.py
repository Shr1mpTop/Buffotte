import logging
from .user_manager import UserManager
import pymysql

logger = logging.getLogger(__name__)

class UserActions:
    def __init__(self):
        self.user_manager = UserManager()

    def create_track_table(self):
        conn = None
        try:
            conn = self.user_manager.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS track (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        market_hash_name VARCHAR(255) NOT NULL,
                        CONSTRAINT fk_email FOREIGN KEY (email) REFERENCES user(email) ON DELETE CASCADE,
                        UNIQUE KEY unique_track (email, market_hash_name)
                    )
                """)
            conn.commit()
            logger.info("Table 'track' created successfully or already exists.")
        except Exception as e:
            logger.error(f"An error occurred while creating the 'track' table: {e}")
        finally:
            if conn:
                conn.close()

    def add_track_item(self, email, market_hash_name):
        conn = None
        try:
            conn = self.user_manager.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO track (email, market_hash_name) VALUES (%s, %s)",
                    (email, market_hash_name)
                )
            conn.commit()
            return {"success": True, "message": "Item tracked successfully."}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            if conn:
                conn.close()

    def remove_track_item(self, email, market_hash_name):
        conn = None
        try:
            conn = self.user_manager.get_db_connection()
            with conn.cursor() as cursor:
                # 1. 删除该用户的追踪记录
                cursor.execute(
                    "DELETE FROM track WHERE email = %s AND market_hash_name = %s",
                    (email, market_hash_name)
                )
                conn.commit()

                # 2. 检查是否还有其他用户在追踪这个饰品
                cursor.execute(
                    "SELECT 1 FROM track WHERE market_hash_name = %s LIMIT 1",
                    (market_hash_name,)
                )
                if not cursor.fetchone():
                    # 没有人在追踪了，清理 item_kline_day 中的缓存数据
                    cursor.execute(
                        "DELETE FROM item_kline_day WHERE market_hash_name = %s",
                        (market_hash_name,)
                    )
                    conn.commit()
                    logger.info(f"饰品 {market_hash_name} 已无用户追踪，已清理其K线缓存数据")

            return {"success": True, "message": "Item untracked successfully."}
        except Exception as e:
            logger.error(f"取消追踪失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            if conn:
                conn.close()

    def get_tracked_items_by_email(self, email):
        conn = None
        try:
            conn = self.user_manager.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        t.market_hash_name, 
                        COALESCE(c.name, t.market_hash_name) as name
                    FROM track t
                    LEFT JOIN cs2_items c ON t.market_hash_name COLLATE utf8mb4_unicode_ci = c.market_hash_name
                    WHERE t.email = %s
                    """,
                    (email,)
                )
                items = cursor.fetchall()
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            if conn:
                conn.close()

if __name__ == '__main__':
    user_actions = UserActions()
    user_actions.create_track_table()