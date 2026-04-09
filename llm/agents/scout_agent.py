import os
import json
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


# 默认搜索话题配置
DEFAULT_SEARCH_TOPICS = [
    {
        "name": "CS2饰品市场动态",
        "prompt": "请搜索最近3天的CS2饰品市场最新资讯，重点关注：1)可能影响饰品价格的新闻 2)职业选手相关动态 3)Valve在CS2市场的规则修改 4)CS2最新赛事结果 5)游戏更新内容。搜索完成后，请就事论事地总结这些新闻，每条新闻包含标题、来源和内容摘要。",
        "sources": ["douyin", "toutiao"],
    },
    {
        "name": "CS2皮肤价格异动",
        "prompt": "请搜索最近3天CS2皮肤/饰品价格的重大变化信息，包括：1)价格暴涨暴跌的饰品 2)新发布的皮肤 3)绝版/稀有饰品的市场动态 4)Steam市场或BUFF平台的交易异常。搜索完成后，请总结价格变化及其原因。",
        "sources": ["douyin", "toutiao"],
    },
    {
        "name": "CS2赛事与更新",
        "prompt": "请搜索最近一周CS2相关的重大赛事结果和游戏更新信息，包括：1)Major赛事进展 2)游戏平衡性更新 3)新箱子/新皮肤发布 4)职业选手转会或退役。搜索完成后，请总结这些信息及其对饰品市场的可能影响。",
        "sources": ["douyin", "toutiao"],
    },
]


