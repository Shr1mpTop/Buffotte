from functools import lru_cache

from app.integrations.bufftracker import BuffTrackerClient
from crawler.item_price import DailyKlineCrawler
from db.item_kline_processor import ItemKlineProcessor
from db.kline_data_processor import KlineDataProcessor
from db.profit_processor import ProfitProcessor
from db.trade_notes_processor import TradeNotesProcessor
from db.user_actions import UserActions
from db.user_manager import UserManager


@lru_cache
def get_user_manager() -> UserManager:
    return UserManager()


@lru_cache
def get_user_actions() -> UserActions:
    return UserActions()


@lru_cache
def get_kline_processor() -> KlineDataProcessor:
    return KlineDataProcessor()


@lru_cache
def get_item_kline_processor() -> ItemKlineProcessor:
    return ItemKlineProcessor()


@lru_cache
def get_item_crawler() -> DailyKlineCrawler:
    return DailyKlineCrawler()


@lru_cache
def get_profit_processor() -> ProfitProcessor:
    return ProfitProcessor()


@lru_cache
def get_trade_notes_processor() -> TradeNotesProcessor:
    return TradeNotesProcessor()


@lru_cache
def get_bufftracker_client() -> BuffTrackerClient:
    return BuffTrackerClient()
