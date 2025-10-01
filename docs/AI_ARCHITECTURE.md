# AI多Agent分析系统 - 系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Buffotte Trading System                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐       ┌──────────────┐
│ Data Layer   │      │ Model Layer  │       │  LLM Layer   │
│              │      │              │       │              │
│ • Kline API  │──────│ • Training   │───────│ • AI Agents  │
│ • MySQL DB   │      │ • Prediction │       │ • Workflow   │
│ • Data ETL   │      │ • Evaluation │       │ • Reports    │
└──────────────┘      └──────────────┘       └──────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Output Layer       │
                    │                      │
                    │ • Charts             │
                    │ • Email Reports      │
                    │ • JSON/HTML Reports  │
                    └──────────────────────┘
```

## LLM Module详细架构

```
llm/
├── __init__.py                 # 模块初始化
│
├── clients/                    # LLM客户端层
│   ├── __init__.py
│   └── gemini_client.py       # Google Gemini API封装
│       ├── GeminiClient
│       ├── generate()          # 文本生成
│       ├── generate_with_images() # 图像+文本生成
│       └── chat()              # 多轮对话
│
├── agents/                     # Agent层（核心业务逻辑）
│   ├── __init__.py
│   ├── base_agent.py          # Agent基类
│   │   └── BaseAgent
│   │       ├── _build_system_instruction()
│   │       ├── analyze()
│   │       └── _generate_response()
│   │
│   ├── data_analyst.py        # 数据分析师Agent
│   │   └── DataAnalystAgent
│   │       ├── analyze()       # 分析历史数据和预测
│   │       ├── _build_analysis_prompt()
│   │       └── _extract_key_findings()
│   │
│   ├── market_analyst.py      # 市场分析师Agent
│   │   └── MarketAnalystAgent
│   │       ├── analyze()       # 分析市场新闻和情绪
│   │       ├── _search_news()  # 搜索新闻
│   │       ├── _extract_sentiment()
│   │       └── _extract_signals()
│   │
│   └── fund_manager.py        # 基金经理Agent
│       └── FundManagerAgent
│           ├── analyze()       # 生成最终投资建议
│           ├── _build_final_prompt()
│           ├── _extract_recommendation()
│           ├── _calculate_confidence()
│           ├── _extract_strategy()
│           └── _extract_risks()
│
├── workflow.py                 # 工作流编排器
│   └── AnalysisWorkflow
│       ├── run_full_analysis() # 运行完整分析流程
│       ├── _calculate_statistics()
│       ├── save_results()      # 保存JSON报告
│       └── generate_html_report() # 生成HTML报告
│
└── utils/                      # 工具函数（预留）
    └── __init__.py
```

## 数据流图

```
┌─────────────┐
│ Historical  │
│   Data      │ (30 days)
│  (MySQL)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ Prediction  │────▶│  Workflow    │
│   Model     │     │ Orchestrator │
│  (joblib)   │     └──────┬───────┘
└─────────────┘            │
       │                   │
       │                   ▼
       │         ┌─────────────────┐
       │         │  Data Analyst   │
       │         │     Agent       │
       │         └────────┬────────┘
       │                  │
       │         ┌────────▼────────┐
       │         │ Market Analyst  │
       │         │     Agent       │
       │         └────────┬────────┘
       │                  │
       ▼         ┌────────▼────────┐
   ┌───────┐    │  Fund Manager   │
   │ Chart │───▶│     Agent       │
   └───────┘    └────────┬────────┘
                         │
                         ▼
               ┌──────────────────┐
               │  Final Report    │
               │                  │
               │ • Recommendation │
               │ • Confidence     │
               │ • Strategy       │
               │ • Risk Analysis  │
               └──────────────────┘
```

## Agent工作流程

### Stage 1: 数据分析师

```
Input:
  • historical_data: DataFrame (30 days)
  • predictions: List[Dict] (5 days forecast)
  • statistics: Dict (calculated metrics)

Process:
  1. 分析历史价格趋势
  2. 计算技术指标 (MA, 波动率等)
  3. 评估预测合理性
  4. 识别关键转折点
  5. 提取数据洞察

Output:
  • report: str (结构化分析报告)
  • key_findings: List[str] (关键发现)
  • metrics: Dict (重要指标)
