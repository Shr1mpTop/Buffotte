# AI市场分析模块（简洁版）

## 概述

这个模块提供简单、清晰、易懂的市场分析报告。

### 核心特点

- ✅ **基于真实数据**: 所有指标都是真实计算，不依赖LLM生成
- ✅ **通俗易懂**: 避免专业术语，像朋友聊天一样
- ✅ **快速高效**: 10-20秒完成分析
- ✅ **一目了然**: 3秒看懂核心观点

## 文件结构

```
llm/
├── simple_workflow.py          # 简洁分析器（主要逻辑）
├── simple_report_builder.py    # 报告生成器
├── clients/                    # LLM客户端
│   ├── gemini_client.py       # Google Gemini
│   └── doubao_client.py       # 字节豆包
└── README.md
```

## 使用方法

```python
from llm.simple_workflow import SimpleMarketAnalyzer

# 初始化
analyzer = SimpleMarketAnalyzer(llm_config)

# 运行分析
result = analyzer.analyze(
    historical_data=df,
    predictions=predictions,
    chart_path='chart.png'
)

# 获取报告
print(result['report'])
```

## 配置说明

编辑 `llm_config.json`：

```json
{
  "llm": {
    "provider": "google",
    "model": "gemini-2.0-flash-exp",
    "api_key": "your-api-key",
    "temperature": 0.3
  }
}
```
