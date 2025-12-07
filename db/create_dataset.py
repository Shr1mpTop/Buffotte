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

        # SQL 查询语句，按时间戳升序排序
        sql_query = "SELECT * FROM kline_data_day ORDER BY timestamp ASC"
        
        # 使用 pandas 直接从 SQL 查询读取数据到 DataFrame
        print("正在从数据库读取数据...")
        df = pd.read_sql(sql_query, conn)
        print(f"成功读取 {len(df)} 条数据。")

        # 定义输出路径
        output_filename = 'train.csv'
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_filename)
        
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
