# AI多Agent分析系统 - 使用示例

## 示例1: 完整的日常工作流

```powershell
# 1. 设置API Key（首次使用）
$env:GEMINI_API_KEY = "your-api-key-here"

# 2. 运行完整的日报告（包含AI分析）
python -m src.run_daily_report
```

**预期输出**:
```
Inserted rows: 450
Inserted 90 rows for 2025-09-30 23:55:10 Shanghai
...

============================================================
🤖 Starting AI Multi-Agent Analysis...
============================================================

============================================================
🤖 启动多Agent AI分析工作流
============================================================

[1/3] 📊 数据分析师正在分析历史数据和预测...
✓ 数据分析完成 - 识别 5 个关键发现

[2/3] 📰 市场分析师正在分析市场动态和新闻...
✓ 市场分析完成 - 情绪: positive

[3/3] 💼 基金经理正在综合分析并制定投资策略...
✓ 投资建议生成完成 - 建议: BUY
  信心度: 75%

============================================================
✅ 多Agent分析工作流完成
============================================================

💾 分析结果已保存至: models/ai_analysis_report.json
📄 HTML报告已生成: models/ai_analysis_report_20251002_120000.html

Email sent to your@email.com
```

## 示例2: 独立运行AI分析

```python
# test_custom_analysis.py
from llm.workflow import AnalysisWorkflow
import pandas as pd
import json

# 1. 准备数据
df = pd.read_sql('SELECT * FROM kline_data_day ORDER BY timestamp DESC LIMIT 30', engine)

predictions = [
    {'day': 1, 'predicted_daily_return': 0.008, 'direction': 'up'},
    {'day': 2, 'predicted_daily_return': 0.012, 'direction': 'up'},
    {'day': 3, 'predicted_daily_return': 0.005, 'direction': 'up'},
    {'day': 4, 'predicted_daily_return': -0.003, 'direction': 'down'},
    {'day': 5, 'predicted_daily_return': 0.002, 'direction': 'up'},
]

# 2. 初始化工作流
workflow = AnalysisWorkflow(model_name='gemini-2.0-flash-exp')

# 3. 运行分析
results = workflow.run_full_analysis(
    historical_data=df,
    predictions=predictions,
    chart_path='models/chart.png',
    enable_news_search=False  # 使用模拟新闻
)

# 4. 查看结果
print(f"投资建议: {results['summary']['recommendation']}")
print(f"信心度: {results['summary']['confidence']*100:.0f}%")
print(f"市场情绪: {results['summary']['market_sentiment']}")

# 5. 保存报告
workflow.save_results(output_dir='models')
html_path = workflow.generate_html_report(output_dir='models')
print(f"HTML报告: {html_path}")
```

## 示例3: 只运行特定Agent

```python
from llm.clients.gemini_client import GeminiClient
from llm.agents.data_analyst import DataAnalystAgent

# 初始化客户端
client = GeminiClient(model_name='gemini-2.0-flash-exp')

# 只创建数据分析师
analyst = DataAnalystAgent(client=client)

# 准备上下文
context = {
    'historical_data': df,
    'predictions': predictions,
    'statistics': {'current_price': 105.5, 'volatility': 0.02}
}

# 运行分析
result = analyst.analyze(context)

print("数据分析报告:")
print(result['report'])
print("\n关键发现:")
for finding in result['key_findings']:
    print(f"• {finding}")
```

## 示例4: 自定义Agent温度

```python
from llm.workflow import AnalysisWorkflow

workflow = AnalysisWorkflow()

# 调整单个Agent的温度
workflow.data_analyst.temperature = 0.2    # 更保守
workflow.market_analyst.temperature = 0.7  # 更有创造性
workflow.fund_manager.temperature = 0.3    # 更谨慎

results = workflow.run_full_analysis(...)
```

## 示例5: 带图像分析的基金经理

```python
from llm.clients.gemini_client import GeminiClient
from llm.agents.fund_manager import FundManagerAgent

client = GeminiClient()
manager = FundManagerAgent(client=client)

# 包含图表路径的上下文
context = {
    'data_analyst_report': {...},
    'market_analyst_report': {...},
    'chart_path': 'models/prediction_chart.png',  # 自动包含图像分析
    'historical_data': df
}

result = manager.analyze(context)
print(result['report'])
```

## 示例6: 解析JSON报告

```python
import json

# 读取AI分析报告
with open('models/ai_analysis_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# 提取关键信息
data_report = report['data_analyst']
market_report = report['market_analyst']
final_report = report['fund_manager']

print(f"数据分析师关键发现:")
for finding in data_report['key_findings']:
    print(f"  • {finding}")

print(f"\n市场情绪: {market_report['sentiment']}")
print(f"交易信号: {market_report['signals']}")

print(f"\n最终建议: {final_report['recommendation']}")
print(f"信心度: {final_report['confidence']*100:.0f}%")
print(f"风险评估: {final_report['risk_assessment']}")
```

## 示例7: 添加自定义Agent

