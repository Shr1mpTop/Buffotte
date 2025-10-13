"""
Optimized Multi-Agent Workflow with Concurrent Processing

This module orchestrates a quantitative trading analysis workflow with 5 specialized agents:
1. Quantitative Researcher - Technical and factor analysis
2. Fundamental Analyst - Macro, industry, and valuation analysis  
3. Sentiment Analyst - Market sentiment and capital flow analysis
4. Strategy Manager - Trading strategy generation
5. Risk Control Officer - Risk management and compliance

Key Features:
- Parallel execution of independent analysis tasks (Stage 1: Quant + Fundamental + Sentiment)
- Sequential execution for dependent tasks (Stage 2: Strategy → Risk Control)
- Thread-safe operations with proper exception handling
- Comprehensive result aggregation and reporting
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from llm.clients.gemini_client import GeminiClient
from llm.clients.doubao_client import DoubaoClient
from llm.agents.quant_researcher import QuantResearcherAgent
from llm.agents.fundamental_analyst import FundamentalAnalystAgent
from llm.agents.sentiment_analyst import SentimentAnalystAgent
from llm.agents.strategy_manager import StrategyManagerAgent
from llm.agents.risk_control import RiskControlAgent


class OptimizedQuantWorkflow:
    """优化的量化交易多Agent工作流 - 支持并发处理"""
    
    def __init__(self, llm_config: dict):
        """
        Initialize optimized workflow with all agents.
        
        Args:
            llm_config: Configuration dictionary for LLM and agents
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
        
        temp_configs = self.config.get('llm', {}).get('temperature', {})

        # Initialize all agents
        print("🔧 初始化多Agent系统...")
        self.quant_researcher = QuantResearcherAgent(
            client=self.client,
            temperature=temp_configs.get('quant_researcher', 0.3)
        )
        self.fundamental_analyst = FundamentalAnalystAgent(
            client=self.client,
            temperature=temp_configs.get('fundamental_analyst', 0.4)
        )
        self.sentiment_analyst = SentimentAnalystAgent(
            client=self.client,
            temperature=temp_configs.get('sentiment_analyst', 0.5)
        )
        self.strategy_manager = StrategyManagerAgent(
            client=self.client,
            temperature=temp_configs.get('strategy_manager', 0.4)
        )
        self.risk_control = RiskControlAgent(
            client=self.client,
            temperature=temp_configs.get('risk_control', 0.2)
        )
        
        self.workflow_results = {}
        self.execution_times = {}
        
        print("✅ 多Agent系统初始化完成")
    
    def run_full_analysis(
        self,
        historical_data: pd.DataFrame,
        predictions: list,
        chart_path: str,
        enable_news_search: bool = False,
        max_workers: int = 3
    ) -> Dict[str, Any]:
        """
        Run complete multi-agent analysis workflow with parallel processing.
        
        Args:
            historical_data: DataFrame with historical kline data
            predictions: List of prediction dicts from model
            chart_path: Path to prediction chart image
            enable_news_search: Whether to perform real news search
            max_workers: Maximum number of concurrent threads (default 3 for Stage 1)
            
        Returns:
            Complete analysis results from all agents with execution metrics
        """
        print("\n" + "="*80)
        print("🚀 启动优化的多Agent量化交易分析工作流 (并发版本)")
        print("="*80)
        
        total_start_time = time.time()
        
        # ============================================================================
        # STAGE 1: Parallel Analysis (Quant + Fundamental + Sentiment)
        # These three analysts can work independently and concurrently
        # ============================================================================
        print("\n" + "─"*80)
        print("📊 阶段1: 多维度分析 (并行执行)")
        print("─"*80)
        
        stage1_start = time.time()
        stage1_results = self._run_parallel_analysis(
            historical_data=historical_data,
            predictions=predictions,
            enable_news_search=enable_news_search,
            max_workers=max_workers
        )
        stage1_time = time.time() - stage1_start
        
        print(f"\n✅ 阶段1完成 - 耗时: {stage1_time:.2f}秒")
        
        # Extract results
        quant_result = stage1_results.get('quant_researcher', {})
        fundamental_result = stage1_results.get('fundamental_analyst', {})
        sentiment_result = stage1_results.get('sentiment_analyst', {})
        
        # Store results
        self.workflow_results['quant_researcher'] = quant_result
        self.workflow_results['fundamental_analyst'] = fundamental_result
        self.workflow_results['sentiment_analyst'] = sentiment_result
        
        # ============================================================================
        # STAGE 2: Strategy Generation (Sequential, depends on Stage 1)
        # Strategy Manager needs all Stage 1 results
        # ============================================================================
        print("\n" + "─"*80)
        print("📋 阶段2: 策略生成")
        print("─"*80)
        
        stage2_start = time.time()
        strategy_context = {
            'quant_analysis': quant_result,
            'fundamental_analysis': fundamental_result,
            'sentiment_analysis': sentiment_result,
            'historical_data': historical_data
        }
        strategy_result = self.strategy_manager.analyze(strategy_context)
        self.workflow_results['strategy_manager'] = strategy_result
        stage2_time = time.time() - stage2_start
        
        print(f"\n✅ 阶段2完成 - 耗时: {stage2_time:.2f}秒")
        
        # ============================================================================
        # STAGE 3: Risk Control (Sequential, depends on Stage 2)
        # Risk Control needs strategy result for validation
        # ============================================================================
        print("\n" + "─"*80)
        print("🛡️ 阶段3: 风险审核")
        print("─"*80)
        
        stage3_start = time.time()
        risk_context = {
            'strategy': strategy_result,
            'historical_data': historical_data,
            'current_portfolio': {},  # Can be populated with actual portfolio
            'market_conditions': {}
        }
        risk_result = self.risk_control.analyze(risk_context)
        self.workflow_results['risk_control'] = risk_result
        stage3_time = time.time() - stage3_start
        
        print(f"\n✅ 阶段3完成 - 耗时: {stage3_time:.2f}秒")
        
        # ============================================================================
        # Compile Final Results
        # ============================================================================
        total_time = time.time() - total_start_time
        
        self.execution_times = {
            'stage1_parallel_analysis': stage1_time,
            'stage2_strategy_generation': stage2_time,
            'stage3_risk_control': stage3_time,
            'total_time': total_time,
            'speedup_estimate': '~2-3x vs sequential'  # Estimated speedup
        }
        
        final_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'workflow_version': '2.0-optimized',
            'execution_mode': 'parallel',
            'agents_used': [
                'quant_researcher', 
                'fundamental_analyst', 
                'sentiment_analyst',
                'strategy_manager',
                'risk_control'
            ],
            'execution_times': self.execution_times,
            
            # Agent results
            'quant_researcher': quant_result,
            'fundamental_analyst': fundamental_result,
            'sentiment_analyst': sentiment_result,
            'strategy_manager': strategy_result,
            'risk_control': risk_result,
            
            # Executive summary
            'executive_summary': self._generate_executive_summary(
                strategy_result,
                risk_result
            )
        }
        
        print("\n" + "="*80)
        print(f"✅ 多Agent分析工作流完成 - 总耗时: {total_time:.2f}秒")
        print(f"   阶段1(并行): {stage1_time:.2f}秒 | 阶段2: {stage2_time:.2f}秒 | 阶段3: {stage3_time:.2f}秒")
        print("="*80)
        
        return final_results
    
    def _run_parallel_analysis(
        self,
        historical_data: pd.DataFrame,
        predictions: list,
        enable_news_search: bool,
        max_workers: int
    ) -> Dict[str, Any]:
        """
        Run Stage 1 analysis in parallel using ThreadPoolExecutor.
        
        Returns:
            Dictionary with results from all three analysts
        """
        results = {}
        
        # Ensure matplotlib uses non-interactive backend for thread safety
        import matplotlib
        matplotlib.use('Agg')
        
        # Define tasks for parallel execution
        tasks = {
            'quant_researcher': (
                self.quant_researcher.analyze,
                {
                    'historical_data': historical_data.copy() if historical_data is not None else None,
                    'predictions': predictions,
                    'market_data': {}
                }
            ),
            'fundamental_analyst': (
                self.fundamental_analyst.analyze,
                {
                    'historical_data': historical_data.copy() if historical_data is not None else None,
                    'macro_data': {},
                    'industry_data': {},
                    'company_data': {},
                    'news_data': []
                }
            ),
            'sentiment_analyst': (
                self.sentiment_analyst.analyze,
                {
                    'historical_data': historical_data.copy() if historical_data is not None else None,
                    'news_data': [],
                    'social_data': {},
                    'flow_data': {},
                    'search_enabled': enable_news_search
                }
            )
        }
        
        # Execute tasks in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_agent = {
                executor.submit(task_func, task_context): agent_name
                for agent_name, (task_func, task_context) in tasks.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_name] = result
                    print(f"   ✓ {agent_name} 完成")
                except Exception as e:
                    print(f"   ✗ {agent_name} 失败: {e}")
                    import traceback
                    traceback.print_exc()
                    results[agent_name] = {
                        'agent': agent_name,
                        'error': str(e),
                        'report': f'分析失败: {e}',
                        'key_findings': [f'Agent执行失败: {e}']
                    }
        
        return results
    
    def _generate_executive_summary(
        self,
        strategy_result: Dict[str, Any],
        risk_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary for quick decision making."""
        return {
            'trading_action': strategy_result.get('action', 'HOLD'),
            'strategy_type': strategy_result.get('strategy_type', 'N/A'),
            'confidence': strategy_result.get('confidence', 0),
            'position_size': strategy_result.get('position_size', 0),
            'risk_approval': risk_result.get('approval_status', 'PENDING'),
            'risk_level': risk_result.get('risk_level', 'UNKNOWN'),
            'key_recommendation': self._format_recommendation(strategy_result, risk_result)
        }
    
    def _format_recommendation(
        self,
        strategy_result: Dict[str, Any],
        risk_result: Dict[str, Any]
    ) -> str:
        """Format final recommendation for executive summary."""
        action = strategy_result.get('action', 'HOLD')
        approval = risk_result.get('approval_status', 'PENDING')
        risk_level = risk_result.get('risk_level', 'UNKNOWN')
        
        if approval == 'REJECTED':
            return f"❌ 建议{action}但风控拒绝 - 风险等级{risk_level}，需整改"
        elif approval == 'CONDITIONAL':
            return f"⚠️  建议{action}但需满足风控条件 - 风险等级{risk_level}"
        else:
            return f"✅ 建议{action} - 风险等级{risk_level}，已通过风控"
    
    def save_results(
        self,
        output_dir: str = 'models',
        filename: str = 'quant_workflow_report.json'
    ) -> str:
        """Save workflow results to file."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        # Prepare data for JSON serialization
        save_data = {}
        for key, value in self.workflow_results.items():
            if isinstance(value, dict):
                save_data[key] = value
            else:
                save_data[key] = str(value)
        
        save_data['execution_times'] = self.execution_times
        save_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 分析结果已保存至: {output_path}")
        return output_path
    
    def generate_html_report(self, output_dir: str = 'models') -> str:
        """
        Generate comprehensive HTML report from workflow results.
        
        Returns:
            Path to generated HTML file
        """
        if not self.workflow_results:
            raise ValueError("No workflow results available. Run analysis first.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_path = os.path.join(output_dir, f'quant_workflow_report_{timestamp}.html')
        
        html_content = self._build_html_report()
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML报告已生成: {html_path}")
        return html_path
    
    def _build_html_report(self) -> str:
        """Build comprehensive HTML report."""
        # Extract results
        strategy = self.workflow_results.get('strategy_manager', {})
        risk = self.workflow_results.get('risk_control', {})
        
        action = strategy.get('action', 'HOLD')
        approval = risk.get('approval_status', 'PENDING')
        
        # Color coding
        action_colors = {
            'BUY': '#28a745',
            'WEAK_BUY': '#5cb85c',
            'HOLD': '#ffc107',
            'WEAK_SELL': '#fd7e14',
            'SELL': '#dc3545',
            'HEDGE': '#6c757d'
        }
        action_color = action_colors.get(action, '#6c757d')
        
        approval_colors = {
            'APPROVED': '#28a745',
            'CONDITIONAL': '#ffc107',
            'REJECTED': '#dc3545'
        }
        approval_color = approval_colors.get(approval, '#6c757d')
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>量化交易多Agent分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            text-align: center;
        }}
        .summary-card .label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-card .subtitle {{
            font-size: 14px;
            color: #999;
        }}
        .section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #2a5298;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .agent-badge {{
            display: inline-block;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .badge-quant {{ background: #e3f2fd; color: #1976d2; }}
        .badge-fundamental {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-sentiment {{ background: #fff3e0; color: #e65100; }}
        .badge-strategy {{ background: #e8f5e9; color: #2e7d32; }}
        .badge-risk {{ background: #ffebee; color: #c62828; }}
        .report-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 4px solid #667eea;
        }}
        .report-box pre {{
            white-space: pre-wrap;
            font-family: inherit;
            margin: 0;
            line-height: 1.8;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .metric-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}
        .metric-item .label {{
            font-size: 13px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-item .value {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .findings {{
            background: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
        }}
        .findings ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        .findings li {{
            margin: 5px 0;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 14px;
        }}
        .performance-stats {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .performance-stats strong {{
            color: #2e7d32;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 量化交易多Agent分析报告</h1>
            <div class="subtitle">Multi-Agent Quantitative Trading Analysis Report</div>
            <div class="subtitle">生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="label">交易建议</div>
                <div class="value" style="color: {action_color}">{action}</div>
                <div class="subtitle">信心度: {strategy.get('confidence', 0)*100:.0f}%</div>
            </div>
            <div class="summary-card">
                <div class="label">风控审核</div>
                <div class="value" style="color: {approval_color}">{approval}</div>
                <div class="subtitle">风险等级: {risk.get('risk_level', 'N/A')}</div>
            </div>
            <div class="summary-card">
                <div class="label">策略类型</div>
                <div class="value" style="font-size: 20px; color: #667eea">{strategy.get('strategy_type', 'N/A')}</div>
                <div class="subtitle">建议仓位: {strategy.get('position_size', 0)*100:.0f}%</div>
            </div>
            <div class="summary-card">
                <div class="label">执行效率</div>
                <div class="value" style="font-size: 24px; color: #2e7d32">{self.execution_times.get('total_time', 0):.1f}秒</div>
                <div class="subtitle">并发优化: ~2-3x提速</div>
            </div>
        </div>
        
        {self._build_agent_sections()}
        
        <div class="section">
            <h2>⏱️ 执行性能统计</h2>
            <div class="performance-stats">
                <strong>阶段1 - 多维度分析(并行)</strong>: {self.execution_times.get('stage1_parallel_analysis', 0):.2f}秒<br>
                <strong>阶段2 - 策略生成</strong>: {self.execution_times.get('stage2_strategy_generation', 0):.2f}秒<br>
                <strong>阶段3 - 风险审核</strong>: {self.execution_times.get('stage3_risk_control', 0):.2f}秒<br>
                <strong>总耗时</strong>: {self.execution_times.get('total_time', 0):.2f}秒<br>
                <em>通过并行执行量化、基本面、情绪三个分析师，相比串行执行预计提速2-3倍</em>
            </div>
        </div>
        
        <div class="footer">
            <p>本报告由AI多Agent系统自动生成，采用并发优化技术提升分析效率</p>
            <p>仅供参考，不构成投资建议 | Powered by Optimized Multi-Agent System v2.0</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _build_agent_sections(self) -> str:
        """Build HTML sections for each agent's report."""
        sections = ""
        
        # Define agent order and properties
        agents_config = [
            ('risk_control', '🛡️ 风险控制审核报告', 'badge-risk'),
            ('strategy_manager', '📋 交易策略报告', 'badge-strategy'),
            ('quant_researcher', '🔬 量化分析报告', 'badge-quant'),
            ('fundamental_analyst', '📊 基本面分析报告', 'badge-fundamental'),
            ('sentiment_analyst', '💭 市场情绪分析报告', 'badge-sentiment'),
        ]
        
        for agent_key, title, badge_class in agents_config:
            result = self.workflow_results.get(agent_key, {})
            if result:
                sections += f"""
        <div class="section">
            <span class="agent-badge {badge_class}">{result.get('role', 'Agent')}</span>
            <h2>{title}</h2>
"""
                # Add key findings if available
                if result.get('key_findings'):
                    sections += """
            <div class="findings">
                <strong>🔍 关键发现：</strong>
                <ul>
"""
                    for finding in result['key_findings'][:5]:
                        sections += f"                    <li>{finding}</li>\n"
                    sections += """
                </ul>
            </div>
"""
                
                # Add report
                sections += f"""
            <div class="report-box">
                <pre>{result.get('report', '报告不可用')}</pre>
            </div>
        </div>
"""
        
        return sections
