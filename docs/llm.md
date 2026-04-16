# AI 分析系统

## 概述

Buffotte 的 AI 系统由两部分组成：

1. **新闻分析流水线** — 基于 LLM Agent 的三阶段流水线，自动发现、提取、分析 CS2 饰品相关新闻
2. **大盘分析** — 每日通过豆包 LLM 生成市场行情解读

## 新闻分析流水线

### 架构

```
Scout Agent ──▶ Parser Agent ──▶ Investigator Agent
  (搜索发现)      (实体提取)       (深入分析)
```

### Phase 1: Scout Agent (`scout_agent.py`)

**职责**: 从多信息源搜索 CS2 饰品相关新闻

**信息源**:
- 网易 BUFF 资讯 (`buff.163.com/news`)
- HLTV 赛事资讯 (`hltv.org`)
- 抖音搜索 (`douyin.com`)
- 搜索引擎关键词检索（"CS2 职业选手退役"、"CS 绝版饰品"、"CS2 重大更新"等）

**输出**: 结构化的搜索结果，包含新闻 URL、标题、摘要

### Phase 2: Parser Agent (`skin_parser.py`)

**职责**: 从搜索结果中提取饰品实体

**处理逻辑**:
1. 识别文本中的 CS2 饰品名称
2. 匹配或创建饰品实体记录
3. 建立新闻-饰品关联关系

**输出**: 提取的饰品实体列表 + 创建的调查任务

### Phase 3: Investigator Agent (`skin_investigator.py`)

**职责**: 对提取出的饰品进行深入调查分析

**处理逻辑**:
1. 获取饰品历史价格数据
2. 结合新闻事件分析价格影响
3. 生成投资建议和市场观点

**输出**: 饰品调查报告

### Orchestrator (`orchestrator.py`)

流水线调度器，串联三个 Agent 阶段，支持：

```bash
# 完整流水线
python llm/orchestrator.py

# 跳过 Scout 阶段（使用已有数据调试）
python llm/orchestrator.py --skip-scout --scout-file path/to/file.json

# 自定义 Investigator 批次大小
python llm/orchestrator.py --investigator-batch 20
```

## 大盘分析 (`market_analysis_processor.py`)

每日自动运行，生成市场分析报告：

1. 从数据库获取最近的 K 线数据和新闻
2. 构造 prompt 发送给豆包 LLM
3. LLM 返回结构化的市场分析文本
4. 存入数据库供前端展示

## 新闻分类 (`news_classifier.py`)

对爬取的新闻自动分类，支持以下类别：

| 分类 | 说明 |
|------|------|
| 游戏更新 | CS2 客户端/服务端更新公告 |
| 赛事资讯 | Major、BLAST 等赛事新闻 |
| 职业选手 | 选手转会、退役等动态 |
| 市场动态 | 饰品价格波动、市场政策变化 |
| 装备推荐 | 饰品评测、搭配推荐 |

## LLM 客户端

使用 OpenAI SDK 接入豆包大模型：

```python
from llm.clients.doubao_client import DoubaoClient

client = DoubaoClient()
response = client.chat("分析今日 CS2 市场走势...")
```

**环境变量**:
- `ARK_API_KEY` — 豆包 API 密钥
- `DOUBAO_MODEL` — 模型 endpoint ID

## 自动化调度

通过 `scripts/daily_automation.sh` 每日 07:00 (北京时间) 自动执行：

```bash
# 完整每日流程
1. 新闻爬取 (llm/test.py)
2. 新闻入库解析 (db/news_processor.py)
3. AI 摘要生成 (db/summary_processor.py)
4. 大盘分析 (db/market_analysis_processor.py)
```

失败自动重试，直到成功获取有参考价值的新闻数据。
