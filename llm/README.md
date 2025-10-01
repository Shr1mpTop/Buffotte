# LLM Multi-Agent Analysis Module

## 概述

本模块实现了一个专业的多Agent AI分析系统，模拟证券公司的分析团队工作流程。使用Google Gemini 2.0 Flash模型，通过三个专业Agent协同工作，提供全面的市场分析报告。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                  Analysis Workflow                   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │   📊 Data Analyst Agent         │
        │   - 分析历史30天数据            │
        │   - 评估预测模型准确性          │
        │   - 计算技术指标                │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │   📰 Market Analyst Agent       │
        │   - 搜集市场新闻                │
        │   - 分析利好利空因素            │
        │   - 评估市场情绪                │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │   💼 Fund Manager Agent         │
        │   - 综合所有分析报告            │
        │   - 制定投资策略                │
        │   - 生成最终建议                │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │   📄 Final Report               │
        │   - JSON报告                    │
        │   - HTML可视化报告              │
        │   - 邮件发送                    │
        └─────────────────────────────────┘
```

## Agent职责

### 1. 📊 数据分析师 (Data Analyst)
**角色定位**: 量化分析专家，专注于数据驱动的客观分析

**主要职责**:
- 分析历史30天的价格和交易量数据
- 计算关键统计指标（均值、波动率、趋势等）
- 评估预测模型的输出
- 识别技术支撑位和阻力位
- 提供基于数据的客观结论

**输出内容**:
- 市场概况摘要
- 技术指标分析
- 预测数据评估
- 风险因素识别
- 关键数据洞察（Top 5）

**Temperature**: 0.3（低温度，保持客观和一致性）

### 2. 📰 市场分析师 (Market Analyst)
**角色定位**: 市场情报专家，关注新闻和市场情绪

**主要职责**:
- 搜集BUFF、悠悠优品、Steam社区的最新动态
- 识别影响市场的利好和利空消息
- 分析竞争对手动态
- 评估市场情绪和舆情
- 提供投资建议倾向

**关注领域**:
- BUFF平台政策和活动
- 悠悠优品竞争动态
- Steam官方政策更新
- 热门游戏和饰品趋势
- 监管政策和行业风险

**输出内容**:
- 最新市场动态汇总
- 利好因素分析
- 利空因素分析
- 市场情绪评估（positive/neutral/negative）
- 交易信号（buy/sell/hold）

**Temperature**: 0.5（中等温度，平衡创造性和准确性）

### 3. 💼 基金经理 (Fund Manager)
**角色定位**: 决策者，综合所有信息做出最终投资建议

**主要职责**:
- 综合数据分析师和市场分析师的报告
- 评估多方信息，做出平衡决策
- 制定具体的投资策略
- 识别关键风险并制定风控措施
- 撰写专业的商业调研报告

**决策原则**:
- 数据驱动 + 市场敏感
- 明确的风险控制
- 具体可执行的建议
- 兼顾短期和长期

**输出内容**:
- 执行摘要（Executive Summary）
- 市场形势综合分析
- 投资策略建议（仓位、时机、止损止盈）
- 风险评估与管理方案
- 关键指标监控清单
- 明确的行动建议

**Temperature**: 0.4（偏低温度，保持专业和决断）

## 安装配置

### 1. 安装依赖

```bash
pip install google-generativeai pillow
```

或使用requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 获取Gemini API Key

1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 创建API Key
3. 设置环境变量：

**Windows PowerShell**:
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Linux/Mac**:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**永久设置（Windows）**:
```powershell
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your-api-key-here', 'User')
```

### 3. 配置文件

编辑 `llm_config.json`:

```json
{
  "llm": {
    "provider": "google",
    "model": "gemini-2.0-flash-exp",
    "api_key_env": "GEMINI_API_KEY",
    "temperature": {
      "data_analyst": 0.3,
      "market_analyst": 0.5,
      "fund_manager": 0.4
    }
  },
  "workflow": {
    "enable_news_search": false,
    "save_reports": true,
    "generate_html": true,
    "output_dir": "models"
  }
}
```

## 使用方式

### 方式1: 集成到日报告系统（推荐）

AI分析已自动集成到 `run_daily_report.py`：

```bash
python -m src.run_daily_report
```

脚本会自动：
1. 获取最新数据
2. 运行预测模型
3. 生成K线图
4. **运行AI多Agent分析** ⭐
5. 生成HTML报告
6. 发送邮件（包含AI分析结果）

### 方式2: 独立运行AI分析

```python
from llm.workflow import AnalysisWorkflow
import pandas as pd

# 准备数据
df = pd.read_csv('historical_data.csv')
predictions = [
    {'day': 1, 'predicted_daily_return': 0.005, 'direction': 'up'},
    # ...
]

