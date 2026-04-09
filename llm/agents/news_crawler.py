import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def run_news_crawler_workflow():
    """
    执行新闻抓取的工作流：加载配置 -> 读取 Prompt -> 调用模型 -> 打印结果。
    """
    # 1. 加载配置
    load_dotenv()
    api_key = os.getenv("ARK_API_KEY")
    models_str = os.getenv("DOUBAO_MODEL", "").strip('[]')
    model_name = models_str.split(',')[0].strip() # 默认使用列表中的第一个模型

    if not api_key or not model_name:
        logger.error("错误: 请确保 .env 文件中已配置 ARK_API_KEY 和有效的 DOUBAO_MODEL。")
        return

    # 2. 读取 Prompt
    try:
        current_dir = os.path.dirname(__file__)
        prompt_path = os.path.join(current_dir, 'News_Scratcher.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error(f"错误: Prompt 文件未在 '{prompt_path}' 找到。")
        return

    # 3. 初始化客户端
    try:
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
    except Exception as e:
        logger.error(f"初始化 OpenAI 客户端时出错: {e}")
        return

    # 4. 调用模型
    # 我们将 Prompt.md 的内容作为 system message，并将具体任务作为 user message
    user_task = "请帮我搜索 CS2 饰品相关的最新信息。"
    
    logger.info(f"正在使用模型 '{model_name}' 执行任务")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_task,
                }
            ]
        )

        if response.choices:
            content = response.choices[0].message.content
            logger.info(f"模型回复: {content[:200]}...")
        else:
            logger.warning("未能从响应中提取到有效的回复内容")

    except Exception as e:
        logger.error(f"请求失败: {e}")

if __name__ == "__main__":
    run_news_crawler_workflow()
