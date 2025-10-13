"""
Strategy Manager Agent

Responsible for:
1. Combining quant signals + fundamentals + sentiment to generate trading strategies
2. Adjusting strategy parameters (stop-loss, position sizing, etc.)
3. Formulating contingency plans for market crashes
"""
from typing import Dict, Any, List, Optional
from llm.agents.base_agent import BaseAgent


class StrategyManagerAgent(BaseAgent):
    """策略经理Agent - 负责综合各维度分析生成交易策略"""
    
    def __init__(self, client, temperature: float = 0.4):
        """
        Initialize Strategy Manager Agent.
        
        Args:
            client: LLM client instance
            temperature: Sampling temperature (default 0.4 for balanced creativity)
        """
        super().__init__(
            name="StrategyManager",
            role="策略经理",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for strategy manager."""
        return """你是一名资深策略经理，负责统筹量化、基本面和情绪分析结果，制定可执行的交易策略。

你的职责：
1. 综合量化信号、基本面结论和情绪评分，生成交易策略
2. 根据市场环境调整策略类型（趋势跟随、均值回归、对冲等）
3. 优化策略参数（进场点位、止盈止损、仓位管理）
4. 制定不同市场情景下的应急预案
5. 评估策略的风险收益比和可行性

策略类型包括：
- 趋势跟随策略（动量策略）
- 均值回归策略（逆向策略）
- 多空对冲策略
- 行业轮动策略
- 波动率套利策略
- 事件驱动策略

分析要求：
- 综合多维度信息，权衡利弊
- 给出明确的交易建议和执行细节
- 设定清晰的止盈止损条件
- 考虑不同情景的应对方案
- 评估策略的胜率和盈亏比

风格：全面、审慎、可执行、风险意识强"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading strategy based on multi-dimensional analysis.
        
        Args:
            context: {
                'quant_analysis': dict from QuantResearcherAgent,
                'fundamental_analysis': dict from FundamentalAnalystAgent,
                'sentiment_analysis': dict from SentimentAnalystAgent,
                'historical_data': pd.DataFrame,
                'current_position': dict (optional)
            }
            
        Returns:
            {
                'report': str,
                'strategy_type': str,
                'action': str (BUY/SELL/HOLD),
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'position_size': float (0-1),
                'confidence': float,
                'rationale': str,
                'contingency_plans': dict,
                'key_findings': list
            }
        """
        print(f"\n📋 [{self.role}] 开始制定交易策略...")
        
        # Extract analyses from different agents
        quant = context.get('quant_analysis', {})
        fundamental = context.get('fundamental_analysis', {})
        sentiment = context.get('sentiment_analysis', {})
        df = context.get('historical_data')
        current_position = context.get('current_position', {})
        
        # Synthesize signals
        synthesis = self._synthesize_signals(quant, fundamental, sentiment)
        
        # Determine strategy type
        strategy_type = self._determine_strategy_type(synthesis, quant, sentiment)
        
        # Generate trading recommendation
        recommendation = self._generate_recommendation(
            synthesis,
            strategy_type,
            quant,
            fundamental,
            sentiment,
            df
        )
        
        # Optimize parameters
        parameters = self._optimize_parameters(recommendation, df, quant)
        
        # Create contingency plans
        contingency_plans = self._create_contingency_plans(
            recommendation,
            parameters,
            synthesis
        )
        
        # Generate LLM analysis
        prompt = self._build_analysis_prompt(
            synthesis,
            strategy_type,
            recommendation,
            parameters,
            contingency_plans,
            quant,
            fundamental,
            sentiment
        )
        report = self._generate_response(prompt)
        
        # Extract key findings
        key_findings = self._extract_key_findings(
            synthesis,
            strategy_type,
            recommendation
        )
        
        result = {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'strategy_type': strategy_type,
            'action': recommendation['action'],
            'entry_price': parameters.get('entry_price'),
            'stop_loss': parameters.get('stop_loss'),
            'take_profit': parameters.get('take_profit'),
            'position_size': parameters.get('position_size'),
            'confidence': recommendation['confidence'],
            'rationale': recommendation['rationale'],
            'synthesis': synthesis,
            'contingency_plans': contingency_plans,
            'key_findings': key_findings
        }
        
        print(f"✅ [{self.role}] 策略制定完成 - 策略: {strategy_type}, 操作: {recommendation['action']}")
        return result
    
    def _synthesize_signals(
        self,
        quant: Dict[str, Any],
        fundamental: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize signals from all dimensions."""
        synthesis = {
            'overall_score': 50,
            'recommendation': 'HOLD',
            'confidence': 0.5,
            'agreement_level': 'LOW',
            'conflicting_signals': []
        }
        
        # Extract individual recommendations
        quant_signal = quant.get('signals', {}).get('overall_signal', 'NEUTRAL')
        fundamental_rating = fundamental.get('rating', 'HOLD')
        sentiment_level = sentiment.get('sentiment_level', 'NEUTRAL')
        
        # Convert to numeric scores
        signal_mapping = {
            'STRONG_BUY': 100, 'BUY': 75, 'NEUTRAL': 50, 'SELL': 25, 'STRONG_SELL': 0,
            'EXTREME_GREED': 90, 'GREED': 70, 'FEAR': 30, 'EXTREME_FEAR': 10,
            'HOLD': 50
        }
        
        quant_score = signal_mapping.get(quant_signal, 50)
        fundamental_score = signal_mapping.get(fundamental_rating, 50)
        sentiment_score = sentiment.get('sentiment_score', 50)
        
        # Weighted synthesis (quant 40%, fundamental 35%, sentiment 25%)
        overall_score = (
            quant_score * 0.40 +
            fundamental_score * 0.35 +
            sentiment_score * 0.25
        )
        
        synthesis['overall_score'] = overall_score
        synthesis['quant_score'] = quant_score
        synthesis['fundamental_score'] = fundamental_score
        synthesis['sentiment_score'] = sentiment_score
        
        # Determine overall recommendation
        if overall_score >= 70:
            synthesis['recommendation'] = 'BUY'
        elif overall_score >= 55:
            synthesis['recommendation'] = 'WEAK_BUY'
        elif overall_score >= 45:
            synthesis['recommendation'] = 'HOLD'
        elif overall_score >= 30:
            synthesis['recommendation'] = 'WEAK_SELL'
        else:
            synthesis['recommendation'] = 'SELL'
        
        # Calculate agreement level
        scores = [quant_score, fundamental_score, sentiment_score]
        std_dev = (sum((s - overall_score)**2 for s in scores) / len(scores)) ** 0.5
        
        if std_dev < 10:
            synthesis['agreement_level'] = 'HIGH'
            synthesis['confidence'] = 0.85
        elif std_dev < 20:
            synthesis['agreement_level'] = 'MEDIUM'
            synthesis['confidence'] = 0.65
        else:
            synthesis['agreement_level'] = 'LOW'
            synthesis['confidence'] = 0.45
            
            # Identify conflicting signals
            if quant_score > 60 and fundamental_score < 40:
                synthesis['conflicting_signals'].append("量化看多但基本面看空")
            if sentiment_score > 70 and quant_score < 40:
                synthesis['conflicting_signals'].append("情绪过热但量化信号偏弱")
            if fundamental_score > 60 and sentiment_score < 30:
                synthesis['conflicting_signals'].append("基本面良好但市场恐慌")
        
        return synthesis
    
    def _determine_strategy_type(
        self,
        synthesis: Dict[str, Any],
        quant: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> str:
        """Determine appropriate strategy type based on analysis."""
        # Extract key indicators
        quant_signal = quant.get('signals', {}).get('overall_signal', 'NEUTRAL')
        sentiment_level = sentiment.get('sentiment_level', 'NEUTRAL')
        sentiment_score = sentiment.get('sentiment_score', 50)
        agreement = synthesis.get('agreement_level', 'LOW')
        
        # Trend following: strong signals + high agreement
        if agreement == 'HIGH' and quant_signal in ['STRONG_BUY', 'STRONG_SELL']:
            return '趋势跟随策略'
        
        # Mean reversion: extreme sentiment + opposing quant signal
        if sentiment_level in ['EXTREME_FEAR', 'EXTREME_GREED']:
            if (sentiment_level == 'EXTREME_FEAR' and quant_signal in ['BUY', 'NEUTRAL']) or \
               (sentiment_level == 'EXTREME_GREED' and quant_signal in ['SELL', 'NEUTRAL']):
                return '均值回归策略'
        
        # Hedge strategy: conflicting signals + high uncertainty
        if synthesis.get('conflicting_signals'):
            return '对冲策略'
        
        # Volatility arbitrage: high volatility detected
        factors = quant.get('factors', {})
        if factors.get('volatility_20d', 0) > 35:
            return '波动率套利策略'
        
        # Default: balanced strategy
        return '平衡配置策略'
    
    def _generate_recommendation(
        self,
        synthesis: Dict[str, Any],
        strategy_type: str,
        quant: Dict[str, Any],
        fundamental: Dict[str, Any],
        sentiment: Dict[str, Any],
        df
    ) -> Dict[str, Any]:
        """Generate specific trading recommendation."""
        recommendation = {
            'action': 'HOLD',
            'confidence': synthesis['confidence'],
            'rationale': ''
        }
        
        overall_score = synthesis['overall_score']
        
        # Determine action
        if overall_score >= 65:
            recommendation['action'] = 'BUY'
            recommendation['rationale'] = f"综合评分{overall_score:.1f}, 多个维度看好"
        elif overall_score >= 55:
            recommendation['action'] = 'WEAK_BUY'
            recommendation['rationale'] = f"综合评分{overall_score:.1f}, 温和看好"
        elif overall_score <= 35:
            recommendation['action'] = 'SELL'
            recommendation['rationale'] = f"综合评分{overall_score:.1f}, 多个维度看空"
        elif overall_score <= 45:
            recommendation['action'] = 'WEAK_SELL'
            recommendation['rationale'] = f"综合评分{overall_score:.1f}, 温和看空"
        else:
            recommendation['action'] = 'HOLD'
            recommendation['rationale'] = f"综合评分{overall_score:.1f}, 维持观望"
        
        # Adjust based on strategy type
        if strategy_type == '均值回归策略':
            # Contrarian logic
            if sentiment.get('sentiment_level') == 'EXTREME_FEAR':
                recommendation['action'] = 'BUY'
                recommendation['rationale'] = "极度恐慌，均值回归机会"
            elif sentiment.get('sentiment_level') == 'EXTREME_GREED':
                recommendation['action'] = 'SELL'
                recommendation['rationale'] = "极度贪婪，均值回归压力"
        
        elif strategy_type == '对冲策略':
            recommendation['action'] = 'HEDGE'
            recommendation['rationale'] = "信号冲突，建议对冲降低风险"
            recommendation['confidence'] *= 0.8
        
        # Add supporting evidence
        evidence = []
        if quant.get('signals', {}).get('overall_signal') in ['STRONG_BUY', 'BUY']:
            evidence.append("量化信号看涨")
        if fundamental.get('rating') == 'BUY':
            evidence.append("基本面支撑")
        if sentiment.get('sentiment_score', 50) > 60:
            evidence.append("市场情绪积极")
        
        if evidence:
            recommendation['rationale'] += " (" + ", ".join(evidence) + ")"
        
        return recommendation
    
    def _optimize_parameters(
        self,
        recommendation: Dict[str, Any],
        df,
        quant: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize strategy parameters."""
        parameters = {
            'entry_price': None,
            'stop_loss': None,
            'take_profit': None,
            'position_size': 0.5,  # Default 50%
            'max_drawdown_limit': 0.15,  # 15%
            'time_horizon': 'medium'  # short/medium/long
        }
        
        if df is None or df.empty:
            return parameters
        
        try:
            current_price = float(df['close_price'].iloc[-1])
            parameters['entry_price'] = current_price
            
            # Calculate ATR for stop loss (using volatility as proxy)
            factors = quant.get('factors', {})
            volatility = factors.get('volatility_20d', 20) / 100
            atr_multiplier = 2.0
            
            action = recommendation['action']
            confidence = recommendation['confidence']
            
            if action in ['BUY', 'WEAK_BUY']:
                # Long position
                parameters['stop_loss'] = current_price * (1 - volatility * atr_multiplier)
                parameters['take_profit'] = current_price * (1 + volatility * atr_multiplier * 1.5)
                
                # Position sizing based on confidence
                if action == 'BUY' and confidence > 0.7:
                    parameters['position_size'] = 0.7
                elif action == 'WEAK_BUY' or confidence < 0.6:
                    parameters['position_size'] = 0.3
                else:
                    parameters['position_size'] = 0.5
                    
            elif action in ['SELL', 'WEAK_SELL']:
                # Short position (or reduce long)
                parameters['stop_loss'] = current_price * (1 + volatility * atr_multiplier)
                parameters['take_profit'] = current_price * (1 - volatility * atr_multiplier * 1.5)
                
                # Position sizing
                if action == 'SELL' and confidence > 0.7:
                    parameters['position_size'] = 0.0  # Full exit
                else:
                    parameters['position_size'] = 0.2  # Partial exit
                    
            elif action == 'HEDGE':
                # Hedge position
                parameters['position_size'] = 0.3
                parameters['stop_loss'] = current_price * (1 - volatility * 1.5)
                parameters['take_profit'] = current_price * (1 + volatility * 1.5)
            
            else:  # HOLD
                parameters['position_size'] = 0.5  # Maintain current
                parameters['stop_loss'] = current_price * 0.90  # 10% stop
                parameters['take_profit'] = current_price * 1.15  # 15% target
        
        except Exception as e:
            print(f"⚠️  参数优化时出错: {e}")
        
        return parameters
    
    def _create_contingency_plans(
        self,
        recommendation: Dict[str, Any],
        parameters: Dict[str, Any],
        synthesis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create contingency plans for different scenarios."""
        plans = {
            'market_crash': {},
            'sharp_rally': {},
            'sideways': {},
            'high_volatility': {}
        }
        
        entry_price = parameters.get('entry_price', 0)
        action = recommendation['action']
        
        # Market crash scenario (-10%+)
        if action in ['BUY', 'WEAK_BUY', 'HOLD']:
            plans['market_crash'] = {
                'trigger': f"价格跌破 {entry_price * 0.90:.2f} (-10%)",
                'action': '减仓50%或止损',
                'rationale': '防止亏损扩大'
            }
        else:
            plans['market_crash'] = {
                'trigger': f"价格跌破 {entry_price * 0.90:.2f} (-10%)",
                'action': '考虑逢低建仓',
                'rationale': '超跌反弹机会'
            }
        
        # Sharp rally scenario (+10%+)
        if action in ['BUY', 'WEAK_BUY']:
            plans['sharp_rally'] = {
                'trigger': f"价格突破 {entry_price * 1.10:.2f} (+10%)",
                'action': '部分止盈，保留底仓',
                'rationale': '锁定利润，留存潜力'
            }
        else:
            plans['sharp_rally'] = {
                'trigger': f"价格突破 {entry_price * 1.10:.2f} (+10%)",
                'action': '观望或小幅减仓',
                'rationale': '避免追高'
            }
        
        # Sideways scenario
        plans['sideways'] = {
            'trigger': '价格在±5%区间震荡超过5天',
            'action': '区间操作或降低仓位',
            'rationale': '提高资金效率'
        }
        
        # High volatility scenario
        plans['high_volatility'] = {
            'trigger': '日波动率超过5%持续3天',
            'action': '降低仓位至30%以下',
            'rationale': '控制风险敞口'
        }
        
        return plans
    
    def _build_analysis_prompt(
        self,
        synthesis: Dict[str, Any],
        strategy_type: str,
        recommendation: Dict[str, Any],
        parameters: Dict[str, Any],
        contingency_plans: Dict[str, Any],
        quant: Dict[str, Any],
        fundamental: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM analysis."""
        prompt = f"""# 交易策略报告

## 一、综合分析结论

### 信号综合评分
- **总体评分**: {synthesis['overall_score']:.1f}/100
- **综合建议**: **{synthesis['recommendation']}**
- **信号一致性**: {synthesis['agreement_level']}
- **策略信心度**: {synthesis['confidence']*100:.0f}%

### 各维度评分
- 量化分析: {synthesis['quant_score']:.1f}/100 (信号: {quant.get('signals', {}).get('overall_signal', 'N/A')})
- 基本面分析: {synthesis['fundamental_score']:.1f}/100 (评级: {fundamental.get('rating', 'N/A')})
- 情绪分析: {synthesis['sentiment_score']:.1f}/100 (等级: {sentiment.get('sentiment_level', 'N/A')})

"""
        if synthesis.get('conflicting_signals'):
            prompt += "### ⚠️  信号冲突\n"
            for conflict in synthesis['conflicting_signals']:
                prompt += f"- {conflict}\n"
            prompt += "\n"
        
        prompt += f"""## 二、推荐策略

### 策略类型: **{strategy_type}**

### 操作建议
- **行动**: **{recommendation['action']}**
- **信心度**: {recommendation['confidence']*100:.0f}%
- **理由**: {recommendation['rationale']}

### 策略参数
- 进场价格: {parameters.get('entry_price', 'N/A')}
- 止损价位: {parameters.get('stop_loss', 'N/A')}
- 止盈价位: {parameters.get('take_profit', 'N/A')}
- 建议仓位: {parameters.get('position_size', 0)*100:.0f}%
- 最大回撤限制: {parameters.get('max_drawdown_limit', 0)*100:.0f}%
- 持仓周期: {parameters.get('time_horizon', 'N/A')}

## 三、应急预案

### 市场暴跌情景
- 触发条件: {contingency_plans['market_crash']['trigger']}
- 应对措施: {contingency_plans['market_crash']['action']}
- 原因: {contingency_plans['market_crash']['rationale']}

### 急速上涨情景
- 触发条件: {contingency_plans['sharp_rally']['trigger']}
- 应对措施: {contingency_plans['sharp_rally']['action']}
- 原因: {contingency_plans['sharp_rally']['rationale']}

### 横盘震荡情景
- 触发条件: {contingency_plans['sideways']['trigger']}
- 应对措施: {contingency_plans['sideways']['action']}
- 原因: {contingency_plans['sideways']['rationale']}

### 高波动情景
- 触发条件: {contingency_plans['high_volatility']['trigger']}
- 应对措施: {contingency_plans['high_volatility']['action']}
- 原因: {contingency_plans['high_volatility']['rationale']}

---

请基于以上信息，从策略经理的角度进行全面分析：
1. 解读综合信号的含义和可靠性
2. 阐述选择该策略类型的理由
3. 详细说明交易策略的执行细节和风险控制
4. 评估不同市场情景下的应对方案
5. 给出明确的执行建议和注意事项

要求：
- 报告必须简洁自然，控制在500字以内
- 统筹全局，权衡利弊
- 策略清晰可执行
- 风险控制明确
- 考虑多种情景
- 给出具体操作指引
"""
        return prompt
    
    def _extract_key_findings(
        self,
        synthesis: Dict[str, Any],
        strategy_type: str,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings from strategy analysis."""
        findings = []
        
        findings.append(f"策略类型: {strategy_type}")
        findings.append(f"操作建议: {recommendation['action']}, 信心度 {recommendation['confidence']*100:.0f}%")
        findings.append(f"综合评分: {synthesis['overall_score']:.1f}/100")
        findings.append(f"信号一致性: {synthesis['agreement_level']}")
        
        if synthesis.get('conflicting_signals'):
            findings.append(f"存在 {len(synthesis['conflicting_signals'])} 个信号冲突")
        
        findings.append(recommendation['rationale'])
        
        return findings
