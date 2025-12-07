from langchain_openai import ChatOpenAI
import os

def DoubaoChat(model: str, **kwargs):
    """
    一个辅助函数，用于快速初始化一个针对火山方舟豆包模型的 LangChain 客户端。
    """
    api_key = os.getenv("ARK_API_KEY")
    base_url = "https://ark.cn-beijing.volces.com/api/v3"

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
