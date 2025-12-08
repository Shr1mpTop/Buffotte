import os
import pymysql
from dotenv import load_dotenv
import bcrypt
import hashlib

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
        创建 user 表（如果不存在）。
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                # 注意：这里我们只创建没有level字段的原始user表
                # level字段的添加和外键约束通过alter_user_table_add_level处理
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS user (
                    email VARCHAR(255) PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_sql)
                conn.commit()
            print(" -> 'user' table checked/created successfully (initial schema).")
        except Exception as e:
            print(f" -> ERROR during user table creation: {e}")
            raise # 重新抛出异常
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
                INSERT INTO user (email, username, password_hash, level)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (email, username, hashed_password, 1))
                conn.commit()
            print(f"用户 {username} 注册成功")
            return True
        except pymysql.IntegrityError as e:
            if e.args[0] == 1062:  # 重复键错误
                print(f"邮箱 {email} 已存在")
            else:
                print(f"注册失败: {e}")
            return False
        except Exception as e:
            print(f"注册失败: {e}")
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
            print(f"验证密码失败: {e}")
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
            print(f"获取用户详细信息失败: {e}")
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
            print(f"获取用户创建时间失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

# --- 数据库初始化和迁移脚本 ---
if __name__ == '__main__':
    print("Starting database schema setup and migration...")
    manager = UserManager()