class ScoutAgent:
    """
    Scout Agent（侦察代理）：使用 Doubao Responses API + web_search 进行广域搜索。
    
    职责：
    1. 使用 web_search 工具搜索 CS2 饰品相关新闻
    2. 将原始响应 JSON 持久化到 llm/responses/ 目录
    3. 调用 news_processor 持久化新闻标注
    4. 调用 summary_processor 持久化摘要
    5. 返回响应数据供 Parser Agent 处理
    """

    def __init__(self, model: str = None):
        api_key = os.getenv("ARK_API_KEY")
        if not api_key:
            raise ValueError("未配置 ARK_API_KEY，请在 .env 中设置")

        # 默认使用 flash 模型（更快、更便宜）
        if model is None:
            models_str = os.getenv("DOUBAO_MODEL", "").strip('[]')
            models = [m.strip() for m in models_str.split(',')]
            # 优先使用 flash 模型
            model = next((m for m in models if 'flash' in m), models[0] if models else 'doubao-seed-1-6-flash-250828')

        self.model = model
        self.client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )

        # 确保响应存储目录存在
        self.responses_dir = os.path.join(os.path.dirname(__file__), '..', 'responses')
        os.makedirs(self.responses_dir, exist_ok=True)

    def search(self, topic: dict = None, max_keyword: int = 4,
               max_tool_calls: int = 3, limit: int = 10) -> dict:
        """
        执行一次搜索任务。
        
        Args:
            topic: 搜索话题配置，包含 name, prompt, sources。
                   如果为 None，使用默认的第一个话题。
            max_keyword: 最大搜索关键词数（1~50，建议1~10）。
            max_tool_calls: 最大工具调用轮次（1~10，默认3）。
                           限制模型搜索轮次，达到上限后模型将生成最终回答。
            limit: 单轮搜索返回的最大结果条数（1~50，默认10）。
        
        Returns:
            包含 response_data, filepath, references 的字典。
        """
        if topic is None:
            topic = DEFAULT_SEARCH_TOPICS[0]

        tools = [{
            "type": "web_search",
            "sources": topic.get("sources", ["douyin", "toutiao"]),
            "max_keyword": max_keyword,
            "limit": limit,
        }]

        logger.info(f"[Scout] 正在搜索: {topic['name']} (模型: {self.model}, max_tool_calls={max_tool_calls})")

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": topic["prompt"]}],
                tools=tools,
                max_tool_calls=max_tool_calls,
            )
        except Exception as e:
            logger.error(f"[Scout] API 调用失败: {e}")
            return {"error": str(e)}

        # 序列化响应
        response_data = json.loads(response.model_dump_json(indent=2))

        # 持久化原始响应
        filepath = self._save_response(response_data, topic["name"])

        # 健康检查
        health = self._check_response_health(response_data)
        if not health['has_message']:
            logger.warning(f"[Scout] 响应异常: 无 message 输出 (搜索{health['web_search_count']}轮, "
                  f"function_call={health['has_function_call']})")
            if health['has_function_call']:
                logger.warning(f"[Scout] 模型试图继续搜索但被截断，建议增大 max_tool_calls 或简化 prompt")

        # 提取引用信息
        references = self._extract_references(response_data)

        # 提取摘要文本（即使没有 annotations 也有价值）
        summary_text = self._extract_summary_text(response_data)

        logger.info(f"[Scout] 搜索完成: 找到 {len(references)} 条引用, "
              f"摘要长度: {len(summary_text) if summary_text else 0} 字符")
        logger.info(f"[Scout] 响应已保存: {filepath}")

        return {
            "response_data": response_data,
            "filepath": filepath,
            "references": references,
            "summary_text": summary_text,
            "health": health,
        }

    def search_all_topics(self, topics: list = None, max_keyword: int = 4,
                          max_tool_calls: int = 3, limit: int = 10) -> list[dict]:
        """
        执行所有话题的搜索。
        
        Args:
            topics: 话题列表，如果为 None 使用默认话题。
            max_keyword: 最大搜索关键词数。
            max_tool_calls: 最大工具调用轮次（1~10）。
            limit: 单轮搜索返回的最大结果条数。
        
        Returns:
            所有搜索结果的列表。
        """
        if topics is None:
            topics = DEFAULT_SEARCH_TOPICS

        results = []
        for i, topic in enumerate(topics):
            logger.info(f"[Scout] === 话题 {i+1}/{len(topics)}: {topic['name']} ===")
            result = self.search(topic, max_keyword=max_keyword,
                                 max_tool_calls=max_tool_calls, limit=limit)
            results.append(result)

        return results

    def _save_response(self, response_data: dict, topic_name: str) -> str:
        """将响应 JSON 保存到文件，文件名包含时间戳和话题名。"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理话题名中的特殊字符
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in topic_name)
        filename = f"scout_{safe_name}_{timestamp}.json"
        filepath = os.path.join(self.responses_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)

        return filepath

    @staticmethod
    def _extract_references(response_data: dict) -> list[dict]:
        """从 Doubao Responses API 响应中提取 url_citation 标注。"""
        references = []
        for item in response_data.get('output', []):
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
                                    'summary': annotation.get('summary'),
                                })
        return references

    @staticmethod
    def _check_response_health(response_data: dict) -> dict:
        """
        检查响应的健康状态。
        
        Returns:
            包含 is_healthy, has_message, has_function_call, web_search_count 的字典。
        """
        output = response_data.get('output', [])
        has_message = any(item.get('type') == 'message' for item in output)
        has_function_call = any(item.get('type') == 'function_call' for item in output)
        web_search_count = sum(1 for item in output if item.get('type') == 'web_search_call')

        return {
            'is_healthy': has_message and not has_function_call,
            'has_message': has_message,
            'has_function_call': has_function_call,
            'web_search_count': web_search_count,
        }

    @staticmethod
    def _extract_summary_text(response_data: dict) -> str | None:
        """从响应中提取摘要文本（优先 message，其次 reasoning）。"""
        for item in response_data.get('output', []):
            if item.get('type') == 'message':
                content = item.get('content', [])
                if content:
                    return content[0].get('text')
        # 降级：从 reasoning 中提取
        for item in response_data.get('output', []):
            if item.get('type') == 'reasoning':
                summary = item.get('summary', [])
                if summary:
                    return summary[0].get('text')
        return None

    def process_to_db(self, result: dict):
        """
        将搜索结果持久化到数据库（新闻 + 摘要）。
        
        Args:
            result: search() 方法返回的结果字典。
        """
        from db.news_processor import NewsProcessor
        from db.summary_processor import create_tables, get_db_connection

        references = result.get('references', [])
        response_data = result.get('response_data', {})
        summary_text = result.get('summary_text')

        # 持久化新闻引用
        if references:
            with NewsProcessor() as processor:
                if processor.conn:
                    processor.create_table_if_not_exists()
                    processor.insert_or_update_news(references)
                    logger.info(f"[Scout] 已持久化 {len(references)} 条新闻引用")

        # 持久化摘要
        annotations = []
        for item in response_data.get('output', []):
            if item.get('type') == 'message':
                content = item.get('content', [])
                if content:
                    annotations = content[0].get('annotations', [])
                    break

        if summary_text:
            conn = get_db_connection()
            try:
                create_tables(conn)
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO summary (summary) VALUES (%s)", (summary_text,))
                    summary_id = cursor.lastrowid

                    # 仅当有 annotations 时才关联新闻
                    if annotations:
                        urls = [anno['url'] for anno in annotations if 'url' in anno]
                        if urls:
                            sql = "SELECT id FROM news WHERE url IN ({})".format(
                                ','.join(['%s'] * len(urls))
                            )
                            cursor.execute(sql, tuple(urls))
                            news_ids = [item[0] for item in cursor.fetchall()]

                            for news_id in news_ids:
                                cursor.execute(
                                    "INSERT INTO summary_news_association (summary_id, news_id) VALUES (%s, %s)",
                                    (summary_id, news_id)
                                )

                        conn.commit()
                        logger.info(f"[Scout] 已持久化摘要 ID: {summary_id}，关联 {len(news_ids) if urls else 0} 条新闻")
                    else:
                        conn.commit()
                        logger.info(f"[Scout] 已持久化摘要 ID: {summary_id}（无 annotations 关联）")
            except Exception as e:
                logger.error(f"[Scout] 持久化摘要失败: {e}")
                conn.rollback()
            finally:
                if conn.open:
                    conn.close()


def run_scout(topic_index: int = None):
    """
    运行 Scout Agent 的便捷函数。
    
    Args:
        topic_index: 指定话题索引（0-based），None 表示搜索所有话题。
    """
    agent = ScoutAgent()

    if topic_index is not None:
        if topic_index < 0 or topic_index >= len(DEFAULT_SEARCH_TOPICS):
            logger.error(f"无效的话题索引: {topic_index}，共 {len(DEFAULT_SEARCH_TOPICS)} 个话题")
            return
        result = agent.search(DEFAULT_SEARCH_TOPICS[topic_index])
        agent.process_to_db(result)
        return result
    else:
        results = agent.search_all_topics()
        for result in results:
            if 'error' not in result:
                agent.process_to_db(result)
        return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1])
            run_scout(idx)
        except ValueError:
            logger.info("用法: python scout_agent.py [话题索引]")
            logger.info(f"可用话题: {[t['name'] for t in DEFAULT_SEARCH_TOPICS]}")
    else:
        run_scout()
