import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 将数据库操作类直接定义在此脚本中，避免任何导入问题
class DbManager:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }

    def get_db_connection(self):
        """建立并返回数据库连接。"""
        return pymysql.connect(**self.db_config)

    def setup_level_table(self):
        """创建 level 表并填充初始数据。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                print(" -> Creating 'level' table if not exists...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS level (
                        level INT PRIMARY KEY,
                        level_name VARCHAR(50) NOT NULL,
                        track_permit INT NOT NULL
                    )
                """)
                
                cursor.execute("SELECT COUNT(*) FROM level")
                if cursor.fetchone()[0] == 0:
                    print(" -> Populating 'level' table with initial data...")
                    levels = [
                        (1, '交易学徒', 1),
                        (2, '量化先锋', 2),
                        (3, '华尔街之狼', 3),
                        (4, '股神巴菲特', 4),
                        (5, '金融巨鳄', 5),
                        (99, '超管', 999)
                    ]
                    cursor.executemany(
                        "INSERT INTO level (level, level_name, track_permit) VALUES (%s, %s, %s)",
                        levels
                    )
            conn.commit()
            print(" -> 'level' table is ready.")
        except Exception as e:
            print(f" -> ERROR during level table setup: {e}")
        finally:
            if conn:
                conn.close()

    def alter_user_table(self):
        """修改 user 表，添加 level 字段和外键。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                # 检查 'level' 列是否存在
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'user' AND COLUMN_NAME = 'level'
                """, (self.db_config['database'],))
                
                if cursor.fetchone()[0] == 0:
                    print(" -> 'level' column not found. Adding it to 'user' table...")
                    cursor.execute("ALTER TABLE user ADD COLUMN level INT DEFAULT 1")
                    print(" -> Adding foreign key constraint...")
                    cursor.execute("ALTER TABLE user ADD CONSTRAINT fk_user_level FOREIGN KEY (level) REFERENCES level(level)")
                    conn.commit()
                    print(" -> 'user' table altered successfully.")
                else:
                    print(" -> 'level' column already exists in 'user' table. No changes needed.")
        except Exception as e:
            print(f" -> ERROR during user table alteration: {e}")
        finally:
            if conn:
                conn.close()

# --- 主执行逻辑 ---
def main():
    print("Starting database setup...")
    manager = DbManager()
    
    # 步骤 1: 设置 level 表
    print("\nStep 1: Setting up 'level' table.")
    manager.setup_level_table()
    
    # 步骤 2: 修改 user 表
    print("\nStep 2: Modifying 'user' table.")
    manager.alter_user_table()
    
    print("\nDatabase setup script finished.")

if __name__ == "__main__":
    main()