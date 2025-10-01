"""
Market Analyst Agent

Searches and analyzes market news and sentiment from various sources.
"""
import json
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
from llm.agents.base_agent import BaseAgent


class MarketAnalystAgent(BaseAgent):
    """Market Analyst agent for news and sentiment analysis."""
    
    def __init__(self, client, temperature: float = 0.5):
        """Initialize Market Analyst agent."""
        super().__init__(
            name="市场分析师",
            role="Market Analyst",
            client=client,
            temperature=temperature
        )
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for market analyst."""
        return """你是一名专业的市场分析师，专注于BUFF饰品市场及相关Steam游戏饰品交易生态。

你的职责：
1. 搜集和分析BUFF、悠悠优品、steam社区的最新动态
2. 识别影响市场的利好和利空消息
3. 评估新闻对市场情绪的影响
4. 分析竞争对手动态和行业趋势
5. 提供市场情绪和舆情分析

关注重点：
- BUFF平台政策变化、活动促销
- 悠悠优品的竞争动态
- Steam官方政策和游戏更新
- 热门游戏和饰品趋势
- 用户情绪和交易热度变化
- 监管政策和行业风险

分析维度：
- 利好因素（促进价格上涨）
- 利空因素（可能导致下跌）
- 中性事件（需持续观察）
- 影响程度（高/中/低）
- 时效性（即时/短期/长期）

输出格式：
提供结构化的市场情报报告，包含：
1. 最新市场动态汇总
2. 利好因素分析
3. 利空因素分析
4. 市场情绪评估
5. 投资建议倾向
"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market news and sentiment.
        
        Args:
            context: {
                'data_analyst_report': str - Report from data analyst,
                'search_enabled': bool - Whether to perform actual web search,
                'keywords': List[str] - Keywords to search for
            }
            
        Returns:
            {
                'report': str - Market analysis report,
                'news_items': List[Dict] - Collected news items,
                'sentiment': str - Overall market sentiment,
                'signals': Dict - Buy/sell/hold signals
            }
        """
        data_report = context.get('data_analyst_report', '')
        search_enabled = context.get('search_enabled', False)
        keywords = context.get('keywords', ['BUFF', '悠悠优品', 'steam饰品', 'CSGO饰品'])
        
        # Collect news (simulated or real)
        news_items = []
        if search_enabled:
            news_items = self._search_news(keywords)
        else:
            # Use simulated news for demo
            news_items = self._get_simulated_news()
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(data_report, news_items)
        
        # Generate analysis
        report = self._generate_response(prompt)
        
        # Extract sentiment and signals
        sentiment = self._extract_sentiment(report)
        signals = self._extract_signals(report)
        
        return {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'news_items': news_items,
            'sentiment': sentiment,
            'signals': signals
        }
    
    def _search_news(self, keywords: List[str]) -> List[Dict[str, str]]:
        """
        Search for news items (placeholder for actual web search).
        
        In production, this would use:
        - Google News API
        - Bing Search API
        - Web scraping of specific sites
        - RSS feeds
        """
        # TODO: Implement actual web search
        # For now, return simulated news
        return self._get_simulated_news()
    
    def _get_simulated_news(self) -> List[Dict[str, str]]:
        """Get simulated news for demonstration."""
        today = datetime.now().strftime('%Y-%m-%d')
        return [
            {
                'title': 'BUFF平台推出国庆限时优惠活动',
                'source': 'BUFF官方',
                'date': today,
                'summary': 'BUFF宣布国庆期间所有饰品交易手续费降低0.5%，预计将刺激交易活跃度。',
                'sentiment': 'positive',
                'impact': 'medium'
            },
            {
                'title': 'Steam更新反作弊系统VAC3.0',
                'source': 'Steam社区',
                'date': today,
                'summary': 'Valve发布新版反作弊系统，可能影响部分第三方交易平台的API接口稳定性。',
                'sentiment': 'neutral',
                'impact': 'low'
            },
            {
                'title': 'CS2新箱子即将发布',
                'source': '游戏媒体',
                'date': today,
                'summary': 'Counter-Strike 2将在下周发布新武器箱，可能带动老箱子价格波动。',
                'sentiment': 'positive',
                'impact': 'high'
            },
            {
                'title': '悠悠优品调整平台费率结构',
                'source': '悠悠优品',
                'date': today,
                'summary': '竞争对手悠悠优品宣布调整部分商品的交易费率，可能影响用户选择。',
                'sentiment': 'negative',
                'impact': 'medium'
            },
            {
                'title': '电竞赛事Major即将开赛',
                'source': '电竞资讯',
                'date': today,
                'summary': 'CS2 Major锦标赛下月举行，历史数据显示赛事期间饰品交易量通常上升20-30%。',
                'sentiment': 'positive',
                'impact': 'high'
            }
        ]
    
    def _build_analysis_prompt(self, data_report: str, news_items: List[Dict]) -> str:
        """Build prompt for market analysis."""
        
        # Format news items
        news_summary = "最新市场资讯：\n\n"
        for i, item in enumerate(news_items, 1):
            news_summary += f"{i}. 【{item.get('source', '未知来源')}】{item.get('title', '')}\n"
            news_summary += f"   日期: {item.get('date', '')}\n"
            news_summary += f"   内容: {item.get('summary', '')}\n"
            news_summary += f"   情绪倾向: {item.get('sentiment', 'neutral')} | 影响程度: {item.get('impact', 'medium')}\n\n"
        
        prompt = f"""请基于以下信息进行市场分析：

