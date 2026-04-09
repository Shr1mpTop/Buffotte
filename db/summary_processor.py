import json
import os
import logging
import pymysql
from dotenv import load_dotenv
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

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
    兼容旧表结构：仅在列不存在时添加 summary_date 列。
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INT AUTO_INCREMENT PRIMARY KEY,
                summary TEXT NOT NULL,
                summary_date DATE DEFAULT NULL COMMENT '摘要所属日期（北京时间），每天最多一条',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_summary_date (summary_date)
            )
        """)
        # 兼容旧表：如果表已存在但没有 summary_date 列，则添加
        try:
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'summary' AND COLUMN_NAME = 'summary_date'
            """, (os.getenv('DATABASE'),))
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE summary ADD COLUMN summary_date DATE DEFAULT NULL COMMENT '摘要所属日期' AFTER summary")
                cursor.execute("ALTER TABLE summary ADD UNIQUE KEY uk_summary_date (summary_date)")
                # 回填旧数据：从 created_at 推导 summary_date
                cursor.execute("UPDATE summary SET summary_date = DATE(created_at) WHERE summary_date IS NULL")
                logger.info("已为 summary 表添加 summary_date 列并回填旧数据")
        except Exception as e:
            logger.warning(f"检查/添加 summary_date 列时: {e}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary_news_association (
                summary_id INT,
                news_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (summary_id, news_id),
                FOREIGN KEY (summary_id) REFERENCES summary(id) ON DELETE CASCADE,
                FOREIGN KEY (news_id) REFERENCES news(id)
            )
        """)
    conn.commit()

def _extract_summary_and_annotations(response_data: dict):
    """
    从 LLM 响应数据中提取摘要文本和标注。
    优先使用 message 类型，如果没有则使用 reasoning 类型。
    """
    summary_text = None
    annotations = []

    # 第一轮：优先找 message 类型（包含完整的 text + annotations）
    for item in response_data.get('output', []):
        if item.get('type') == 'message':
            content = item.get('content', [])
            if content:
                summary_text = content[0].get('text')
                annotations = content[0].get('annotations', [])
                if summary_text:
                    return summary_text, annotations

    # 第二轮：降级使用 reasoning 类型
    for item in response_data.get('output', []):
        if item.get('type') == 'reasoning':
            summary_list = item.get('summary', [])
            if summary_list:
                summary_text = summary_list[0].get('text')
                if summary_text:
                    return summary_text, []

    return summary_text, annotations

def process_summary_from_response():
    """
    从 llm/response.txt 解析响应，处理并插入摘要和关联。
    每天只保留一条摘要：如果当天已有则替换。
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    response_path = os.path.join(project_root, 'llm', 'response.txt')

    with open(response_path, 'r', encoding='utf-8') as f:
        response_data = json.load(f)

    summary_text, annotations = _extract_summary_and_annotations(response_data)

    if not summary_text:
        logger.warning("未找到有效的摘要文本，跳过。")
        return

    # 计算当天日期（北京时间）
    today_bj = datetime.now(pytz.timezone('Asia/Shanghai')).date()

    conn = get_db_connection()
    try:
        create_tables(conn)
        with conn.cursor() as cursor:
            # 检查当天是否已有摘要
            cursor.execute("SELECT id FROM summary WHERE summary_date = %s", (today_bj,))
            existing = cursor.fetchone()

            if existing:
                old_summary_id = existing[0]
                # 删除旧的关联和摘要，重新插入
                cursor.execute("DELETE FROM summary_news_association WHERE summary_id = %s", (old_summary_id,))
                cursor.execute("DELETE FROM summary WHERE id = %s", (old_summary_id,))
                logger.info(f"已删除当天旧摘要 ID={old_summary_id}，准备替换")

            # 插入新摘要
            cursor.execute(
                "INSERT INTO summary (summary, summary_date) VALUES (%s, %s)",
                (summary_text, today_bj)
            )
            summary_id = cursor.lastrowid

            # 查找并插入关联（即使 annotations 为空也不影响摘要入库）
            news_ids = []
            urls = [anno['url'] for anno in annotations if 'url' in anno]
            if urls:
                placeholders = ','.join(['%s'] * len(urls))
                sql = f"SELECT id FROM news WHERE url IN ({placeholders})"
                cursor.execute(sql, tuple(urls))
                news_ids = [row[0] for row in cursor.fetchall()]

                for news_id in news_ids:
                    cursor.execute(
                        "INSERT IGNORE INTO summary_news_association (summary_id, news_id) VALUES (%s, %s)",
                        (summary_id, news_id)
                    )

            conn.commit()
            logger.info(f"成功插入摘要 ID={summary_id}，日期={today_bj}，关联了 {len(news_ids)} 条新闻。")

    except Exception as e:
        logger.error(f"处理摘要时发生错误: {e}")
        conn.rollback()
    finally:
        if conn.open:
            conn.close()

if __name__ == "__main__":
    process_summary_from_response()
