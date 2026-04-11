import os
import logging
import pymysql
from dotenv import load_dotenv
import bcrypt
import hashlib

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class UserManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }

    def get_db_connection(self):
        try:
            return pymysql.connect(**self.config)
        except Exception as e:
            # Propagate exception so callers can handle connection issues
            raise

    def create_user_table(self):
        """
        创建 user 表（如果不存在），并确保 id / created_at / level 列存在。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    username VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level INT DEFAULT 1
                )
                """
                cursor.execute(create_table_sql)
                conn.commit()

                # 兼容旧表：逐列检测并补充缺失列
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'user'",
                    (self.config['database'],)
                )
                existing = {row[0] for row in cursor.fetchall()}

                if 'id' not in existing:
                    cursor.execute(
                        "ALTER TABLE user ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST"
                    )
                    logger.info("user 表已添加 id 列")

                if 'created_at' not in existing:
                    cursor.execute(
                        "ALTER TABLE user ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                    logger.info("user 表已添加 created_at 列")

                if 'level' not in existing:
                    cursor.execute(
                        "ALTER TABLE user ADD COLUMN level INT DEFAULT 1"
                    )
                    logger.info("user 表已添加 level 列")

                conn.commit()
            logger.info("'user' table checked/created successfully.")
        except Exception as e:
            logger.error(f"ERROR during user table creation: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def generate_user_id(self, email: str) -> str:
        """
        根据邮箱生成唯一的用户 ID。
        """
        return hashlib.sha256(email.encode()).hexdigest()

    def hash_password(self, password: str) -> str:
        """
        使用 bcrypt 对密码进行哈希。
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def register_user(self, username: str, email: str, password: str) -> bool:
        """
        注册新用户。
        返回 True 如果成功，False 如果失败（例如邮箱已存在）。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT email FROM user WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False  # 用户已存在
                
                hashed_password = self.hash_password(password)
                
                # 注册时默认level为1 (Novice)
                sql = """
                INSERT INTO user (email, username, password_hash, level, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, (email, username, hashed_password, 1))
                conn.commit()
            logger.info(f"用户 {username} 注册成功")
            return True
        except pymysql.IntegrityError as e:
            if e.args[0] == 1062:  # 重复键错误
                logger.warning(f"邮箱 {email} 已存在")
            else:
                logger.error(f"注册失败: {e}")
            return False
        except Exception as e:
            logger.error(f"注册失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def verify_password(self, email: str, password: str) -> bool:
        """
        验证用户密码。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash FROM user WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    stored_hash = result[0].encode('utf-8')
                    return bcrypt.checkpw(password.encode(), stored_hash)
                else:
                    return False
        except Exception as e:
            logger.error(f"验证密码失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_user_details(self, email: str):
        """
        获取用户的详细信息，包括等级和权限。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT 
                    u.email, 
                    u.username, 
                    u.created_at, 
                    l.level, 
                    l.level_name, 
                    l.track_permit,
                    (SELECT COUNT(*) FROM track WHERE email = u.email) as tracked_count
                FROM user u
                JOIN level l ON u.level = l.level
                WHERE u.email = %s
                """
                cursor.execute(sql, (email,))
                result = cursor.fetchone()
                return result
        except Exception as e:
            logger.error(f"获取用户详细信息失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_created_at(self, email: str):
        """
        获取用户的创建时间。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT created_at FROM user WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    return None
        except Exception as e:
            logger.error(f"获取用户创建时间失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

# --- 数据库初始化和迁移脚本 ---
if __name__ == '__main__':
    logger.info("Starting database schema setup and migration...")
    manager = UserManager()