```python
# llm/agents/risk_manager.py
from llm.agents.base_agent import BaseAgent

class RiskManagerAgent(BaseAgent):
    """风险管理专家Agent"""
    
    def __init__(self, client, temperature=0.2):
        super().__init__(
            name="风险管理师",
            role="Risk Manager",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self):
        return """你是一名专业的风险管理师，专注于识别和评估投资风险。
        
你的职责：
1. 识别市场风险、流动性风险、政策风险
2. 量化风险敞口
3. 制定风险缓解措施
4. 设定止损止盈点位
5. 提供风险控制建议

请提供专业的风险评估报告。
"""
    
    def analyze(self, context):
        # 构建风险分析prompt
        data_report = context.get('data_analyst_report', '')
        market_report = context.get('market_analyst_report', '')
        
        prompt = f"""基于以下分析，进行风险评估：

数据分析：
{data_report}

市场分析：
{market_report}

请识别主要风险因素，并提供风险控制建议。
"""
        
        report = self._generate_response(prompt)
        
        return {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'risk_level': self._assess_risk_level(report)
        }
    
    def _assess_risk_level(self, report):
        # 简单的风险等级评估
        if '高风险' in report or '严重' in report:
            return 'high'
        elif '中等风险' in report:
            return 'medium'
        else:
            return 'low'


# 在workflow中使用
from llm.workflow import AnalysisWorkflow

class CustomWorkflow(AnalysisWorkflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加风险管理师
        self.risk_manager = RiskManagerAgent(client=self.client)
    
    def run_full_analysis(self, *args, **kwargs):
        # 先运行标准分析
        results = super().run_full_analysis(*args, **kwargs)
        
        # 再运行风险评估
        risk_context = {
            'data_analyst_report': results['data_analyst']['report'],
            'market_analyst_report': results['market_analyst']['report']
        }
        risk_result = self.risk_manager.analyze(risk_context)
        
        # 添加到结果中
        results['risk_manager'] = risk_result
        results['summary']['risk_assessment'] = risk_result['risk_level']
        
        return results
```

## 示例8: 批量分析多个时间段

```python
from datetime import datetime, timedelta
import pandas as pd

def analyze_historical_periods(days_back=90, window=30):
    """分析历史多个时间段，评估AI准确性"""
    
    workflow = AnalysisWorkflow()
    results = []
    
    for i in range(0, days_back, window):
        # 获取该时间段的数据
        end_date = datetime.now() - timedelta(days=i)
        start_date = end_date - timedelta(days=window)
        
        df = load_data_for_period(start_date, end_date)
        predictions = get_predictions_for_date(end_date)
        
        # 运行分析
        analysis = workflow.run_full_analysis(
            historical_data=df,
            predictions=predictions,
            chart_path=None,
            enable_news_search=False
        )
        
        results.append({
            'period': f"{start_date.date()} to {end_date.date()}",
            'recommendation': analysis['summary']['recommendation'],
            'confidence': analysis['summary']['confidence'],
            'actual_outcome': get_actual_outcome(end_date)  # 需要实现
        })
    
    # 分析准确率
    accuracy = calculate_accuracy(results)
    print(f"AI建议历史准确率: {accuracy*100:.1f}%")
    
    return results
```

## 示例9: 集成到自动化任务

```python
# daily_automation.py
import os
import sys
from datetime import datetime

def main():
    """每日自动运行的脚本"""
    
    print(f"[{datetime.now()}] 开始每日分析...")
    
    # 1. 检查环境
    if not os.getenv('GEMINI_API_KEY'):
        print("错误: API Key未设置")
        return 1
    
    # 2. 运行完整流程
    try:
        from src.run_daily_report import main as run_report
        run_report()
        print(f"[{datetime.now()}] 分析完成")
        return 0
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
```

**Windows计划任务配置**:
```powershell
# 注册每日任务
$action = New-ScheduledTaskAction -Execute "python" -Argument "E:\github\Buffotte\daily_automation.py" -WorkingDirectory "E:\github\Buffotte"
$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "Buffotte_AI_Analysis" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM"
```

## 示例10: 错误处理和重试

```python
from llm.workflow import AnalysisWorkflow
import time

def run_analysis_with_retry(max_retries=3):
    """带重试的分析"""
    
    for attempt in range(max_retries):
        try:
            workflow = AnalysisWorkflow()
            results = workflow.run_full_analysis(
                historical_data=df,
                predictions=predictions,
                chart_path=chart_path
            )
            return results
            
        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("所有重试均失败，使用基础分析")
                return None
    
    return None
```

## 最佳实践总结

1. **API Key管理**
   ```python
   # ✅ 推荐：使用环境变量
   api_key = os.getenv('GEMINI_API_KEY')
   
   # ❌ 不推荐：硬编码
   api_key = "AIza..."  # 危险！
   ```

2. **错误处理**
   ```python
   # ✅ 总是包含try-except
   try:
       results = workflow.run_full_analysis(...)
   except Exception as e:
       logger.error(f"分析失败: {e}")
       # 回退到基础分析
   ```

3. **数据验证**
   ```python
   # ✅ 验证输入数据
   if df.empty or len(df) < 30:
       raise ValueError("历史数据不足")
   
   if not predictions:
       raise ValueError("预测数据缺失")
   ```

4. **结果持久化**
   ```python
   # ✅ 保存所有分析结果
   workflow.save_results(output_dir='models')
   workflow.generate_html_report(output_dir='models')
   ```

5. **性能优化**
   ```python
   # ✅ 缓存重复分析
   cache_key = f"{df.iloc[-1]['timestamp']}_{len(predictions)}"
   if cache_key in cache:
       return cache[cache_key]
   ```

---

**更多示例和帮助**: 
- 查看 `llm/README.md`
- 查看测试脚本 `test_ai_analysis.py`
- 提交Issue或PR
