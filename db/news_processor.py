import pymysql
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import re

# 加载环境变量
# 假设此脚本从项目根目录运行，或者 .env 文件在上一级目录
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    """建立并返回数据库连接。"""
    try:
        config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('USER'),
            'password': os.getenv('PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }
        return pymysql.connect(**config)
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

class NewsProcessor:
    def __init__(self):
        self.conn = get_db_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn and self.conn.open:
            self.conn.close()
            print("数据库连接已关闭。")

    def create_table_if_not_exists(self):
        """如果表不存在，则创建 news 表。"""
        # url 设置为 UNIQUE KEY 以便使用 ON DUPLICATE KEY UPDATE
        # 将 title 设置为 TEXT 以容纳更长的标题
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS news (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title TEXT,
            url VARCHAR(768) UNIQUE,
            source VARCHAR(255),
            publish_time DATETIME,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_table_sql)
            self.conn.commit()
            print("表 'news' 已确认存在。")
        except Exception as e:
            print(f"创建表失败: {e}")

    def _parse_publish_time(self, time_str: str) -> datetime | None:
        """解析非标准的日期时间字符串。"""
        if not time_str:
            return None
        try:
            # 使用正则表达式移除括号内容和星期
            cleaned_str = re.sub(r'\(.*?\)|星期.', '', time_str).strip()
            # 替换中文日期单位
            cleaned_str = cleaned_str.replace('年', '-').replace('月', '-').replace('日', '')
            return datetime.strptime(cleaned_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # 尝试其他可能的格式
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            except:
                print(f"警告: 无法解析日期格式: {time_str}")
                return None

    def insert_or_update_news(self, news_items: list):
        """插入或更新新闻元数据。"""
        if not news_items:
            print("没有要插入的新闻数据。")
            return

        insert_sql = """
        INSERT INTO news (title, url, source, publish_time, summary)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            source = VALUES(source),
            publish_time = VALUES(publish_time),
            summary = VALUES(summary)
        """
        
        values_to_insert = []
        for item in news_items:
            publish_time = self._parse_publish_time(item.get('publish_time'))
            values_to_insert.append((
                item.get('title'),
                item.get('url'),
                item.get('site_name'),
                publish_time,
                item.get('summary')
            ))

        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(insert_sql, values_to_insert)
            self.conn.commit()
            print(f"成功插入或更新了 {len(values_to_insert)} 条新闻记录。")
        except Exception as e:
            print(f"数据库操作失败: {e}")
            self.conn.rollback()

def process_response_file(filepath: str):
    """
    解析指定的 JSON 文件，并将新闻引用数据存入数据库。
    """
    print(f"开始处理文件: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取或解析文件失败: {e}")
        return

    references = []
    output_list = data.get('output', [])
    for item in output_list:
        if item.get('type') == 'message' and 'content' in item:
            for content_item in item['content']:
                if 'annotations' in content_item and content_item['annotations']:
                    for annotation in content_item['annotations']:
                        if annotation.get('type') == 'url_citation':
                            references.append({
                                'title': annotation.get('title'),
                                'url': annotation.get('url'),
                                'publish_time': annotation.get('publish_time'),
                                'site_name': annotation.get('site_name'),
                                'summary': annotation.get('summary') # 提取 summary 字段
                            })
    
    if not references:
        print("在文件中未找到任何参考文献 (annotations)。")
        return

    # 使用 with 语句确保数据库连接被正确关闭
    with NewsProcessor() as processor:
        if processor.conn:
            processor.create_table_if_not_exists()
            processor.insert_or_update_news(references)

if __name__ == '__main__':
    # 假设此脚本在 db 目录下，a.txt 在上两级的 llm 目录下
    project_root = os.path.dirname(os.path.dirname(__file__))
    file_to_parse = os.path.join(project_root, 'llm', 'response.txt')
    
    process_response_file(file_to_parse)