【数据分析师报告摘要】
{data_report[:500] if len(data_report) > 500 else data_report}
...（完整报告已参考）

【市场资讯】
{news_summary}

请提供一份专业的市场分析报告，包括：

1. 【市场动态概览】- 总结当前市场的主要新闻和事件

2. 【利好因素分析】
   - 列举所有利好消息
   - 分析对市场的积极影响
   - 评估影响的持续时间和强度

3. 【利空因素分析】
   - 列举所有利空或风险因素
   - 分析可能的负面影响
   - 评估风险程度

4. 【市场情绪评估】
   - 综合判断当前市场情绪（乐观/中性/悲观）
   - 分析情绪对短期走势的影响

5. 【投资建议倾向】
   - 基于新闻和数据，给出初步的市场观点
   - 建议是偏向看多、看空还是观望
   - 需要关注的关键指标或事件

请保持专业、客观，综合考虑多方面因素。
"""
        return prompt
    
    def _extract_sentiment(self, report: str) -> str:
        """Extract overall sentiment from report."""
        report_lower = report.lower()
        
        # Simple keyword-based sentiment detection
        positive_words = ['利好', '上涨', '乐观', '积极', '看多', '买入']
        negative_words = ['利空', '下跌', '悲观', '消极', '看空', '卖出']
        
        pos_count = sum(1 for word in positive_words if word in report)
        neg_count = sum(1 for word in negative_words if word in report)
        
        if pos_count > neg_count * 1.5:
            return 'positive'
        elif neg_count > pos_count * 1.5:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_signals(self, report: str) -> Dict[str, Any]:
        """Extract trading signals from report."""
        report_lower = report.lower()
        
        signals = {
            'recommendation': 'hold',  # buy/sell/hold
            'confidence': 'medium',     # high/medium/low
            'timeframe': 'short-term'   # short-term/medium-term/long-term
        }
        
        # Extract recommendation
        if '买入' in report or '看多' in report or '建议做多' in report:
            signals['recommendation'] = 'buy'
        elif '卖出' in report or '看空' in report or '建议做空' in report:
            signals['recommendation'] = 'sell'
        else:
            signals['recommendation'] = 'hold'
        
        # Extract confidence
        if '强烈' in report or '明确' in report or '确定' in report:
            signals['confidence'] = 'high'
        elif '谨慎' in report or '观察' in report or '不确定' in report:
            signals['confidence'] = 'low'
        
        return signals
