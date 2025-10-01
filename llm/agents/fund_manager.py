"""
Fund Manager Agent

Synthesizes all reports and generates final investment recommendations.
"""
import json
from typing import Dict, Any, List
from llm.agents.base_agent import BaseAgent


class FundManagerAgent(BaseAgent):
    """Fund Manager agent for final decision making."""
    
    def __init__(self, client, temperature: float = 0.4):
        """Initialize Fund Manager agent."""
        super().__init__(
            name="基金经理",
            role="Fund Manager",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for fund manager."""
        return """你是一名资深的基金经理，专注于BUFF饰品市场的投资管理。你拥有丰富的金融市场经验和决策能力。

你的职责：
1. 综合数据分析师和市场分析师的报告
2. 评估多方信息，做出平衡的投资决策
3. 制定明确的投资策略和仓位建议
4. 识别关键风险并制定风控措施
5. 撰写专业的投资建议报告

决策原则：
- 数据驱动：基于量化数据和技术指标
- 风险控制：明确止损止盈点位
- 市场敏感：结合市场情绪和新闻面
- 组合管理：考虑仓位配置和资金管理
- 长短结合：兼顾短期交易和长期投资

报告要求：
1. 执行摘要（Executive Summary）- 核心结论
2. 市场形势分析 - 综合数据和市场面
3. 投资策略建议 - 具体操作建议
4. 风险评估与管理 - 风险点和应对方案
5. 关键指标监控 - 需要持续跟踪的指标

输出风格：
- 专业、权威、决断
- 结构清晰、逻辑严密
- 具体可执行的建议
- 明确的数字和目标
"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final investment report.
        
        Args:
            context: {
                'data_analyst_report': Dict - Data analyst's analysis,
                'market_analyst_report': Dict - Market analyst's analysis,
                'chart_path': str - Path to prediction chart,
                'historical_data': DataFrame - Raw historical data
            }
            
        Returns:
            {
                'report': str - Final investment report,
                'recommendation': str - buy/sell/hold,
                'confidence': float - Confidence score 0-1,
                'strategy': Dict - Detailed strategy,
                'risk_assessment': Dict - Risk factors
            }
        """
        data_report = context.get('data_analyst_report', {})
        market_report = context.get('market_analyst_report', {})
        chart_path = context.get('chart_path', '')
        
        # Build comprehensive prompt
        prompt = self._build_final_prompt(data_report, market_report)
        
        # Generate with chart if available
        if chart_path:
            try:
                report = self._generate_with_images(
                    prompt=prompt,
                    image_paths=[chart_path]
                )
            except Exception as e:
                print(f"Failed to include chart in analysis: {e}")
                report = self._generate_response(prompt)
        else:
            report = self._generate_response(prompt)
        
        # Extract structured recommendations
        recommendation = self._extract_recommendation(report, market_report)
        confidence = self._calculate_confidence(data_report, market_report)
        strategy = self._extract_strategy(report)
        risk_assessment = self._extract_risks(report)
        
        return {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'recommendation': recommendation,
            'confidence': confidence,
            'strategy': strategy,
            'risk_assessment': risk_assessment
        }
    
    def _build_final_prompt(
        self,
        data_report: Dict[str, Any],
        market_report: Dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for fund manager."""
        
        # Extract key information
        data_analysis = data_report.get('report', '数据分析报告不可用')
        data_findings = data_report.get('key_findings', [])
        
        market_analysis = market_report.get('report', '市场分析报告不可用')
        market_sentiment = market_report.get('sentiment', 'neutral')
        market_signals = market_report.get('signals', {})
        
        prompt = f"""作为基金经理，你需要综合以下团队成员的分析报告，做出最终的投资决策。

═══════════════════════════════════════
【数据分析师报告】
═══════════════════════════════════════
{data_analysis}

关键发现：
{chr(10).join(f'• {finding}' for finding in data_findings[:5])}

═══════════════════════════════════════
【市场分析师报告】
═══════════════════════════════════════
{market_analysis}

市场情绪：{market_sentiment}
初步信号：{json.dumps(market_signals, ensure_ascii=False)}

═══════════════════════════════════════
【预测K线图】
═══════════════════════════════════════
（图表已附上，包含历史30天和未来5天预测）

═══════════════════════════════════════

请基于以上所有信息，撰写一份专业的投资建议报告。

报告结构要求：

📊 【执行摘要】
- 用2-3句话总结核心投资建议
- 明确给出操作方向：买入/卖出/持有/观望
- 说明主要理由和信心程度

📈 【市场形势综合分析】
- 整合数据面和消息面的分析
- 评估当前市场所处阶段
- 分析主要驱动因素

💡 【投资策略建议】
- 具体操作建议（仓位、时机、品种）
- 建议的入场点位或条件
- 止盈止损策略
- 预期收益和风险比

⚠️ 【风险评估与管理】
- 识别3-5个主要风险因素
- 每个风险的应对方案
- 最大可承受亏损
- 触发退出的条件

📍 【关键指标监控】
- 需要每日跟踪的指标
- 需要关注的新闻事件
- 策略调整的触发条件

🎯 【结论与行动项】
- 明确的下一步行动
- 时间敏感的决策点
- 预期复核时间

请提供专业、全面、可执行的投资建议。
"""
        return prompt
    
    def _extract_recommendation(
        self,
        report: str,
        market_report: Dict
    ) -> str:
        """Extract final recommendation from report."""
        report_lower = report.lower()
        
        # Check report content
        buy_keywords = ['建议买入', '建议做多', '看多', '买入机会', '建议增持']
        sell_keywords = ['建议卖出', '建议做空', '看空', '卖出', '建议减持']
        hold_keywords = ['建议持有', '观望', '等待', '持有', '暂不操作']
        
        buy_score = sum(1 for kw in buy_keywords if kw in report)
        sell_score = sum(1 for kw in sell_keywords if kw in report)
        hold_score = sum(1 for kw in hold_keywords if kw in report)
        
        # Also consider market analyst's signal
        market_signal = market_report.get('signals', {}).get('recommendation', 'hold')
        
        # Weighted decision
        if buy_score > sell_score and buy_score > hold_score:
            return 'buy'
        elif sell_score > buy_score and sell_score > hold_score:
            return 'sell'
        elif hold_score > 0 or (buy_score == sell_score):
            return 'hold'
        else:
            # Fallback to market signal
            return market_signal
    
    def _calculate_confidence(
        self,
        data_report: Dict,
        market_report: Dict
    ) -> float:
        """Calculate confidence score based on reports alignment."""
        
        # Start with medium confidence
        confidence = 0.5
        
        # Check data quality
        metrics = data_report.get('metrics', {})
        if metrics:
            confidence += 0.1
        
        # Check market sentiment clarity
        sentiment = market_report.get('sentiment', 'neutral')
        if sentiment in ['positive', 'negative']:
            confidence += 0.15
        
        # Check signal confidence
        signal_confidence = market_report.get('signals', {}).get('confidence', 'medium')
        if signal_confidence == 'high':
            confidence += 0.2
        elif signal_confidence == 'low':
            confidence -= 0.15
        
        # Ensure confidence is in [0, 1]
        confidence = max(0.1, min(0.95, confidence))
        
        return round(confidence, 2)
    
    def _extract_strategy(self, report: str) -> Dict[str, Any]:
        """Extract strategy details from report."""
        strategy = {
            'position_size': 'medium',  # small/medium/large
            'timeframe': 'short-term',  # short/medium/long
            'entry_points': [],
            'exit_points': [],
            'notes': ''
        }
        
        # Simple extraction based on keywords
        if '重仓' in report or '加大' in report:
            strategy['position_size'] = 'large'
        elif '轻仓' in report or '谨慎' in report or '小仓位' in report:
            strategy['position_size'] = 'small'
        
        if '长期' in report or '持有' in report:
            strategy['timeframe'] = 'long-term'
        elif '中期' in report:
            strategy['timeframe'] = 'medium-term'
        
        return strategy
    
    def _extract_risks(self, report: str) -> Dict[str, List[str]]:
        """Extract risk factors from report."""
        risks = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'mitigation': []
        }
        
        # Look for risk section
        risk_section = ''
        if '风险' in report:
            lines = report.split('\n')
            in_risk_section = False
            for line in lines:
                if '风险' in line:
                    in_risk_section = True
                elif in_risk_section:
                    if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-') or line.strip().startswith('•')):
                        risk_section += line + '\n'
                    elif line.strip().startswith('【') or line.strip().startswith('#'):
                        break
        
        # Categorize risks (simple heuristic)
        if risk_section:
            lines = [l.strip() for l in risk_section.split('\n') if l.strip()]
            for line in lines[:5]:  # Top 5 risks
                if '严重' in line or '重大' in line or '高' in line:
                    risks['high_risk'].append(line)
                elif '中等' in line or '一般' in line:
                    risks['medium_risk'].append(line)
                else:
                    risks['low_risk'].append(line)
        
        return risks
