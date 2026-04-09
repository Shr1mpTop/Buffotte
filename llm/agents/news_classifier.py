"""
新闻分类 Agent
使用豆包模型对未分类的新闻进行自动分类。
分类结果以 JSON 格式输出，直接写入 news.category 字段。
"""
import os
import json
import logging
import pymysql
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

# ─── 分类定义 ─────────────────────────────────────────────────
CATEGORIES = [
    "赛事动态",   # 电竞赛事、比赛结果、转会消息
    "版本更新",   # Valve 更新、游戏补丁、新功能
    "市场行情",   # 饰品价格波动、市场分析、投资建议
    "饰品资讯",   # 新皮肤发布、开箱、合成系统
    "社区热点",   # 社区讨论、争议事件、玩家反馈
    "其他",       # 不属于以上分类
]

SYSTEM_PROMPT = """你是一个 CS2 饰品与电竞领域的新闻分类专家。

你将收到一组新闻条目（JSON 数组），每条包含 id、title、preview（摘要）。
请为每条新闻分配一个最合适的分类。

可用的分类有：
- 赛事动态：电竞赛事、比赛结果、选手转会、战队新闻
- 版本更新：Valve 官方更新、游戏补丁、新功能上线、反作弊更新
- 市场行情：饰品价格波动、交易数据分析、投资策略、平台政策
- 饰品资讯：新皮肤发布、开箱概率、武器箱更新、合成/汰换系统
- 社区热点：社区讨论与争议、Mod/创意工坊、主播/内容创作者动态
- 其他：不属于以上任何分类

严格按以下 JSON 格式输出（禁止 markdown 代码块标记）：
[{"id": 1, "category": "分类名"}, {"id": 2, "category": "分类名"}, ...]
"""


def get_db_connection():
    load_dotenv()
    return pymysql.connect(
        host=os.getenv('HOST'),
        port=int(os.getenv('PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DATABASE'),
        charset=os.getenv('CHARSET')
    )


def _get_uncategorized_news(conn, limit=50):
    """获取尚未分类的新闻。"""
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT id, title, summary as preview FROM news "
            "WHERE category IS NULL OR category = '' "
            "ORDER BY id DESC LIMIT %s",
            (limit,)
        )
        return cursor.fetchall()


def _call_classifier(news_items: list) -> list:
    """调用豆包模型对新闻进行分类。"""
    load_dotenv()
    api_key = os.getenv("ARK_API_KEY")
    models_str = os.getenv("DOUBAO_MODEL", "").strip('[]')
    # 使用 flash 模型（第二个）进行分类，更快更便宜
    models = [m.strip() for m in models_str.split(',') if m.strip()]
    model_name = models[-1] if len(models) > 1 else models[0]

    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )

    # 构造输入：只传必要字段，节省 token
    input_data = [
        {"id": n["id"], "title": n["title"], "preview": (n.get("preview") or "")[:120]}
        for n in news_items
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    # 清理可能的 markdown 代码块标记
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    return json.loads(raw)


def _update_categories(conn, classifications: list):
    """将分类结果批量写入数据库。"""
    valid = [c for c in classifications if c.get("category") in CATEGORIES]
    if not valid:
        logger.warning("没有有效的分类结果")
        return 0

    with conn.cursor() as cursor:
        for item in valid:
            cursor.execute(
                "UPDATE news SET category = %s WHERE id = %s",
                (item["category"], item["id"])
            )
    conn.commit()
    logger.info("已更新 %d 条新闻的分类", len(valid))
    return len(valid)


def ensure_category_column(conn):
    """确保 news 表有 category 字段。"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'news' AND COLUMN_NAME = 'category'",
            (os.getenv('DATABASE'),)
        )
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE news ADD COLUMN category VARCHAR(32) DEFAULT NULL "
                "COMMENT '新闻分类' AFTER summary"
            )
            cursor.execute("CREATE INDEX idx_news_category ON news (category)")
            conn.commit()
            logger.info("已为 news 表添加 category 列和索引")


def run_classifier(batch_size=30):
    """
    主入口：获取未分类新闻 → 调用 LLM 分类 → 写回 DB。
    分批处理以防单次请求过大。
    """
    conn = get_db_connection()
    try:
        ensure_category_column(conn)
        total_updated = 0

        while True:
            uncategorized = _get_uncategorized_news(conn, limit=batch_size)
            if not uncategorized:
                logger.info("没有更多未分类新闻")
                break

            logger.info("正在分类 %d 条新闻...", len(uncategorized))
            try:
                results = _call_classifier(uncategorized)
                count = _update_categories(conn, results)
                total_updated += count
            except Exception as e:
                logger.error("分类请求失败: %s", e)
                break

        logger.info("分类完成，共更新 %d 条", total_updated)
        return total_updated
    finally:
        if conn.open:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_classifier()
