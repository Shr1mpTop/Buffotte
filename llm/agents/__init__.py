"""Agent implementations for the multi-agent analysis system."""

from llm.agents.base_agent import BaseAgent
from llm.agents.quant_researcher import QuantResearcherAgent
from llm.agents.fundamental_analyst import FundamentalAnalystAgent
from llm.agents.sentiment_analyst import SentimentAnalystAgent
from llm.agents.strategy_manager import StrategyManagerAgent
from llm.agents.risk_control import RiskControlAgent

# Legacy agents (for backward compatibility)
from llm.agents.data_analyst import DataAnalystAgent
from llm.agents.market_analyst import MarketAnalystAgent
from llm.agents.fund_manager import FundManagerAgent
from llm.agents.summarizer import SummarizerAgent

__all__ = [
    'BaseAgent',
    # New optimized agents
    'QuantResearcherAgent',
    'FundamentalAnalystAgent',
    'SentimentAnalystAgent',
    'StrategyManagerAgent',
    'RiskControlAgent',
    # Legacy agents
    'DataAnalystAgent',
    'MarketAnalystAgent',
    'FundManagerAgent',
    'SummarizerAgent',
]
