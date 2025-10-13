"""
Sentiment Analyst Agent

Responsible for:
1. Monitoring public sentiment and news heat
2. Analyzing capital flows (institutional, retail)
3. Calculating market fear/greed indices
"""
from typing import Dict, Any, List, Optional
from llm.agents.base_agent import BaseAgent
import pandas as pd
import numpy as np


class SentimentAnalystAgent(BaseAgent):
    """市场情绪分析师Agent - 负责舆情、资金流向和情绪指标分析"""
    
    def __init__(self, client, temperature: float = 0.5):
        """
        Initialize Sentiment Analyst Agent.
        
        Args:
            client: LLM client instance
            temperature: Sampling temperature (default 0.5 for creative analysis)
        """
        super().__init__(
            name="SentimentAnalyst",
            role="市场情绪分析师",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for sentiment analyst."""
        return """你是一名资深市场情绪分析师，专注于分析市场参与者的情绪和行为。

你的职责：
1. 监控舆情热度和新闻情绪（社交媒体、新闻、论坛等）
2. 分析资金流向（机构资金、散户资金、北向资金等）
3. 测算市场情绪指标（恐慌指数、贪婪指数、情绪温度计）
4. 识别情绪极端化情况（过度恐慌/过度狂热）
5. 输出情绪热力图和风险预警

分析要求：
- 综合多个维度的情绪信号
- 识别情绪拐点和异常波动
- 区分短期情绪波动和长期趋势
- 关注群体行为和从众效应
- 及时预警极端情绪风险

风格：敏锐、前瞻、善于捕捉市场微妙变化"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform sentiment analysis.
        
        Args:
            context: {
                'historical_data': pd.DataFrame,
                'news_data': list of news/articles,
                'social_data': dict of social media sentiment,
                'flow_data': dict of capital flow data,
                'search_enabled': bool
            }
            
        Returns:
            {
                'report': str,
                'sentiment_score': float (0-100),
                'sentiment_level': str,
                'flow_analysis': dict,
                'heat_analysis': dict,
                'fear_greed_index': float,
                'warnings': list,
                'key_findings': list
            }
        """
        print(f"\n💭 [{self.role}] 开始市场情绪分析...")
        
        # Extract data
        df = context.get('historical_data')
        news_data = context.get('news_data', [])
        social_data = context.get('social_data', {})
        flow_data = context.get('flow_data', {})
        
        # Analyze different sentiment dimensions
        price_sentiment = self._analyze_price_sentiment(df)
        volume_sentiment = self._analyze_volume_sentiment(df)
        news_sentiment = self._analyze_news_sentiment(news_data)
        flow_analysis = self._analyze_capital_flow(df, flow_data)
        
        # Calculate comprehensive sentiment score
        sentiment_score, sentiment_level = self._calculate_overall_sentiment(
            price_sentiment,
            volume_sentiment,
            news_sentiment,
            flow_analysis
        )
        
        # Calculate fear & greed index
        fear_greed_index = self._calculate_fear_greed_index(
            price_sentiment,
            volume_sentiment,
            sentiment_score
        )
        
        # Analyze heat map
        heat_analysis = self._analyze_market_heat(df, volume_sentiment)
        
        # Generate warnings
        warnings = self._generate_warnings(sentiment_score, fear_greed_index, flow_analysis)
        
        # Generate LLM analysis
        prompt = self._build_analysis_prompt(
            sentiment_score,
            sentiment_level,
            price_sentiment,
            volume_sentiment,
            news_sentiment,
            flow_analysis,
            fear_greed_index,
            heat_analysis,
            warnings
        )
        report = self._generate_response(prompt)
        
        # Extract key findings
        key_findings = self._extract_key_findings(
            sentiment_score,
            sentiment_level,
            fear_greed_index,
            warnings
        )
        
        result = {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'sentiment_score': sentiment_score,
            'sentiment_level': sentiment_level,
            'price_sentiment': price_sentiment,
            'volume_sentiment': volume_sentiment,
            'news_sentiment': news_sentiment,
            'flow_analysis': flow_analysis,
            'fear_greed_index': fear_greed_index,
            'heat_analysis': heat_analysis,
            'warnings': warnings,
            'key_findings': key_findings
        }
        
        print(f"✅ [{self.role}] 情绪分析完成 - 情绪: {sentiment_level}, 评分: {sentiment_score:.1f}/100")
        return result
    
    def _analyze_price_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sentiment from price action."""
        sentiment = {
            'score': 50,
            'trend': 'NEUTRAL',
            'momentum': 0,
            'signals': []
        }
        
        if df is None or df.empty:
            return sentiment
        
        try:
            close = df['close_price'].values
            
            # Calculate returns
            returns = pd.Series(close).pct_change()
            recent_return = returns.tail(5).mean() * 100
            
            # Momentum
            if len(close) >= 20:
                momentum = (close[-1] / close[-20] - 1) * 100
                sentiment['momentum'] = float(momentum)
                
                # Determine trend
                if momentum > 5:
                    sentiment['trend'] = 'BULLISH'
                    sentiment['score'] = min(100, 50 + momentum * 2)
                    sentiment['signals'].append(f"价格上涨趋势明显({momentum:.1f}%)")
                elif momentum < -5:
                    sentiment['trend'] = 'BEARISH'
                    sentiment['score'] = max(0, 50 + momentum * 2)
                    sentiment['signals'].append(f"价格下跌趋势明显({momentum:.1f}%)")
                else:
                    sentiment['trend'] = 'NEUTRAL'
                    sentiment['score'] = 50 + momentum * 2
            
            # Volatility impact
            volatility = returns.std() * 100
            if volatility > 5:
                sentiment['score'] = max(0, sentiment['score'] - 10)
                sentiment['signals'].append(f"价格波动剧烈({volatility:.1f}%), 市场不确定性高")
            
            # Recent price action
            if recent_return > 2:
                sentiment['signals'].append("近期价格加速上涨，市场热情高涨")
            elif recent_return < -2:
                sentiment['signals'].append("近期价格加速下跌，市场恐慌情绪蔓延")
        
        except Exception as e:
            print(f"⚠️  价格情绪分析时出错: {e}")
        
        return sentiment
    
    def _analyze_volume_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sentiment from volume patterns."""
        sentiment = {
            'score': 50,
            'activity': 'NORMAL',
            'trend': 'STABLE',
            'signals': []
        }
        
        if df is None or df.empty or 'volume' not in df.columns:
            return sentiment
        
        try:
            volume = df['volume'].values
            
            if len(volume) >= 20:
                recent_vol = np.mean(volume[-5:])
                historic_vol = np.mean(volume[-20:-5])
                
                if historic_vol > 0:
                    vol_ratio = recent_vol / historic_vol
                    
                    # Activity level
                    if vol_ratio > 1.5:
                        sentiment['activity'] = 'HIGH'
                        sentiment['score'] = 70
                        sentiment['signals'].append(f"成交量激增({vol_ratio:.1f}x), 市场参与度大幅提升")
                    elif vol_ratio > 1.2:
                        sentiment['activity'] = 'ABOVE_NORMAL'
                        sentiment['score'] = 60
                        sentiment['signals'].append(f"成交量放大({vol_ratio:.1f}x), 市场活跃度上升")
                    elif vol_ratio < 0.7:
                        sentiment['activity'] = 'LOW'
                        sentiment['score'] = 35
                        sentiment['signals'].append(f"成交量萎缩({vol_ratio:.1f}x), 市场观望情绪浓厚")
                    elif vol_ratio < 0.85:
                        sentiment['activity'] = 'BELOW_NORMAL'
                        sentiment['score'] = 45
                        sentiment['signals'].append(f"成交量下降({vol_ratio:.1f}x), 市场热度降温")
                    else:
                        sentiment['activity'] = 'NORMAL'
                        sentiment['score'] = 50
                        sentiment['signals'].append("成交量平稳，市场保持正常交投")
                
                # Volume trend
                vol_trend = (volume[-1] - volume[-5]) / volume[-5] * 100 if volume[-5] != 0 else 0
                if vol_trend > 20:
                    sentiment['trend'] = 'INCREASING'
                    sentiment['signals'].append("量能持续放大，资金持续流入")
                elif vol_trend < -20:
                    sentiment['trend'] = 'DECREASING'
                    sentiment['signals'].append("量能持续萎缩，资金持续流出")
                else:
                    sentiment['trend'] = 'STABLE'
        
        except Exception as e:
            print(f"⚠️  成交量情绪分析时出错: {e}")
        
        return sentiment
    
    def _analyze_news_sentiment(self, news_data: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news and social media."""
        sentiment = {
            'score': 50,
            'polarity': 'NEUTRAL',
            'heat_level': 'NORMAL',
            'keywords': [],
            'signals': []
        }
        
        if not news_data:
            sentiment['signals'].append("暂无新闻数据")
            return sentiment
        
        # Simple sentiment analysis based on news count and content
        news_count = len(news_data)
        
        if news_count > 10:
            sentiment['heat_level'] = 'HIGH'
            sentiment['score'] = 65
            sentiment['signals'].append(f"新闻数量较多({news_count}条), 市场关注度高")
        elif news_count > 5:
            sentiment['heat_level'] = 'ABOVE_NORMAL'
            sentiment['score'] = 57
            sentiment['signals'].append(f"有一定新闻报道({news_count}条), 保持市场热度")
        elif news_count > 0:
            sentiment['heat_level'] = 'NORMAL'
            sentiment['score'] = 50
            sentiment['signals'].append(f"新闻数量正常({news_count}条)")
        else:
            sentiment['heat_level'] = 'LOW'
            sentiment['score'] = 40
            sentiment['signals'].append("新闻较少，市场关注度一般")
        
        # Extract keywords (simplified)
        all_text = " ".join([n.get('title', '') + " " + n.get('summary', '') for n in news_data])
        # In real implementation, use NLP for keyword extraction
        sentiment['keywords'] = ['市场动态', '价格波动', '交易活跃']
        
        return sentiment
    
    def _analyze_capital_flow(
        self,
        df: pd.DataFrame,
        flow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze capital flow patterns."""
        analysis = {
            'score': 50,
            'direction': 'NEUTRAL',
            'strength': 'MODERATE',
            'institutional_flow': 'N/A',
            'retail_flow': 'N/A',
            'signals': []
        }
        
        if df is None or df.empty:
            return analysis
        
        try:
            # Use volume and price to infer flow
            close = df['close_price'].values
            volume = df['volume'].values
            
            if len(close) >= 10 and len(volume) >= 10:
                # Calculate price-volume correlation
                recent_close = close[-10:]
                recent_volume = volume[-10:]
                
                correlation = np.corrcoef(recent_close, recent_volume)[0, 1]
                
                # Strong positive correlation: buying pressure
                # Strong negative correlation: selling pressure
                if correlation > 0.5:
                    analysis['direction'] = 'INFLOW'
                    analysis['strength'] = 'STRONG'
                    analysis['score'] = 70
                    analysis['signals'].append(f"价量齐升(相关性{correlation:.2f}), 买盘力量强劲")
                elif correlation > 0.2:
                    analysis['direction'] = 'INFLOW'
                    analysis['strength'] = 'MODERATE'
                    analysis['score'] = 60
                    analysis['signals'].append(f"资金温和流入(相关性{correlation:.2f})")
                elif correlation < -0.5:
                    analysis['direction'] = 'OUTFLOW'
                    analysis['strength'] = 'STRONG'
                    analysis['score'] = 30
                    analysis['signals'].append(f"价量背离(相关性{correlation:.2f}), 卖盘力量强劲")
                elif correlation < -0.2:
                    analysis['direction'] = 'OUTFLOW'
                    analysis['strength'] = 'MODERATE'
                    analysis['score'] = 40
                    analysis['signals'].append(f"资金温和流出(相关性{correlation:.2f})")
                else:
                    analysis['direction'] = 'NEUTRAL'
                    analysis['strength'] = 'WEAK'
                    analysis['score'] = 50
                    analysis['signals'].append(f"资金流向不明显(相关性{correlation:.2f})")
                
                # Volume change
                vol_change = (volume[-1] / np.mean(volume[-10:-1]) - 1) * 100
                if vol_change > 50:
                    analysis['signals'].append(f"单日放量({vol_change:.1f}%), 大资金活跃")
                elif vol_change < -30:
                    analysis['signals'].append(f"单日缩量({vol_change:.1f}%), 资金观望")
        
        except Exception as e:
            print(f"⚠️  资金流向分析时出错: {e}")
        
        # Add external flow data if available
        if flow_data:
            analysis['institutional_flow'] = flow_data.get('institutional', 'N/A')
            analysis['retail_flow'] = flow_data.get('retail', 'N/A')
        
        return analysis
    
    def _calculate_overall_sentiment(
        self,
        price_sentiment: Dict,
        volume_sentiment: Dict,
        news_sentiment: Dict,
        flow_analysis: Dict
    ) -> tuple:
        """Calculate overall sentiment score and level."""
        # Weighted average
        weights = {
            'price': 0.35,
            'volume': 0.25,
            'news': 0.20,
            'flow': 0.20
        }
        
        score = (
            price_sentiment['score'] * weights['price'] +
            volume_sentiment['score'] * weights['volume'] +
            news_sentiment['score'] * weights['news'] +
            flow_analysis['score'] * weights['flow']
        )
        
        # Determine level
        if score >= 75:
            level = 'EXTREME_GREED'
        elif score >= 60:
            level = 'GREED'
        elif score >= 45:
            level = 'NEUTRAL'
        elif score >= 30:
            level = 'FEAR'
        else:
            level = 'EXTREME_FEAR'
        
        return score, level
    
    def _calculate_fear_greed_index(
        self,
        price_sentiment: Dict,
        volume_sentiment: Dict,
        overall_score: float
    ) -> float:
        """Calculate fear & greed index (0-100)."""
        # Use overall score as base
        index = overall_score
        
        # Adjust based on volatility (high volatility -> more fear)
        momentum = price_sentiment.get('momentum', 0)
        if abs(momentum) > 10:
            # Extreme movement increases fear
            index = index * 0.9
        
        # Volume impact
        if volume_sentiment['activity'] in ['HIGH', 'ABOVE_NORMAL']:
            # High activity can indicate greed or panic
            if momentum > 0:
                index = min(100, index * 1.1)  # Greed
            else:
                index = max(0, index * 0.9)  # Fear
        
        return float(np.clip(index, 0, 100))
    
    def _analyze_market_heat(
        self,
        df: pd.DataFrame,
        volume_sentiment: Dict
    ) -> Dict[str, Any]:
        """Analyze market heat/coolness."""
        heat_map = {
            'overall_heat': 50,
            'heat_level': 'NORMAL',
            'trend': 'STABLE',
            'zones': {}
        }
        
        if df is None or df.empty:
            return heat_map
        
        # Use volume activity as proxy for heat
        vol_score = volume_sentiment['score']
        
        if vol_score >= 70:
            heat_map['overall_heat'] = 85
            heat_map['heat_level'] = 'VERY_HOT'
            heat_map['trend'] = 'HEATING'
        elif vol_score >= 60:
            heat_map['overall_heat'] = 70
            heat_map['heat_level'] = 'HOT'
            heat_map['trend'] = 'HEATING'
        elif vol_score <= 35:
            heat_map['overall_heat'] = 25
            heat_map['heat_level'] = 'COLD'
            heat_map['trend'] = 'COOLING'
        elif vol_score <= 45:
            heat_map['overall_heat'] = 40
            heat_map['heat_level'] = 'COOL'
            heat_map['trend'] = 'COOLING'
        else:
            heat_map['overall_heat'] = 50
            heat_map['heat_level'] = 'NORMAL'
            heat_map['trend'] = 'STABLE'
        
        return heat_map
    
    def _generate_warnings(
        self,
        sentiment_score: float,
        fear_greed_index: float,
        flow_analysis: Dict
    ) -> List[str]:
        """Generate risk warnings based on sentiment analysis."""
        warnings = []
        
        # Extreme sentiment warnings
        if sentiment_score >= 80:
            warnings.append("⚠️  市场情绪过度狂热，警惕回调风险")
        elif sentiment_score <= 20:
            warnings.append("⚠️  市场情绪过度恐慌，可能存在超卖机会")
        
        # Fear & greed warnings
        if fear_greed_index >= 85:
            warnings.append("⚠️  贪婪指数极高，市场可能过热")
        elif fear_greed_index <= 15:
            warnings.append("⚠️  恐慌指数极高，市场可能超跌")
        
        # Capital flow warnings
        if flow_analysis['direction'] == 'OUTFLOW' and flow_analysis['strength'] == 'STRONG':
            warnings.append("⚠️  资金大幅流出，注意止损")
        
        if not warnings:
            warnings.append("✓ 当前无极端情绪预警")
        
        return warnings
    
    def _build_analysis_prompt(
        self,
        sentiment_score: float,
        sentiment_level: str,
        price_sentiment: Dict,
        volume_sentiment: Dict,
        news_sentiment: Dict,
        flow_analysis: Dict,
        fear_greed_index: float,
        heat_analysis: Dict,
        warnings: List[str]
    ) -> str:
        """Build prompt for LLM analysis."""
        prompt = f"""# 市场情绪分析报告

## 一、综合情绪评估

- **情绪评分**: {sentiment_score:.1f}/100
- **情绪等级**: **{sentiment_level}**
- **恐慌/贪婪指数**: {fear_greed_index:.1f}/100
- **市场热度**: {heat_analysis['heat_level']} ({heat_analysis['overall_heat']}/100)

## 二、价格情绪分析

- 趋势: **{price_sentiment['trend']}**
- 动量: {price_sentiment['momentum']:.2f}%
- 情绪评分: {price_sentiment['score']:.1f}/100

### 关键信号
"""
        for signal in price_sentiment['signals']:
            prompt += f"- {signal}\n"
        
        prompt += f"""
## 三、成交量情绪分析

- 活跃度: **{volume_sentiment['activity']}**
- 趋势: **{volume_sentiment['trend']}**
- 情绪评分: {volume_sentiment['score']:.1f}/100

### 关键信号
"""
        for signal in volume_sentiment['signals']:
            prompt += f"- {signal}\n"
        
        prompt += f"""
## 四、舆情热度分析

- 热度等级: **{news_sentiment['heat_level']}**
- 情绪倾向: **{news_sentiment['polarity']}**
- 情绪评分: {news_sentiment['score']:.1f}/100

### 关键信号
"""
        for signal in news_sentiment['signals']:
            prompt += f"- {signal}\n"
        
        prompt += f"""
## 五、资金流向分析

- 流向: **{flow_analysis['direction']}**
- 强度: **{flow_analysis['strength']}**
- 情绪评分: {flow_analysis['score']:.1f}/100
- 机构资金: {flow_analysis['institutional_flow']}
- 散户资金: {flow_analysis['retail_flow']}

### 关键信号
"""
        for signal in flow_analysis['signals']:
            prompt += f"- {signal}\n"
        
        prompt += "\n## 六、风险预警\n\n"
        for warning in warnings:
            prompt += f"{warning}\n"
        
        prompt += """
---

请基于以上市场情绪数据，从情绪分析师的角度进行深度分析：
1. 解读当前市场情绪的整体状态和演变趋势
2. 分析价格、成交量、舆情、资金四个维度的情绪信号
3. 识别市场参与者的行为特征（恐慌、贪婪、理性）
4. 评估情绪极端化风险和潜在拐点
5. 给出基于情绪分析的交易建议和风险提示

要求：
- 报告必须简洁自然，控制在500字以内
- 善于捕捉微妙的情绪变化
- 区分短期情绪波动和中长期趋势
- 识别从众效应和羊群行为
- 预警情绪极端化风险
- 给出明确的情绪交易策略
"""
        return prompt
    
    def _extract_key_findings(
        self,
        sentiment_score: float,
        sentiment_level: str,
        fear_greed_index: float,
        warnings: List[str]
    ) -> List[str]:
        """Extract key findings from sentiment analysis."""
        findings = []
        
        findings.append(f"市场情绪: {sentiment_level}, 评分 {sentiment_score:.1f}/100")
        findings.append(f"恐慌贪婪指数: {fear_greed_index:.1f}/100")
        
        # Add top warnings
        for warning in warnings[:2]:
            findings.append(warning.replace("⚠️  ", "").replace("✓ ", ""))
        
        return findings
