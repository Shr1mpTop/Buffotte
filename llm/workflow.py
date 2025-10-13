"""
Multi-Agent Workflow Orchestrator

Coordinates the analysis workflow between data analyst, market analyst, and fund manager.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

from llm.clients.gemini_client import GeminiClient
from llm.clients.doubao_client import DoubaoClient
from llm.agents.data_analyst import DataAnalystAgent
from llm.agents.market_analyst import MarketAnalystAgent
from llm.agents.fund_manager import FundManagerAgent
from llm.agents.summarizer import SummarizerAgent


class AnalysisWorkflow:
    """Orchestrates multi-agent analysis workflow."""
    
    def __init__(self, llm_config: dict):
        """
        Initialize analysis workflow with all necessary agents.
        
        Args:
            llm_config: Configuration dictionary for LLM and agents.
        """
        self.config = llm_config
        provider = self.config.get('llm', {}).get('provider', 'google')
        model_name = self.config.get('llm', {}).get('model', 'gemini-1.5-flash')
        api_key = self.config.get('llm', {}).get('api_key')

        if not api_key:
            raise ValueError("API key not found in the 'llm.api_key' field of the configuration.")

        # Initialize LLM client based on provider
        if provider.lower() == 'google':
            self.client = GeminiClient(api_key=api_key, model_name=model_name)
        elif provider.lower() == 'doubao':
            self.client = DoubaoClient(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        agent_configs = self.config.get('agents', {})
        temp_configs = self.config.get('llm', {}).get('temperature', {})

        # Initialize agents
        self.data_analyst = DataAnalystAgent(
            client=self.client, 
            temperature=temp_configs.get('data_analyst', 0.3)
        )
        self.market_analyst = MarketAnalystAgent(
            client=self.client, 
            temperature=temp_configs.get('market_analyst', 0.5)
        )
        self.fund_manager = FundManagerAgent(
            client=self.client, 
            temperature=temp_configs.get('fund_manager', 0.4)
        )
        self.summarizer = SummarizerAgent(
            client=self.client,
            temperature=temp_configs.get('summarizer', 0.4) # Added for summarizer
        )

        self.workflow_results = {}
    
    def run_full_analysis(
        self,
        historical_data: pd.DataFrame,
        predictions: list,
        chart_path: str,
        enable_news_search: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete multi-agent analysis workflow.
        
        Args:
            historical_data: DataFrame with historical kline data
            predictions: List of prediction dicts from model
            chart_path: Path to prediction chart image
            enable_news_search: Whether to perform real news search
            
        Returns:
            Complete analysis results from all agents
        """
        print("\n" + "="*60)
        print("🤖 启动多Agent AI分析工作流")
        print("="*60)
        
        # Calculate statistics
        statistics = self._calculate_statistics(historical_data, predictions)
        
        # Stage 1: Data Analyst
        print("\n[1/4] 📊 数据分析师正在分析历史数据和预测...")
        data_context = {
            'historical_data': historical_data,
            'predictions': predictions,
            'statistics': statistics
        }
        data_result = self.data_analyst.analyze(data_context)
        self.workflow_results['data_analyst'] = data_result
        print(f"✓ 数据分析完成 - 识别 {len(data_result.get('key_findings', []))} 个关键发现")
        
        # Stage 2: Market Analyst
        print("\n[2/4] 📰 市场分析师正在分析市场动态和新闻...")
        market_context = {
            'data_analyst_report': data_result['report'],
            'search_enabled': enable_news_search,
            'keywords': ['BUFF', '悠悠优品', 'steam饰品', 'CSGO饰品', 'CS2']
        }
        market_result = self.market_analyst.analyze(market_context)
        self.workflow_results['market_analyst'] = market_result
        print(f"✓ 市场分析完成 - 情绪: {market_result.get('sentiment', 'unknown')}")
        
        # Stage 3: Fund Manager
        print("\n[3/4] 💼 基金经理正在综合分析并制定投资策略...")
        manager_context = {
            'data_analyst_report': data_result,
            'market_analyst_report': market_result,
            'chart_path': chart_path,
            'historical_data': historical_data
        }
        manager_result = self.fund_manager.analyze(manager_context)
        self.workflow_results['fund_manager'] = manager_result
        print(f"✓ 投资建议生成完成 - 建议: {manager_result.get('recommendation', 'unknown').upper()}")
        print(f"  信心度: {manager_result.get('confidence', 0)*100:.0f}%")
        
        # Stage 4: Summarizer
        print("\n[4/4] ✍️ 摘要专家正在生成报告摘要...")
        summary_result = self.summarizer.analyze(self.workflow_results)
        self.workflow_results['summary_agent'] = summary_result
        print("✓ 摘要生成完成")

        # Compile final results
        final_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'workflow_version': '1.1',
            'agents_used': ['data_analyst', 'market_analyst', 'fund_manager', 'summarizer'],
            'data_analyst': data_result,
            'market_analyst': market_result,
            'fund_manager': manager_result,
            'summary_agent': summary_result,
            'summary': {
                'recommendation': manager_result.get('recommendation'),
                'confidence': manager_result.get('confidence'),
                'key_findings': data_result.get('key_findings', [])[:3],
                'market_sentiment': market_result.get('sentiment'),
                'risk_level': self._assess_overall_risk(manager_result),
                'email_body': summary_result.get('summary')
            }
        }
        
        print("\n" + "="*60)
        print("✅ 多Agent分析工作流完成")
        print("="*60)
        
        return final_results
    
    def _calculate_statistics(
        self,
        df: pd.DataFrame,
        predictions: list
    ) -> Dict[str, Any]:
        """Calculate key statistics from data."""
        if df is None or df.empty:
            return {}
        
        stats = {}
        
        try:
            # Price statistics
            stats['current_price'] = float(df['close_price'].iloc[-1])
            stats['price_change_30d'] = float(
                (df['close_price'].iloc[-1] - df['close_price'].iloc[0]) / df['close_price'].iloc[0] * 100
            )
            stats['price_volatility'] = float(df['close_price'].pct_change().std() * 100)
            stats['avg_volume'] = float(df['volume'].mean())
            stats['max_price_30d'] = float(df['close_price'].max())
            stats['min_price_30d'] = float(df['close_price'].min())
            
            # Trend indicators
            ma5 = df['close_price'].rolling(window=5).mean().iloc[-1]
            ma10 = df['close_price'].rolling(window=10).mean().iloc[-1]
            stats['ma5'] = float(ma5)
            stats['ma10'] = float(ma10)
            stats['trend'] = 'bullish' if ma5 > ma10 else 'bearish'
            
            # Prediction statistics
            if predictions:
                avg_return = sum(p['predicted_daily_return'] for p in predictions) / len(predictions)
                stats['predicted_avg_return'] = float(avg_return)
                stats['predicted_direction'] = 'up' if avg_return > 0 else 'down'
                stats['prediction_days'] = len(predictions)
            
        except Exception as e:
            print(f"Warning: Failed to calculate some statistics: {e}")
        
        return stats
    
    def _assess_overall_risk(self, manager_result: Dict) -> str:
        """Assess overall risk level based on fund manager's analysis."""
        confidence = manager_result.get('confidence', 0.5)
        risk_assessment = manager_result.get('risk_assessment', {})
        
        high_risks = len(risk_assessment.get('high_risk', []))
        
        if high_risks > 2 or confidence < 0.4:
            return 'high'
        elif high_risks > 0 or confidence < 0.6:
            return 'medium'
        else:
            return 'low'
    
    def save_results(self, output_dir: str = 'models', filename: str = 'ai_analysis_report.json'):
        """Save workflow results to file."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.workflow_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存至: {output_path}")
        return output_path
    
    def generate_html_report(self, output_dir: str = 'models') -> str:
        """
        Generate HTML report from workflow results.
        
        Returns:
            Path to generated HTML file
        """
        if not self.workflow_results:
            raise ValueError("No workflow results available. Run analysis first.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_path = os.path.join(output_dir, f'ai_analysis_report_{timestamp}.html')
        
        html_content = self._build_html_report()
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML报告已生成: {html_path}")
        return html_path
    
    def _build_html_report(self) -> str:
        """Build HTML report from workflow results."""
        data_result = self.workflow_results.get('data_analyst', {})
        market_result = self.workflow_results.get('market_analyst', {})
        manager_result = self.workflow_results.get('fund_manager', {})
        
        recommendation = manager_result.get('recommendation', 'hold').upper()
        confidence = manager_result.get('confidence', 0.5) * 100
        
        # Recommendation color
        rec_color = {
            'BUY': '#28a745',
            'SELL': '#dc3545',
            'HOLD': '#ffc107'
        }.get(recommendation, '#6c757d')
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BUFF饰品市场AI分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header .timestamp {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .recommendation-box {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .recommendation-box h2 {{
            margin-top: 0;
            color: #333;
        }}
        .recommendation {{
            font-size: 48px;
            font-weight: bold;
            color: {rec_color};
            margin: 20px 0;
        }}
        .confidence {{
            font-size: 24px;
            color: #666;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .agent-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .badge-data {{
            background-color: #e3f2fd;
            color: #1976d2;
        }}
        .badge-market {{
            background-color: #f3e5f5;
            color: #7b1fa2;
        }}
        .badge-manager {{
            background-color: #e8f5e9;
            color: #388e3c;
        }}
        .key-findings {{
            background-color: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
        }}
        .key-findings ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .report-content {{
            white-space: pre-wrap;
            line-height: 1.8;
            color: #333;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 BUFF饰品市场AI分析报告</h1>
        <div class="timestamp">生成时间: {datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
    </div>
    
    <div class="recommendation-box">
        <h2>📊 投资建议</h2>
        <div class="recommendation">{recommendation}</div>
        <div class="confidence">信心度: {confidence:.0f}%</div>
    </div>
    
    <div class="section">
        <span class="agent-badge badge-manager">💼 基金经理</span>
        <h2>🎯 最终投资策略建议（重点）</h2>
        <div class="report-content">{manager_result.get('report', '报告不可用')}</div>
    </div>
    
    <div class="section">
        <span class="agent-badge badge-data">📊 数据分析师</span>
        <h2>数据分析报告</h2>
        <div class="key-findings">
            <strong>🔍 关键发现：</strong>
            <ul>
                {''.join(f'<li>{finding}</li>' for finding in data_result.get('key_findings', [])[:5])}
            </ul>
        </div>
        <div class="report-content">{data_result.get('report', '报告不可用')}</div>
    </div>
    
    <div class="section">
        <span class="agent-badge badge-market">📰 市场分析师</span>
        <h2>市场分析报告</h2>
        <div class="report-content">{market_result.get('report', '报告不可用')}</div>
    </div>
    
    <div class="footer">
        <p>本报告由AI多Agent系统自动生成，仅供参考，不构成投资建议</p>
        <p>Powered by Gemini AI & Buffotte Analysis System</p>
    </div>
</body>
</html>
"""
        return html
