"""
Simple and Clear Market Analysis Workflow

This module provides a streamlined market analysis with:
- Clear, data-driven insights
- No jargon, easy to understand
- Quick to read (< 30 seconds)
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from llm.clients.gemini_client import GeminiClient
from llm.clients.doubao_client import DoubaoClient


class SimpleMarketAnalyzer:
    """简洁的市场分析器 - 基于真实数据，通俗易懂"""
    
    def __init__(self, llm_config: dict):
        """
        Initialize simple analyzer.
        
        Args:
            llm_config: Configuration dictionary for LLM
        """
        self.config = llm_config
        provider = self.config.get('llm', {}).get('provider', 'google')
        model_name = self.config.get('llm', {}).get('model', 'gemini-2.0-flash-exp')
        api_key = self.config.get('llm', {}).get('api_key')

        if not api_key:
            raise ValueError("API key not found in configuration")

        # Initialize LLM client
        if provider.lower() == 'google':
            self.client = GeminiClient(api_key=api_key, model_name=model_name)
        elif provider.lower() == 'doubao':
            self.client = DoubaoClient(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        print("✅ 简洁分析器初始化完成")
    
    def analyze(
        self,
        historical_data: pd.DataFrame,
        predictions: list,
        chart_path: str
    ) -> Dict[str, Any]:
        """
        Analyze market with simple, clear output.
        
        Args:
            historical_data: DataFrame with historical kline data
            predictions: List of prediction dicts
            chart_path: Path to prediction chart
            
        Returns:
            Analysis results with clear insights
        """
        print("\n" + "="*80)
        print("🚀 启动简洁市场分析")
        print("="*80)
        
        start_time = time.time()
        
        # Step 1: Calculate real market metrics (no LLM involved)
        print("\n📊 计算市场指标...")
        metrics = self._calculate_market_metrics(historical_data, predictions)
        
        # Step 2: Generate simple summary with LLM
        print("\n💡 生成市场洞察...")
        insights = self._generate_insights(metrics, historical_data)
        
        # Step 3: Build simple report
        print("\n📝 构建简洁报告...")
        report = self._build_simple_report(metrics, insights, chart_path)
        
        total_time = time.time() - start_time
        
        result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': metrics,
            'insights': insights,
            'report': report,
            'execution_time': total_time
        }
        
        print(f"\n✅ 分析完成 - 耗时: {total_time:.2f}秒")
        print("="*80)
        
        return result
    
    def _calculate_market_metrics(self, df: pd.DataFrame, predictions: list) -> Dict[str, Any]:
        """Calculate all market metrics based on real data."""
        
        price_col = self._get_column(df, ['close', 'close_price'])
        volume_col = self._get_column(df, ['volume', 'volume_usdt'], required=False)

        price_series = df[price_col].astype(float)
        latest = df.iloc[-1]
        current_price = float(latest[price_col])
        
        # Price metrics
        price_20d_ago = float(df.iloc[-20][price_col]) if len(df) >= 20 else current_price
        price_change_20d = ((current_price - price_20d_ago) / price_20d_ago * 100)
        
        # Calculate price percentile
        all_prices = price_series.values
        price_percentile = (all_prices < current_price).sum() / len(all_prices) * 100
        
        # Moving averages
        ma5 = price_series.tail(5).mean()
        ma20 = price_series.tail(20).mean() if len(df) >= 20 else current_price
        ma60 = price_series.tail(60).mean() if len(df) >= 60 else current_price
        
        # Volume metrics
        current_volume = float(latest.get(volume_col, 0)) if volume_col else 0
        if volume_col:
            avg_volume = df[volume_col].tail(20).mean()
        else:
            avg_volume = current_volume
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Technical indicators
        rsi = self._calculate_rsi(price_series, period=14)
        macd_line, signal_line, histogram = self._calculate_macd(price_series)
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(price_series)
        
        # Volatility
        returns = price_series.pct_change().dropna()
        volatility_20d = returns.tail(20).std() * np.sqrt(252) * 100  # Annualized
        
        # Prediction analysis
        pred_avg_return = np.mean([p.get('predicted_return', 0) for p in predictions]) if predictions else 0
        pred_direction = "上涨" if pred_avg_return > 0 else "下跌" if pred_avg_return < 0 else "持平"
        
        # Trend determination
        if current_price > ma5 > ma20:
            trend = "上涨"
            trend_emoji = "📈"
        elif current_price < ma5 < ma20:
            trend = "下跌"
            trend_emoji = "📉"
        else:
            trend = "震荡"
            trend_emoji = "↔️"
        
        # Market heat level
        if volume_ratio > 1.2:
            heat = "火热"
            heat_emoji = "🔥"
        elif volume_ratio > 0.9:
            heat = "正常"
            heat_emoji = "😊"
        else:
            heat = "冷清"
            heat_emoji = "❄️"
        
        # Sentiment score (based on technical indicators)
        sentiment_score = 50  # Start neutral
        if rsi < 30:
            sentiment_score += 20  # Oversold is positive
        elif rsi > 70:
            sentiment_score -= 20  # Overbought is negative
        
        if histogram > 0:
            sentiment_score += 10  # MACD bullish
        else:
            sentiment_score -= 10
        
        if current_price < bb_lower:
            sentiment_score += 10  # Below lower band
        elif current_price > bb_upper:
            sentiment_score -= 10
        
        sentiment_score = max(0, min(100, sentiment_score))  # Clamp to 0-100
        
        if sentiment_score >= 70:
            sentiment = "乐观"
            sentiment_emoji = "😄"
        elif sentiment_score >= 40:
            sentiment = "中性"
            sentiment_emoji = "😐"
        else:
            sentiment = "悲观"
            sentiment_emoji = "😟"
        
        return {
            'price': {
                'current': round(current_price, 2),
                'change_20d': round(price_change_20d, 2),
                'percentile': round(price_percentile, 0),
                'ma5': round(ma5, 2),
                'ma20': round(ma20, 2),
                'ma60': round(ma60, 2),
                'vs_ma20': round((current_price - ma20) / ma20 * 100, 2),
                'trend': trend,
                'trend_emoji': trend_emoji
            },
            'volume': {
                'current': int(current_volume),
                'avg_20d': int(avg_volume),
                'ratio': round(volume_ratio, 2),
                'change_pct': round((volume_ratio - 1) * 100, 0),
                'heat': heat,
                'heat_emoji': heat_emoji
            },
            'technical': {
                'rsi': round(rsi, 1),
                'macd_histogram': round(histogram, 2),
                'macd_signal': "金叉" if histogram > 0 else "死叉",
                'bb_position': round((current_price - bb_lower) / (bb_upper - bb_lower) * 100, 1) if bb_upper != bb_lower else 50,
                'volatility': round(volatility_20d, 1)
            },
            'sentiment': {
                'score': int(sentiment_score),
                'level': sentiment,
                'emoji': sentiment_emoji
            },
            'prediction': {
                'direction': pred_direction,
                'avg_return': round(pred_avg_return, 2),
                'days': len(predictions)
            },
            'risk': {
                'volatility_level': "极高" if volatility_20d > 100 else "高" if volatility_20d > 50 else "中等" if volatility_20d > 30 else "低",
                'volume_risk': "低迷" if volume_ratio < 0.8 else "正常",
            }
        }

    def _get_column(self, df: pd.DataFrame, candidates, required: bool = True) -> Optional[str]:
        """Return the first existing column name from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        if required:
            raise KeyError(f"None of the required columns found: {candidates}")
        return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def _calculate_macd(self, prices: pd.Series, fast=12, slow=26, signal=9):
        """Calculate MACD indicator."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper.iloc[-1], middle.iloc[-1], lower.iloc[-1]
    
    def _generate_insights(self, metrics: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate market insights using LLM."""
        
        # Build prompt with real data
        prompt = f"""基于以下真实市场数据，用一句话总结当前市场状态（不超过20字）：

当前价格: ¥{metrics['price']['current']}
20日涨跌: {metrics['price']['change_20d']:+.1f}%
价格位置: 历史{metrics['price']['percentile']:.0f}%分位
价格趋势: {metrics['price']['trend']}
成交量比: {metrics['volume']['ratio']:.2f}x（{metrics['volume']['heat']}）
市场情绪: {metrics['sentiment']['level']}（{metrics['sentiment']['score']}/100）
技术指标RSI: {metrics['technical']['rsi']:.1f}
预测方向: {metrics['prediction']['direction']}

要求：
1. 不要使用专业术语
2. 语言通俗易懂，像和朋友聊天
3. 一句话说清楚：价格贵不贵、人气旺不旺、该不该买
"""
        
        summary = self.client.generate(
            prompt=prompt,
            system_instruction="你是一个市场分析助手，用最简单的语言解释市场状态。避免使用专业术语。",
            temperature=0.3
        ).strip()
        
        # Generate action suggestion
        action_prompt = f"""基于市场数据，给出操作建议：

价格: ¥{metrics['price']['current']} ({metrics['price']['trend']})
成交量: {metrics['volume']['heat']}（比平时{metrics['volume']['change_pct']:+.0f}%）
情绪: {metrics['sentiment']['level']}（{metrics['sentiment']['score']}/100）
RSI: {metrics['technical']['rsi']:.1f}（30以下超卖，70以上超买）
波动率: {metrics['risk']['volatility_level']}

请给出：
1. 操作建议：买入/观望/卖出（选一个）
2. 信心度：0-100的整数
3. 简短理由：一句话说明原因（不超过30字）

格式示例：
操作建议: 观望
信心度: 65
理由: 价格便宜但人气不足，等成交量回升再买
"""
        
        action_response = self.client.generate(
            prompt=action_prompt,
            system_instruction="你是投资顾问，给出明确的操作建议。语言简洁通俗。",
            temperature=0.3
        )
        
        # Parse action response
        action = "观望"
        confidence = 50
        reason = "市场不明朗"
        
        for line in action_response.split('\n'):
            if '操作建议' in line or '建议' in line:
                if '买入' in line:
                    action = "买入"
                elif '卖出' in line:
                    action = "卖出"
                elif '观望' in line or '等待' in line:
                    action = "观望"
            elif '信心度' in line or '信心' in line:
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    confidence = int(numbers[0])
            elif '理由' in line:
                reason = line.split(':', 1)[-1].strip()
        
        return {
            'summary': summary,
            'action': action,
            'confidence': confidence,
            'reason': reason
        }
    
    def _build_simple_report(self, metrics: Dict[str, Any], insights: Dict[str, Any], chart_path: str) -> str:
        """Build simple, easy-to-read report."""
        
        m = metrics
        price = m['price']
        volume = m['volume']
        tech = m['technical']
        sentiment = m['sentiment']
        pred = m['prediction']
        risk = m['risk']
        
        # Determine what to watch for
        watch_items = []
        if tech['rsi'] < 30:
            watch_items.append(f"✓ RSI已经很低({tech['rsi']:.0f})，可能随时反弹")
        elif tech['rsi'] > 35 and tech['rsi'] < 45:
            watch_items.append(f"✓ RSI继续下跌到30以下（现在{tech['rsi']:.0f}）")
        
        if volume['ratio'] < 1.0:
            watch_items.append(f"✓ 成交量放大20%以上（现在比平时少{abs(volume['change_pct']):.0f}%）")
        
        if price['change_20d'] < 0:
            watch_items.append(f"✓ 连续3天价格不再下跌")
        
        # Generate buy/sell levels
        buy_price = round(price['current'] * 0.9, 2)  # 10% lower
        stop_loss = round(price['current'] * 0.9, 2)
        take_profit = round(price['current'] * 1.1, 2)  # 10% higher
        
        report = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUFF市场日报 - {datetime.now().strftime('%Y年%m月%d日')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 今日结论
{insights['summary']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 价格走势
当前价格: ¥{price['current']}
最近涨跌: 20天{price['change_20d']:+.1f}% {price['trend_emoji']}
历史位置: 处于历史{price['percentile']:.0f}%分位（{'便宜' if price['percentile'] < 30 else '正常' if price['percentile'] < 70 else '偏贵'}）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 市场热度
交易热度: {volume['heat_emoji']} {volume['heat']}（成交量比平时{volume['change_pct']:+.0f}%）
市场情绪: {sentiment['emoji']} {sentiment['level']} ({sentiment['score']}分/100分)
资金流向: {'💰 有资金流入' if volume['ratio'] > 0.9 else '💸 资金流出'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 风险提示
• 价格波动性: {risk['volatility_level']}
• 成交量状态: {risk['volume_risk']}
{'• 短期继续' + ('上涨' if price['change_20d'] > 0 else '下跌') + '的可能性存在' if abs(price['change_20d']) > 2 else '• 短期可能继续震荡'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 操作建议
{insights['action']} （信心度: {insights['confidence']}%）

{insights['reason']}

"""
        
        if insights['action'] == "观望":
            report += f"""什么时候可以考虑买入？
"""
            for item in watch_items[:3]:
                report += f"{item}\n"
            
            report += f"""
满足以上条件后可以考虑：
• 少量试水，投入不超过10%的资金
• 买入后设置止损在¥{stop_loss}
• 涨到¥{take_profit}先卖一部分锁定利润
"""
        
        elif insights['action'] == "买入":
            report += f"""建议买入方案：
• 分批买入，首次不超过总资金的10%
• 止损价格: ¥{stop_loss}（跌破果断卖出）
• 止盈价格: ¥{take_profit}（涨到先卖一半）
• 密切关注成交量变化
"""
        
        elif insights['action'] == "卖出":
            report += f"""建议卖出方案：
• 如果有持仓，建议逐步减仓
• 目标减仓至{max(0, 50 - insights['confidence'])}%或清仓
• 等待更好的买入时机
"""
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 技术参考（可选阅读）
RSI指标: {tech['rsi']:.1f} {'（超卖区）' if tech['rsi'] < 30 else '（超买区）' if tech['rsi'] > 70 else '（正常）'}
MACD: {tech['macd_signal']}
趋势: {price['trend']}
预测: 未来{pred['days']}天可能{pred['direction']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
本报告基于真实市场数据生成，仅供参考
"""
        
        return report
    
    def save_report(self, result: Dict[str, Any], output_dir: str = 'models') -> str:
        """Save analysis result to file."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = os.path.join(output_dir, f'simple_report_{timestamp}.json')
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 报告已保存: {json_path}")
        return json_path
