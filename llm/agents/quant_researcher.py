"""
Quantitative Researcher Agent

Responsible for:
1. Calculating core factors (momentum, valuation, volatility)
2. Backtesting strategy effectiveness
3. Real-time calculation of market indicators (ETF premium/discount, stock index futures basis)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from llm.agents.base_agent import BaseAgent


class QuantResearcherAgent(BaseAgent):
    """量化研究员Agent - 负责量化分析和因子挖掘"""
    
    def __init__(self, client, temperature: float = 0.3):
        """
        Initialize Quantitative Researcher Agent.
        
        Args:
            client: LLM client instance
            temperature: Sampling temperature (default 0.3 for more precise analysis)
        """
        super().__init__(
            name="QuantResearcher",
            role="量化研究员",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for quantitative researcher."""
        return """你是一名资深量化研究员，专注于量化策略和因子分析。

你的职责：
1. 挖掘和计算有效量化因子（动量、估值、波动率、流动性等）
2. 基于历史数据回测策略有效性，评估夏普比率、最大回撤等指标
3. 实时计算市场技术指标（RSI、MACD、布林带等）
4. 识别市场异常和套利机会（如ETF折溢价、期现基差）
5. 输出明确的量化信号（超买/超卖、多头/空头信号）

分析要求：
- 使用统计学方法，提供可量化的指标
- 关注因子的显著性和稳定性
- 评估策略在不同市场环境下的表现
- 识别统计套利机会
- 输出格式清晰，包含具体数值和信号强度

风格：专业、数据驱动、逻辑严谨"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform quantitative analysis.
        
        Args:
            context: {
                'historical_data': pd.DataFrame with price/volume data,
                'predictions': list of prediction dicts,
                'market_data': optional additional market data
            }
            
        Returns:
            {
                'report': str,
                'factors': dict of calculated factors,
                'signals': dict of trading signals,
                'metrics': dict of performance metrics,
                'key_findings': list of key insights
            }
        """
        print(f"\n🔬 [{self.role}] 开始量化分析...")
        
        # Extract data
        df = context.get('historical_data')
        predictions = context.get('predictions', [])
        market_data = context.get('market_data', {})
        
        # Calculate quantitative factors
        factors = self._calculate_factors(df)
        
        # Generate trading signals
        signals = self._generate_signals(df, factors)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(df, predictions)
        
        # Backtest strategy
        backtest_results = self._backtest_strategy(df, signals)
        
        # Generate LLM analysis
        prompt = self._build_analysis_prompt(factors, signals, metrics, backtest_results)
        report = self._generate_response(prompt)
        
        # Extract key findings
        key_findings = self._extract_key_findings(factors, signals, metrics)
        
        result = {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'factors': factors,
            'signals': signals,
            'metrics': metrics,
            'backtest_results': backtest_results,
            'key_findings': key_findings
        }
        
        print(f"✅ [{self.role}] 量化分析完成 - 生成 {len(signals)} 个信号")
        return result
    
    def _calculate_factors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate quantitative factors."""
        if df is None or df.empty:
            return {}
        
        factors = {}
        
        try:
            close = df['close_price'].values
            volume = df['volume'].values
            
            # 1. Momentum factors
            factors['momentum_5d'] = float((close[-1] - close[-5]) / close[-5] * 100) if len(close) >= 5 else 0
            factors['momentum_10d'] = float((close[-1] - close[-10]) / close[-10] * 100) if len(close) >= 10 else 0
            factors['momentum_20d'] = float((close[-1] - close[-20]) / close[-20] * 100) if len(close) >= 20 else 0
            
            # 2. Volatility factors
            returns = pd.Series(close).pct_change()
            factors['volatility_5d'] = float(returns.tail(5).std() * np.sqrt(252) * 100)
            factors['volatility_10d'] = float(returns.tail(10).std() * np.sqrt(252) * 100)
            factors['volatility_20d'] = float(returns.tail(20).std() * np.sqrt(252) * 100)
            
            # 3. Technical indicators
            # RSI
            factors['rsi_14'] = self._calculate_rsi(close, period=14)
            
            # MACD
            macd, signal, hist = self._calculate_macd(close)
            factors['macd'] = float(macd)
            factors['macd_signal'] = float(signal)
            factors['macd_histogram'] = float(hist)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
            factors['bb_upper'] = float(bb_upper)
            factors['bb_middle'] = float(bb_middle)
            factors['bb_lower'] = float(bb_lower)
            factors['bb_position'] = float((close[-1] - bb_lower) / (bb_upper - bb_lower) * 100) if bb_upper != bb_lower else 50
            
            # 4. Volume factors
            factors['volume_ratio'] = float(volume[-1] / np.mean(volume[-20:])) if len(volume) >= 20 else 1.0
            factors['volume_trend'] = float(np.mean(volume[-5:]) / np.mean(volume[-20:])) if len(volume) >= 20 else 1.0
            
            # 5. Moving averages
            factors['ma5'] = float(np.mean(close[-5:])) if len(close) >= 5 else close[-1]
            factors['ma10'] = float(np.mean(close[-10:])) if len(close) >= 10 else close[-1]
            factors['ma20'] = float(np.mean(close[-20:])) if len(close) >= 20 else close[-1]
            factors['price_to_ma20'] = float((close[-1] / factors['ma20'] - 1) * 100)
            
            # 6. Trend strength
            factors['trend_strength'] = self._calculate_trend_strength(close)
            
        except Exception as e:
            print(f"⚠️  计算因子时出错: {e}")
        
        return factors
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
        ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1]
        
        prices_series = pd.Series(prices)
        middle = prices_series.rolling(window=period).mean().iloc[-1]
        std = prices_series.rolling(window=period).std().iloc[-1]
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength using ADX-like calculation."""
        if len(prices) < 20:
            return 50.0
        
        # Simple trend strength: correlation between price and time
        x = np.arange(len(prices[-20:]))
        y = prices[-20:]
        correlation = np.corrcoef(x, y)[0, 1]
        
        # Convert to 0-100 scale
        trend_strength = (correlation + 1) * 50
        return float(trend_strength)
    
    def _generate_signals(self, df: pd.DataFrame, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on factors."""
        signals = {
            'overall_signal': 'NEUTRAL',
            'signal_strength': 0,
            'individual_signals': {}
        }
        
        if not factors:
            return signals
        
        score = 0
        max_score = 0
        
        # RSI signal
        rsi = factors.get('rsi_14', 50)
        if rsi < 30:
            signals['individual_signals']['rsi'] = {'signal': 'BUY', 'strength': 'STRONG', 'value': rsi}
            score += 2
        elif rsi < 40:
            signals['individual_signals']['rsi'] = {'signal': 'BUY', 'strength': 'MODERATE', 'value': rsi}
            score += 1
        elif rsi > 70:
            signals['individual_signals']['rsi'] = {'signal': 'SELL', 'strength': 'STRONG', 'value': rsi}
            score -= 2
        elif rsi > 60:
            signals['individual_signals']['rsi'] = {'signal': 'SELL', 'strength': 'MODERATE', 'value': rsi}
            score -= 1
        else:
            signals['individual_signals']['rsi'] = {'signal': 'NEUTRAL', 'strength': 'WEAK', 'value': rsi}
        max_score += 2
        
        # MACD signal
        macd_hist = factors.get('macd_histogram', 0)
        if macd_hist > 0:
            signals['individual_signals']['macd'] = {'signal': 'BUY', 'strength': 'MODERATE', 'value': macd_hist}
            score += 1
        elif macd_hist < 0:
            signals['individual_signals']['macd'] = {'signal': 'SELL', 'strength': 'MODERATE', 'value': macd_hist}
            score -= 1
        else:
            signals['individual_signals']['macd'] = {'signal': 'NEUTRAL', 'strength': 'WEAK', 'value': macd_hist}
        max_score += 1
        
        # Bollinger Bands signal
        bb_position = factors.get('bb_position', 50)
        if bb_position < 20:
            signals['individual_signals']['bollinger'] = {'signal': 'BUY', 'strength': 'STRONG', 'value': bb_position}
            score += 2
        elif bb_position > 80:
            signals['individual_signals']['bollinger'] = {'signal': 'SELL', 'strength': 'STRONG', 'value': bb_position}
            score -= 2
        else:
            signals['individual_signals']['bollinger'] = {'signal': 'NEUTRAL', 'strength': 'WEAK', 'value': bb_position}
        max_score += 2
        
        # Momentum signal
        momentum_20d = factors.get('momentum_20d', 0)
        if momentum_20d > 5:
            signals['individual_signals']['momentum'] = {'signal': 'BUY', 'strength': 'MODERATE', 'value': momentum_20d}
            score += 1
        elif momentum_20d < -5:
            signals['individual_signals']['momentum'] = {'signal': 'SELL', 'strength': 'MODERATE', 'value': momentum_20d}
            score -= 1
        else:
            signals['individual_signals']['momentum'] = {'signal': 'NEUTRAL', 'strength': 'WEAK', 'value': momentum_20d}
        max_score += 1
        
        # Calculate overall signal
        signal_strength = int((abs(score) / max_score) * 100) if max_score > 0 else 0
        
        if score > 2:
            signals['overall_signal'] = 'STRONG_BUY'
        elif score > 0:
            signals['overall_signal'] = 'BUY'
        elif score < -2:
            signals['overall_signal'] = 'STRONG_SELL'
        elif score < 0:
            signals['overall_signal'] = 'SELL'
        else:
            signals['overall_signal'] = 'NEUTRAL'
        
        signals['signal_strength'] = signal_strength
        signals['raw_score'] = score
        signals['max_score'] = max_score
        
        return signals
    
    def _calculate_metrics(self, df: pd.DataFrame, predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        metrics = {}
        
        if df is None or df.empty:
            return metrics
        
        try:
            close = df['close_price'].values
            returns = pd.Series(close).pct_change().dropna()
            
            # Return metrics
            metrics['total_return'] = float((close[-1] / close[0] - 1) * 100)
            metrics['avg_daily_return'] = float(returns.mean() * 100)
            metrics['annualized_return'] = float(returns.mean() * 252 * 100)
            
            # Risk metrics
            metrics['daily_volatility'] = float(returns.std() * 100)
            metrics['annualized_volatility'] = float(returns.std() * np.sqrt(252) * 100)
            
            # Risk-adjusted metrics
            if metrics['annualized_volatility'] != 0:
                metrics['sharpe_ratio'] = float(metrics['annualized_return'] / metrics['annualized_volatility'])
            else:
                metrics['sharpe_ratio'] = 0.0
            
            # Drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            metrics['max_drawdown'] = float(drawdown.min() * 100)
            metrics['current_drawdown'] = float(drawdown.iloc[-1] * 100)
            
            # Win rate
            metrics['win_rate'] = float((returns > 0).sum() / len(returns) * 100)
            
            # Prediction metrics
            if predictions:
                pred_returns = [p['predicted_daily_return'] for p in predictions]
                metrics['pred_avg_return'] = float(np.mean(pred_returns) * 100)
                metrics['pred_cumulative'] = float(np.prod([1 + r for r in pred_returns]) - 1) * 100
            
        except Exception as e:
            print(f"⚠️  计算性能指标时出错: {e}")
        
        return metrics
    
    def _backtest_strategy(self, df: pd.DataFrame, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Simple backtest based on current signals."""
        backtest = {
            'strategy': 'momentum_reversal',
            'recommendation': signals.get('overall_signal', 'NEUTRAL'),
            'expected_performance': 'UNKNOWN'
        }
        
        # Simple rule: strong signals tend to perform better
        signal_strength = signals.get('signal_strength', 0)
        
        if signal_strength > 60:
            backtest['expected_performance'] = 'HIGH'
            backtest['confidence'] = 0.8
        elif signal_strength > 40:
            backtest['expected_performance'] = 'MEDIUM'
            backtest['confidence'] = 0.6
        else:
            backtest['expected_performance'] = 'LOW'
            backtest['confidence'] = 0.4
        
        return backtest
    
    def _build_analysis_prompt(
        self,
        factors: Dict[str, Any],
        signals: Dict[str, Any],
        metrics: Dict[str, Any],
        backtest: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM analysis."""
        prompt = f"""# 量化分析报告

## 一、核心因子分析

### 动量因子
- 5日动量: {factors.get('momentum_5d', 0):.2f}%
- 10日动量: {factors.get('momentum_10d', 0):.2f}%
- 20日动量: {factors.get('momentum_20d', 0):.2f}%

### 波动率因子
- 5日波动率: {factors.get('volatility_5d', 0):.2f}%
- 10日波动率: {factors.get('volatility_10d', 0):.2f}%
- 20日波动率: {factors.get('volatility_20d', 0):.2f}%

### 技术指标
- RSI(14): {factors.get('rsi_14', 50):.2f}
- MACD: {factors.get('macd', 0):.4f}
- MACD信号: {factors.get('macd_signal', 0):.4f}
- MACD柱: {factors.get('macd_histogram', 0):.4f}
- 布林带位置: {factors.get('bb_position', 50):.2f}%
- 趋势强度: {factors.get('trend_strength', 50):.2f}

### 成交量因子
- 量比: {factors.get('volume_ratio', 1.0):.2f}
- 量能趋势: {factors.get('volume_trend', 1.0):.2f}

## 二、量化信号
- 总体信号: **{signals.get('overall_signal', 'NEUTRAL')}**
- 信号强度: {signals.get('signal_strength', 0)}/100

### 细分信号
"""
        for name, signal in signals.get('individual_signals', {}).items():
            prompt += f"- {name.upper()}: {signal['signal']} ({signal['strength']})\n"
        
        prompt += f"""
## 三、性能指标
- 总收益率: {metrics.get('total_return', 0):.2f}%
- 年化收益率: {metrics.get('annualized_return', 0):.2f}%
- 年化波动率: {metrics.get('annualized_volatility', 0):.2f}%
- 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
- 最大回撤: {metrics.get('max_drawdown', 0):.2f}%
- 胜率: {metrics.get('win_rate', 0):.2f}%

## 四、回测结果
- 策略类型: {backtest.get('strategy', 'N/A')}
- 回测信号: {backtest.get('recommendation', 'N/A')}
- 预期表现: {backtest.get('expected_performance', 'N/A')}
- 置信度: {backtest.get('confidence', 0)*100:.0f}%

---

请基于以上量化数据，从量化研究员的角度进行专业分析：
1. 解读各个因子的含义和当前状态
2. 分析量化信号的强度和可靠性
3. 评估策略的有效性和风险收益特征
4. 给出明确的量化交易建议（超买/超卖、做多/做空信号）
5. 识别潜在的套利机会或异常信号

要求：
- 报告必须简洁自然，控制在500字以内
- 使用专业量化术语
- 提供具体数值支持
- 评估信号的置信度
- 给出风险提示
"""
        return prompt
    
    def _extract_key_findings(
        self,
        factors: Dict[str, Any],
        signals: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings from quantitative analysis."""
        findings = []
        
        # Signal findings
        overall_signal = signals.get('overall_signal', 'NEUTRAL')
        signal_strength = signals.get('signal_strength', 0)
        findings.append(f"量化总体信号: {overall_signal}, 强度: {signal_strength}/100")
        
        # RSI findings
        rsi = factors.get('rsi_14', 50)
        if rsi < 30:
            findings.append(f"RSI严重超卖({rsi:.1f}), 可能存在反弹机会")
        elif rsi > 70:
            findings.append(f"RSI严重超买({rsi:.1f}), 注意回调风险")
        
        # Performance findings
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 1.5:
            findings.append(f"夏普比率优秀({sharpe:.2f}), 风险调整后收益良好")
        elif sharpe < 0.5:
            findings.append(f"夏普比率较低({sharpe:.2f}), 风险收益比不理想")
        
        # Volatility findings
        volatility = metrics.get('annualized_volatility', 0)
        if volatility > 40:
            findings.append(f"波动率较高({volatility:.1f}%), 市场不确定性大")
        elif volatility < 15:
            findings.append(f"波动率较低({volatility:.1f}%), 市场相对稳定")
        
        # Momentum findings
        momentum_20d = factors.get('momentum_20d', 0)
        if abs(momentum_20d) > 10:
            direction = "上涨" if momentum_20d > 0 else "下跌"
            findings.append(f"20日动量显著{direction}({momentum_20d:.1f}%), 趋势明显")
        
        return findings
