from openai import OpenAI
import os

# 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
api_key = "b9aaf372-7788-42f0-9966-10b2ee5d588e"
client = OpenAI(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=api_key
)

tools = [{
    "type": "web_search",
    "sources": ["douyin", "toutiao"]
}]

prompt = """
你是一名目光敏锐的cs2自媒体咨询人，同时也会在虚拟游戏饰品市场进行小投资，请参考以下一个或多个可靠信源：
1. 抖音搜索 (https://www.douyin.com/search/CS2%E9%A5%B0%E5%93%81%E6%9C%80%E6%96%B0)
2. Steam游戏cs2更新资讯 (https://store.steampowered.com/news/app/730/view)
3. 网易BUFF资讯 (https://buff.163.com/news/?news_game=csgo)
4. HLTV比赛赛事最新资讯 (https://www.hltv.org/)
5. 其他抖音、头条等平台。

尽量找到“最近一周”的CS2饰品市场的最新资讯。请注意，需要筛选出可能会影响饰品价格的新闻资讯。然后，请像情报专家一样，敏锐地分析其中的信息流、影响，并预测未来走势，最后进行总结。"""

response = client.responses.create(
    model="doubao-seed-1-6-flash-250828",
    input=[{"role": "user", "content": prompt}],
    tools=tools,
)

print(response)

# 将响应保存到 txt 文件
output_filename = "./llm/response.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(response.model_dump_json(indent=2))
print(f"API 响应已保存到 {output_filename}")