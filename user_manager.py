import pymysql
import bcrypt
import hashlib
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class UserManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('USER'),
            'password': os.getenv('PASSWORD'),
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
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user (
            id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                conn.commit()
            print("user 表创建成功")
        except Exception as e:
            print(f"创建表失败: {e}")
        finally:
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
        user_id = self.generate_user_id(email)
        password_hash = self.hash_password(password)

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO user (id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, username, email, password_hash))
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
            conn.close()

    def verify_password(self, email: str, password: str) -> bool:
        """
        验证用户密码。
        """
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash FROM user WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    stored_hash = result[0]
                    return bcrypt.checkpw(password.encode(), stored_hash.encode())
                else:
                    return False
        except Exception as e:
            print(f"验证密码失败: {e}")
            return False
        finally:
            conn.close()

    def get_user_created_at(self, email: str):
        """
        获取用户的创建时间。
        """
        conn = self.get_db_connection()
        try:
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
            conn.close()