# 初始化工作流
workflow = AnalysisWorkflow(model_name='gemini-2.0-flash-exp')

# 运行分析
results = workflow.run_full_analysis(
    historical_data=df,
    predictions=predictions,
    chart_path='chart.png',
    enable_news_search=False
)

# 保存报告
workflow.save_results(output_dir='models')
workflow.generate_html_report(output_dir='models')
```

## 输出文件

运行后会生成以下文件：

### 1. JSON报告
`models/ai_analysis_report.json`

包含所有Agent的完整分析结果（结构化数据）

### 2. HTML报告
`models/ai_analysis_report_YYYYMMDD_HHMMSS.html`

精美的可视化报告，包含：
- 投资建议卡片（Buy/Sell/Hold）
- 信心度评分
- 各Agent的详细报告
- 关键发现高亮显示

### 3. 邮件附件
- 预测K线图
- 预测JSON数据
- AI分析HTML报告
- AI分析JSON数据

## 报告示例

### 执行摘要示例
```
📊 投资建议: BUY
信心度: 75%

基于数据分析显示近期价格呈现上升趋势，市场情绪积极，
建议在当前价位适度建仓，目标涨幅5-8%，止损设置在-3%。
```

### 关键发现示例
```
🔍 关键发现：
• 30日均价上涨12.5%，呈现明确上升趋势
• 交易量较前期增长35%，市场活跃度提升
• 近5日价格突破重要阻力位，技术面转强
• 预测模型显示未来5天持续看涨信号
• 波动率处于合理区间，风险可控
```

## 自定义开发

### 添加新的Agent

1. 在 `llm/agents/` 创建新文件
2. 继承 `BaseAgent` 类
3. 实现必需方法：

```python
from llm.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def _build_system_instruction(self) -> str:
        return "你的系统指令..."
    
    def analyze(self, context: dict) -> dict:
        # 你的分析逻辑
        return {'report': '...', ...}
```

4. 在 `workflow.py` 中集成新Agent

### 自定义Prompt

编辑各Agent文件中的 `_build_system_instruction()` 和 `_build_analysis_prompt()` 方法。

### 添加真实新闻搜索

在 `market_analyst.py` 的 `_search_news()` 方法中实现：

```python
def _search_news(self, keywords):
    # 使用Google News API、Bing Search等
    # 或网页爬虫获取实时新闻
    pass
```

## 性能优化

### 1. 控制Token消耗
- 调整历史数据窗口大小（默认30天）
- 使用更小的模型（如gemini-1.5-flash）
- 缓存重复的分析结果

### 2. 并行处理
工作流当前是串行的，可以改进为：
- 数据分析师和市场分析师并行运行
- 使用异步API调用

### 3. 错误处理
- 所有Agent都有try-except保护
- API失败会回退到基础分析
- 日志记录所有错误

## 故障排除

### 问题1: ImportError: No module named 'google.generativeai'
**解决**: 
```bash
pip install google-generativeai
```

### 问题2: API Key未设置
**症状**: "GEMINI_API_KEY not set in environment"
**解决**: 设置环境变量（见上文配置部分）

### 问题3: API调用失败
**可能原因**:
- API Key无效
- 网络问题
- 配额超限

**解决**:
1. 检查API Key是否正确
2. 验证网络连接
3. 查看Google AI Studio的配额使用情况

### 问题4: 报告质量不佳
**优化建议**:
- 调整Agent的temperature参数
- 优化Prompt模板
- 增加更多历史数据
- 提供更详细的市场背景信息

## API成本估算

使用Gemini 2.0 Flash（免费额度）：
- 每次完整分析约消耗 8,000-12,000 tokens
- 免费额度：15 RPM (requests per minute)
- 每日运行一次：完全免费

如需升级到付费计划，成本极低（< $0.01/次）

## 最佳实践

1. **数据质量优先**: 确保历史数据准确完整
2. **定期review**: 每周review AI建议的准确性
3. **人工复核**: AI分析仅供参考，重要决策需人工审核
4. **持续优化**: 根据反馈不断优化Prompt
5. **风险控制**: 严格遵守AI建议中的止损策略

## 扩展方向

1. **情绪分析**: 集成社交媒体情绪分析
2. **技术指标**: 添加更多技术分析指标（RSI、MACD等）
3. **回测系统**: 评估AI建议的历史准确率
4. **实时监控**: 实时监控关键指标触发告警
5. **多市场支持**: 扩展到其他游戏饰品市场

## 许可和免责声明

本模块仅供学习和研究使用。AI生成的投资建议不构成专业金融建议，使用者需自行承担投资风险。

---

**技术支持**: 如有问题请提Issue或联系维护者
**更新日期**: 2025-10-02
**版本**: 1.0.0
