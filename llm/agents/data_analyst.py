"""
Data Analyst Agent

Analyzes historical market data and prediction results to provide quantitative insights.
"""
import json
from typing import Dict, Any, List
import pandas as pd
from llm.agents.base_agent import BaseAgent


class DataAnalystAgent(BaseAgent):
    """Data Analyst agent for quantitative analysis."""
    
    def __init__(self, client, temperature: float = 0.3):
        """Initialize Data Analyst agent with lower temperature for factual analysis."""
        super().__init__(
            name="数据分析师",
            role="Data Analyst",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for data analyst."""
        return """你是一名专业的金融数据分析师，专注于BUFF饰品市场（Steam游戏饰品交易平台）。

你的职责：
1. 分析历史价格数据，识别趋势、模式和异常
2. 评估预测模型的准确性和可靠性
3. 计算关键统计指标（均值、波动率、涨跌幅等）
4. 识别支撑位和阻力位
5. 提供基于数据的客观分析报告

分析要求：
- 使用专业的金融术语
- 提供具体的数字和百分比
- 识别关键转折点
- 评估市场动量
- 保持客观、数据驱动的视角

输出格式：
使用清晰的结构化报告，包含：
1. 市场概况（30天历史表现）
2. 技术指标分析
3. 预测数据评估
4. 风险因素识别
5. 数据总结与关键发现
"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze historical and prediction data.
        
        Args:
            context: {
                'historical_data': DataFrame with 30 days of data,
                'predictions': List of prediction dicts,
                'statistics': Dict of calculated statistics
            }
            
        Returns:
            {
                'report': str - Analysis report,
                'key_findings': List[str] - Key findings,
                'metrics': Dict - Important metrics
            }
        """
        historical_data = context.get('historical_data')
        predictions = context.get('predictions', [])
        statistics = context.get('statistics', {})
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(historical_data, predictions, statistics)
        
        # Generate analysis
        report = self._generate_response(prompt)
        
        # Extract key findings (simple extraction from report)
        key_findings = self._extract_key_findings(report)
        
        return {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'key_findings': key_findings,
            'metrics': statistics
        }
    
    def _build_analysis_prompt(
        self,
        df: pd.DataFrame,
        predictions: List[Dict],
        stats: Dict
    ) -> str:
        """Build prompt for data analysis."""
        
        # Summarize historical data
        if df is not None and not df.empty:
            # Convert timestamps to readable dates
            from datetime import datetime
            start_date = datetime.fromtimestamp(df['timestamp'].min()).strftime('%Y年%m月%d日')
            end_date = datetime.fromtimestamp(df['timestamp'].max()).strftime('%Y年%m月%d日')
            
            # Prepare recent 5 days with readable dates
            recent_5 = df.tail(5).copy()
            recent_5['日期'] = recent_5['timestamp'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
            recent_5_display = recent_5[['日期', 'close_price', 'volume']].to_string(index=False)
            
            df_summary = f"""
近30天历史数据摘要：
- 数据记录数: {len(df)}条
- 时间范围: {start_date} 至 {end_date}
- 收盘价范围: {df['close_price'].min():.2f} - {df['close_price'].max():.2f}
- 平均收盘价: {df['close_price'].mean():.2f}
- 价格标准差: {df['close_price'].std():.2f}
- 最大涨幅: {df['close_price'].pct_change().max()*100:.2f}%
- 最大跌幅: {df['close_price'].pct_change().min()*100:.2f}%
- 平均日交易量: {df['volume'].mean():.0f}

最近5天收盘价:
{recent_5_display}
"""
        else:
            df_summary = "历史数据不可用"
        
        # Format predictions
        pred_summary = "预测数据：\n"
        for p in predictions:
            pred_summary += f"- 第{p['day']}天: 预期回报率 {p['predicted_daily_return']*100:.2f}%, 方向: {p['direction']}\n"
        
        # Format statistics
        stats_summary = f"""
统计指标：
{json.dumps(stats, indent=2, ensure_ascii=False)}
"""
        
        prompt = f"""请基于以下数据进行专业的金融分析：

{df_summary}

{pred_summary}

{stats_summary}

请提供一份结构化的数据分析报告，包括：
1. 【市场概况】- 30天历史表现总结
2. 【技术分析】- 趋势、支撑阻力、波动性分析
3. 【核心分析：5日预测解读】- **这是最重要的部分。请详细解读未来5天的预测数据，分析其对短期市场走势的意义，并将其作为你后续所有分析的核心依据。**
4. 【风险提示】- 基于数据识别的潜在风险
5. 【关键发现】- 3-5个最重要的数据洞察

请保持客观、专业，使用具体数字支撑你的分析。**你的所有分析都应紧密围绕提供的5日预测数据展开。**
"""
        return prompt
    
    def _extract_key_findings(self, report: str) -> List[str]:
        """Extract key findings from report."""
        findings = []
        
        # Simple extraction: look for numbered points or bullet points
        lines = report.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove leading markers
                clean_line = line.lstrip('0123456789.-•） ').strip()
                if len(clean_line) > 10:  # Filter out too short lines
                    findings.append(clean_line)
        
        # Return top 5 findings
        return findings[:5] if findings else ["数据分析完成，详见完整报告"]