```

### Stage 2: 市场分析师

```
Input:
  • data_analyst_report: str
  • search_enabled: bool
  • keywords: List[str]

Process:
  1. 接收数据分析师报告
  2. 搜集市场新闻 (真实或模拟)
  3. 分析利好利空因素
  4. 评估市场情绪
  5. 生成交易信号

Output:
  • report: str (市场分析报告)
  • news_items: List[Dict] (新闻列表)
  • sentiment: str (positive/neutral/negative)
  • signals: Dict (buy/sell/hold信号)
```

### Stage 3: 基金经理

```
Input:
  • data_analyst_report: Dict
  • market_analyst_report: Dict
  • chart_path: str (K线图路径)
  • historical_data: DataFrame

Process:
  1. 接收所有分析报告
  2. 综合数据面和消息面
  3. 结合K线图进行视觉分析
  4. 制定投资策略
  5. 评估风险并设定止损止盈
  6. 生成最终建议

Output:
  • report: str (最终投资报告)
  • recommendation: str (buy/sell/hold)
  • confidence: float (信心度 0-1)
  • strategy: Dict (详细策略)
  • risk_assessment: Dict (风险评估)
```

## API调用流程

```
┌──────────────┐
│   Workflow   │
│   starts     │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ GeminiClient.generate│
│ with system_instruction
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Gemini API          │
│  (gemini-2.0-flash)  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Parse response      │
│  Extract structured  │
│  data                │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Return to workflow  │
└──────────────────────┘
```

## 配置系统

```
llm_config.json
│
├── llm
│   ├── provider: "google"
│   ├── model: "gemini-2.0-flash-exp"
│   ├── api_key_env: "GEMINI_API_KEY"
│   └── temperature
│       ├── data_analyst: 0.3    (低温度→客观)
│       ├── market_analyst: 0.5   (中温度→平衡)
│       └── fund_manager: 0.4     (中低温度→决断)
│
└── workflow
    ├── enable_news_search: false
    ├── save_reports: true
    ├── generate_html: true
    └── output_dir: "models"
```

## 报告生成流程

```
Analysis Results (Python Dict)
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             ▼
   JSON File    HTML File    Email Attachment
   │             │             │
   │             │             │
   ▼             ▼             ▼
models/       models/        SMTP Server
ai_analysis  ai_analysis     │
_report.json _report*.html   ▼
                            User's Email
```

## 扩展点

系统设计了多个扩展点，便于定制：

### 1. 添加新Agent
```python
# llm/agents/your_agent.py
class YourAgent(BaseAgent):
    def _build_system_instruction(self):
        return "Your custom instruction..."
    
    def analyze(self, context):
        # Your analysis logic
        return {...}
```

### 2. 自定义Workflow
```python
# 修改 llm/workflow.py
def run_custom_analysis(self, ...):
    # Stage 1: Your agent
    result1 = self.your_agent.analyze(...)
    # Stage 2: Another agent
    result2 = self.another_agent.analyze(...)
    # ...
```

### 3. 集成其他LLM
```python
# llm/clients/openai_client.py
class OpenAIClient:
    def generate(self, prompt, ...):
        # OpenAI API implementation
        pass
```

### 4. 添加数据源
```python
# llm/agents/market_analyst.py
def _search_real_news(self):
    # 实现真实新闻搜索
    # - Google News API
    # - Web Scraping
    # - RSS Feeds
    pass
```

## 性能优化

### Token消耗优化
- 使用更小的模型（gemini-1.5-flash）
- 限制历史数据窗口
- 压缩prompt长度
- 缓存重复分析

### 响应时间优化
- 并行运行独立agent
- 使用异步API调用
- 预加载数据
- 批量处理

### 成本优化
- 使用免费额度（15 RPM）
- 只在必要时运行AI分析
- 复用历史分析结果
- 设置合理的调用频率

## 安全考虑

1. **API Key安全**
   - 使用环境变量
   - 不要提交到Git
   - 使用密钥管理服务

2. **数据隐私**
   - 不发送敏感个人信息
   - 注意数据脱敏
   - 遵守数据保护法规

3. **错误处理**
   - 所有API调用有异常捕获
   - 失败时回退到基础分析
   - 详细的错误日志

4. **速率限制**
   - 遵守API配额
   - 实现重试机制
   - 避免频繁调用

---

**Last Updated**: 2025-10-02
**Version**: 1.0.0
