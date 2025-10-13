"""
Fundamental Analyst Agent

Responsible for:
1. Interpreting macroeconomic data (CPI, PMI, etc.)
2. Analyzing industry policies and company financial reports
3. Evaluating valuation rationality (PE/PB percentiles)
"""
from typing import Dict, Any, List, Optional
from llm.agents.base_agent import BaseAgent
import pandas as pd
import numpy as np


class FundamentalAnalystAgent(BaseAgent):
    """基本面研究员Agent - 负责宏观、行业和公司基本面分析"""
    
    def __init__(self, client, temperature: float = 0.4):
        """
        Initialize Fundamental Analyst Agent.
        
        Args:
            client: LLM client instance
            temperature: Sampling temperature (default 0.4 for balanced analysis)
        """
        super().__init__(
            name="FundamentalAnalyst",
            role="基本面研究员",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for fundamental analyst."""
        return """你是一名资深基本面研究员，专注于宏观经济、行业分析和公司基本面研究。

你的职责：
1. 解读宏观经济数据（CPI、PMI、GDP、利率等）对市场的影响
2. 分析行业政策、监管变化、竞争格局
3. 研究公司财报、业绩预告、重大公告
4. 评估标的估值合理性（PE、PB、PS等估值指标及其分位数）
5. 给出标的评级调整建议（增持/持有/减持）

分析要求：
- 关注宏观经济周期和政策导向
- 深入分析行业趋势和竞争态势
- 评估公司盈利能力、成长性、财务健康度
- 使用多种估值方法交叉验证
- 识别利好/利空因素，给出明确投资建议

风格：深度、全面、前瞻性、逻辑清晰"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform fundamental analysis.
        
        Args:
            context: {
                'historical_data': pd.DataFrame,
                'macro_data': dict of macro indicators (optional),
                'industry_data': dict of industry info (optional),
                'company_data': dict of company info (optional),
                'news_data': list of relevant news (optional)
            }
            
        Returns:
            {
                'report': str,
                'macro_assessment': dict,
                'industry_assessment': dict,
                'valuation_assessment': dict,
                'rating': str (BUY/HOLD/SELL),
                'confidence': float,
                'key_findings': list
            }
        """
        print(f"\n📊 [{self.role}] 开始基本面分析...")
        
        # Extract data
        df = context.get('historical_data')
        macro_data = context.get('macro_data', {})
        industry_data = context.get('industry_data', {})
        company_data = context.get('company_data', {})
        news_data = context.get('news_data', [])
        
        # Perform multi-level analysis
        macro_assessment = self._assess_macro_environment(macro_data, df)
        industry_assessment = self._assess_industry(industry_data, df)
        valuation_assessment = self._assess_valuation(df, company_data)
        
        # Generate LLM analysis
        prompt = self._build_analysis_prompt(
            macro_assessment,
            industry_assessment,
            valuation_assessment,
            news_data
        )
        report = self._generate_response(prompt)
        
        # Determine rating
        rating, confidence = self._determine_rating(
            macro_assessment,
            industry_assessment,
            valuation_assessment
        )
        
        # Extract key findings
        key_findings = self._extract_key_findings(
            macro_assessment,
            industry_assessment,
            valuation_assessment
        )
        
        result = {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'macro_assessment': macro_assessment,
            'industry_assessment': industry_assessment,
            'valuation_assessment': valuation_assessment,
            'rating': rating,
            'confidence': confidence,
            'key_findings': key_findings
        }
        
        print(f"✅ [{self.role}] 基本面分析完成 - 评级: {rating}, 信心度: {confidence*100:.0f}%")
        return result
    
    def _assess_macro_environment(
        self,
        macro_data: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Assess macroeconomic environment."""
        assessment = {
            'overall_score': 50,  # 0-100
            'economic_cycle': 'EXPANSION',  # EXPANSION/PEAK/CONTRACTION/TROUGH
            'policy_stance': 'NEUTRAL',  # LOOSE/NEUTRAL/TIGHT
            'indicators': {},
            'summary': []
        }
        
        # Note: In real implementation, fetch actual macro data
        # For now, we'll use simulated assessment based on market trends
        
        if df is not None and not df.empty:
            # Use price trend as proxy for macro environment
            recent_return = (df['close_price'].iloc[-1] / df['close_price'].iloc[-20] - 1) * 100 if len(df) >= 20 else 0
            volatility = df['close_price'].pct_change().std() * 100
            
            # Score based on trend and stability
            if recent_return > 5 and volatility < 3:
                assessment['overall_score'] = 75
                assessment['economic_cycle'] = 'EXPANSION'
                assessment['policy_stance'] = 'LOOSE'
                assessment['summary'].append("宏观环境向好，市场趋势上涨且波动可控")
            elif recent_return < -5 or volatility > 5:
                assessment['overall_score'] = 30
                assessment['economic_cycle'] = 'CONTRACTION'
                assessment['policy_stance'] = 'TIGHT'
                assessment['summary'].append("宏观环境承压，市场波动加大")
            else:
                assessment['overall_score'] = 50
                assessment['economic_cycle'] = 'PEAK'
                assessment['policy_stance'] = 'NEUTRAL'
                assessment['summary'].append("宏观环境中性，市场处于平衡状态")
        
        # Add macro indicators (simulated)
        assessment['indicators'] = {
            'gdp_growth': macro_data.get('gdp_growth', 'N/A'),
            'cpi': macro_data.get('cpi', 'N/A'),
            'pmi': macro_data.get('pmi', 'N/A'),
            'interest_rate': macro_data.get('interest_rate', 'N/A')
        }
        
        return assessment
    
    def _assess_industry(
        self,
        industry_data: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Assess industry conditions."""
        assessment = {
            'overall_score': 50,  # 0-100
            'industry_stage': 'MATURE',  # EMERGING/GROWTH/MATURE/DECLINING
            'competitive_position': 'MEDIUM',  # HIGH/MEDIUM/LOW
            'policy_support': 'NEUTRAL',  # STRONG/NEUTRAL/WEAK
            'trends': [],
            'summary': []
        }
        
        # Analyze industry using available data
        if df is not None and not df.empty:
            # Volume trend as proxy for industry activity
            volume = df['volume'].values
            if len(volume) >= 20:
                recent_volume = np.mean(volume[-5:])
                historic_volume = np.mean(volume[-20:-5])
                volume_growth = (recent_volume / historic_volume - 1) * 100
                
                if volume_growth > 20:
                    assessment['overall_score'] = 70
                    assessment['industry_stage'] = 'GROWTH'
                    assessment['trends'].append(f"交易量增长显著({volume_growth:.1f}%), 行业活跃度提升")
                elif volume_growth < -20:
                    assessment['overall_score'] = 35
                    assessment['industry_stage'] = 'DECLINING'
                    assessment['trends'].append(f"交易量萎缩({volume_growth:.1f}%), 行业景气度下降")
                else:
                    assessment['overall_score'] = 50
                    assessment['industry_stage'] = 'MATURE'
                    assessment['trends'].append("交易量平稳，行业处于成熟期")
        
        # Industry-specific assessment for gaming items market
        assessment['summary'].append("游戏饰品市场属于新兴数字资产领域")
        assessment['summary'].append("受游戏玩家基数、电竞热度、平台政策等多因素影响")
        assessment['policy_support'] = 'NEUTRAL'
        assessment['competitive_position'] = 'MEDIUM'
        
        return assessment
    
    def _assess_valuation(
        self,
        df: pd.DataFrame,
        company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess valuation levels."""
        assessment = {
            'overall_score': 50,  # 0-100
            'valuation_level': 'FAIR',  # UNDERVALUED/FAIR/OVERVALUED
            'metrics': {},
            'percentiles': {},
            'summary': []
        }
        
        if df is None or df.empty:
            return assessment
        
        try:
            close = df['close_price'].values
            current_price = close[-1]
            
            # Calculate price percentiles
            price_percentile = self._calculate_percentile(current_price, close)
            assessment['percentiles']['price'] = float(price_percentile)
            
            # Price vs moving averages
            ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_price
            ma60 = np.mean(close[-60:]) if len(close) >= 60 else current_price
            
            assessment['metrics']['price_to_ma20'] = float((current_price / ma20 - 1) * 100)
            assessment['metrics']['price_to_ma60'] = float((current_price / ma60 - 1) * 100)
            
            # Assess valuation level
            if price_percentile < 30:
                assessment['overall_score'] = 70
                assessment['valuation_level'] = 'UNDERVALUED'
                assessment['summary'].append(f"当前价格处于历史低位(分位数{price_percentile:.1f}%), 估值偏低")
            elif price_percentile > 70:
                assessment['overall_score'] = 30
                assessment['valuation_level'] = 'OVERVALUED'
                assessment['summary'].append(f"当前价格处于历史高位(分位数{price_percentile:.1f}%), 估值偏高")
            else:
                assessment['overall_score'] = 50
                assessment['valuation_level'] = 'FAIR'
                assessment['summary'].append(f"当前价格处于合理区间(分位数{price_percentile:.1f}%), 估值适中")
            
            # Historical volatility-adjusted valuation
            returns = pd.Series(close).pct_change().dropna()
            volatility = returns.std()
            if volatility > 0:
                return_vol_ratio = returns.mean() / volatility
                assessment['metrics']['return_volatility_ratio'] = float(return_vol_ratio)
                
                if return_vol_ratio > 0.1:
                    assessment['summary'].append("收益波动比良好，风险调整后价值较高")
                elif return_vol_ratio < -0.1:
                    assessment['summary'].append("收益波动比较差，风险调整后价值较低")
            
        except Exception as e:
            print(f"⚠️  估值分析时出错: {e}")
        
        return assessment
    
    def _calculate_percentile(self, current_value: float, historical_values: np.ndarray) -> float:
        """Calculate percentile of current value in historical distribution."""
        if len(historical_values) == 0:
            return 50.0
        
        percentile = (historical_values < current_value).sum() / len(historical_values) * 100
        return percentile
    
    def _determine_rating(
        self,
        macro: Dict[str, Any],
        industry: Dict[str, Any],
        valuation: Dict[str, Any]
    ) -> tuple:
        """Determine overall rating and confidence."""
        # Weight different factors
        macro_weight = 0.3
        industry_weight = 0.3
        valuation_weight = 0.4
        
        # Calculate weighted score
        overall_score = (
            macro['overall_score'] * macro_weight +
            industry['overall_score'] * industry_weight +
            valuation['overall_score'] * valuation_weight
        )
        
        # Determine rating
        if overall_score >= 65:
            rating = 'BUY'
            confidence = min(0.9, (overall_score - 50) / 50 + 0.5)
        elif overall_score >= 40:
            rating = 'HOLD'
            confidence = 0.6
        else:
            rating = 'SELL'
            confidence = min(0.9, (50 - overall_score) / 50 + 0.5)
        
        return rating, confidence
    
    def _build_analysis_prompt(
        self,
        macro: Dict[str, Any],
        industry: Dict[str, Any],
        valuation: Dict[str, Any],
        news: List[Dict]
    ) -> str:
        """Build prompt for LLM analysis."""
        prompt = f"""# 基本面分析报告

## 一、宏观经济环境分析

### 综合评分: {macro['overall_score']}/100

- 经济周期: **{macro['economic_cycle']}**
- 政策立场: **{macro['policy_stance']}**

### 关键指标
- GDP增速: {macro['indicators'].get('gdp_growth', 'N/A')}
- CPI: {macro['indicators'].get('cpi', 'N/A')}
- PMI: {macro['indicators'].get('pmi', 'N/A')}
- 利率水平: {macro['indicators'].get('interest_rate', 'N/A')}

### 要点
"""
        for point in macro['summary']:
            prompt += f"- {point}\n"
        
        prompt += f"""
## 二、行业分析

### 综合评分: {industry['overall_score']}/100

- 行业阶段: **{industry['industry_stage']}**
- 竞争地位: **{industry['competitive_position']}**
- 政策支持: **{industry['policy_support']}**

### 行业趋势
"""
        for trend in industry['trends']:
            prompt += f"- {trend}\n"
        
        prompt += "\n### 要点\n"
        for point in industry['summary']:
            prompt += f"- {point}\n"
        
        prompt += f"""
## 三、估值分析

### 综合评分: {valuation['overall_score']}/100

- 估值水平: **{valuation['valuation_level']}**

### 估值指标
- 价格分位数: {valuation['percentiles'].get('price', 50):.1f}%
- 相对MA20: {valuation['metrics'].get('price_to_ma20', 0):.2f}%
- 相对MA60: {valuation['metrics'].get('price_to_ma60', 0):.2f}%
"""
        if 'return_volatility_ratio' in valuation['metrics']:
            prompt += f"- 收益波动比: {valuation['metrics']['return_volatility_ratio']:.4f}\n"
        
        prompt += "\n### 要点\n"
        for point in valuation['summary']:
            prompt += f"- {point}\n"
        
        if news:
            prompt += "\n## 四、重要新闻和事件\n"
            for i, item in enumerate(news[:5], 1):
                prompt += f"{i}. {item.get('title', 'N/A')}\n"
        
        prompt += """
---

请基于以上基本面数据，从基本面研究员的角度进行深度分析：
1. 解读宏观经济环境对该标的的影响
2. 分析行业发展趋势和竞争格局
3. 评估当前估值是否合理，是否存在高估或低估
4. 综合判断基本面因素对投资价值的支撑程度
5. 给出明确的投资评级建议（增持/持有/减持）

要求：
- 报告必须简洁自然，控制在500字以内
- 逻辑清晰，层次分明
- 关注长期价值和投资安全边际
- 识别关键风险和机会
- 给出明确的投资建议
"""
        return prompt
    
    def _extract_key_findings(
        self,
        macro: Dict[str, Any],
        industry: Dict[str, Any],
        valuation: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings from fundamental analysis."""
        findings = []
        
        # Macro findings
        findings.append(f"宏观环境: {macro['economic_cycle']}, 评分 {macro['overall_score']}/100")
        findings.extend(macro['summary'][:2])
        
        # Industry findings
        findings.append(f"行业状态: {industry['industry_stage']}, 评分 {industry['overall_score']}/100")
        if industry['trends']:
            findings.append(industry['trends'][0])
        
        # Valuation findings
        findings.append(f"估值水平: {valuation['valuation_level']}, 评分 {valuation['overall_score']}/100")
        if valuation['summary']:
            findings.append(valuation['summary'][0])
        
        return findings
