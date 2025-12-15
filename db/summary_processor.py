import json
import os
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
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DATABASE'),
        'charset': os.getenv('CHARSET')
    }
    return pymysql.connect(**config)

def create_tables(conn):
    """
    创建 summary 和 summary_news_association 表（如果不存在）。
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INT AUTO_INCREMENT PRIMARY KEY,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary_news_association (
                summary_id INT,
                news_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (summary_id, news_id),
                FOREIGN KEY (summary_id) REFERENCES summary(id),
                FOREIGN KEY (news_id) REFERENCES news(id)
            )
        """)
    conn.commit()

def process_summary_from_response():
    """
    从 llm/response.txt 解析响应，处理并插入摘要和关联。
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    response_path = os.path.join(project_root, 'llm', 'response.txt')

    with open(response_path, 'r', encoding='utf-8') as f:
        response_data = json.load(f)

    summary_text = None
    annotations = []

    for item in response_data.get('output', []):
        if item.get('type') == 'message':
            content = item.get('content', [])
            if content:
                summary_text = content[0].get('text')
                annotations = content[0].get('annotations', [])
                break
        elif item.get('type') == 'reasoning':
            summary = item.get('summary', [])
            if summary:
                summary_text = summary[0].get('text')
                # annotations may not be present, set to empty
                annotations = []
                break
    
    if not summary_text or not annotations:
        print("未找到有效的摘要或标注。")
        return

    conn = get_db_connection()
    try:
        create_tables(conn)
        with conn.cursor() as cursor:
            # 插入 summary
            cursor.execute("INSERT INTO summary (summary) VALUES (%s)", (summary_text,))
            summary_id = cursor.lastrowid
            
            # 查找并插入关联
            urls = [anno['url'] for anno in annotations if 'url' in anno]
            if urls:
                # 构建SQL查询以匹配多个URL
                sql = "SELECT id FROM news WHERE url IN ({})".format(','.join(['%s'] * len(urls)))
                cursor.execute(sql, tuple(urls))
                news_ids = [item[0] for item in cursor.fetchall()]

                for news_id in news_ids:
                    cursor.execute(
                        "INSERT INTO summary_news_association (summary_id, news_id) VALUES (%s, %s)",
                        (summary_id, news_id)
                    )
            
            conn.commit()
            print(f"成功插入摘要，ID: {summary_id}，并关联了 {len(news_ids)} 条新闻。")

    except Exception as e:
        print(f"处理摘要时发生错误: {e}")
        conn.rollback()
    finally:
        if conn.open:
            conn.close()

if __name__ == "__main__":
    process_summary_from_response()
