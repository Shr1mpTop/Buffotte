import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_connection():
    """
    建立并返回数据库连接。
    """
    config = {
        'host': os.getenv('HOST'),
        'port': int(os.getenv('PORT')),
        'user': os.getenv('USER'),
        'password': os.getenv('PASSWORD'),
        'database': os.getenv('DATABASE'),
        'charset': os.getenv('CHARSET')
    }
    return pymysql.connect(**config)

def export_kline_data_to_csv():
    """
    从 kline_data_day 表中查询所有数据，并保存为 CSV 文件。
    """
    try:
        conn = get_db_connection()
        print("数据库连接成功。")

        # SQL 查询语句，获取最新的1000条数据并按时间升序排序
        sql_query = "SELECT * FROM (SELECT * FROM kline_data_day ORDER BY timestamp DESC LIMIT 1000) AS sub ORDER BY timestamp ASC"
        
        # 使用 pandas 直接从 SQL 查询读取数据到 DataFrame
        print("正在从数据库读取最新的1000条数据...")
        df = pd.read_sql(sql_query, conn)
        print(f"成功读取 {len(df)} 条数据。")

        # 定义输出路径，确保 train.csv 保存在 models 文件夹下
        output_filename = 'train.csv'
        # 定位到项目根目录，然后进入 models 文件夹
        project_root = os.path.dirname(os.path.dirname(__file__))
        output_path = os.path.join(project_root, 'models', output_filename)
        
        # 将 DataFrame 保存为 CSV 文件，不包含索引列
        df.to_csv(output_path, index=False)
        
        print(f"数据已成功导出到: {output_path}")

    except Exception as e:
        print(f"导出数据时发生错误: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()
            print("数据库连接已关闭。")

if __name__ == "__main__":
    export_kline_data_to_csv()
