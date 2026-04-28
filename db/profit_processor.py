"""
profit_processor.py — 搬砖收益计算核心模块

管理平台费率配置，计算跨平台/同平台搬砖净利润。
"""

import logging
import os
import math
from typing import Dict, List, Optional
from datetime import datetime

import pymysql
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# ── 平台费率默认值（来自 docs/price.md，2026-04-28） ────────────────────────
DEFAULT_PLATFORM_FEES = {
    "BUFF": {
        "sell_fee_rate": 0.015,
        "withdraw_fee_rate": 0.01,
        "withdraw_min_fee": 2.0,
        "withdraw_max_single": 50000.0,
    },
    "IGXE": {
        "sell_fee_rate": 0.006,
        "withdraw_fee_rate": 0.008,
        "withdraw_min_fee": 2.0,
        "withdraw_max_single": 10000.0,
    },
    "C5": {
        "sell_fee_rate": 0.01,
        "withdraw_fee_rate": 0.01,
        "withdraw_min_fee": 2.0,
        "withdraw_max_single": 50000.0,
    },
    "YOUPIN": {
        "sell_fee_rate": 0.0,
        "withdraw_fee_rate": 0.01,
        "withdraw_min_fee": 2.0,
        "withdraw_max_single": 20000.0,
    },
    "CSFLOAT": {
        "sell_fee_rate": 0.02,
        "withdraw_fee_rate": 0.025,
        "withdraw_min_fee": 0.0,
        "withdraw_max_single": None,
    },
}


def _get_db_connection():
    return pymysql.connect(
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DATABASE"),
        charset=os.getenv("CHARSET", "utf8mb4"),
    )


_CREATE_PLATFORM_FEES_TABLE = """
CREATE TABLE IF NOT EXISTS platform_fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(32) NOT NULL UNIQUE COMMENT '平台标识：BUFF/IGXE/C5/YOUPIN/CSFLOAT',
    display_name VARCHAR(64) DEFAULT NULL COMMENT '显示名称',
    sell_fee_rate DECIMAL(5, 4) NOT NULL DEFAULT 0 COMMENT '卖家交易手续费率',
    withdraw_fee_rate DECIMAL(5, 4) NOT NULL DEFAULT 0 COMMENT '提现费率',
    withdraw_min_fee DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '最低提现手续费（元）',
    withdraw_max_single DECIMAL(12, 2) DEFAULT NULL COMMENT '单笔提现上限（元）',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='平台费率配置表'
"""

_CREATE_PROFIT_CALCULATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS profit_calculations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_hash_name VARCHAR(255) NOT NULL COMMENT '饰品标识',
    buy_platform VARCHAR(32) NOT NULL COMMENT '买入平台',
    sell_platform VARCHAR(32) NOT NULL COMMENT '卖出平台',
    buy_price DECIMAL(12, 2) NOT NULL COMMENT '买入价格',
    sell_price DECIMAL(12, 2) NOT NULL COMMENT '预期/实际卖出价格',
    sell_fee DECIMAL(10, 2) COMMENT '卖出手续费',
    withdraw_fee DECIMAL(10, 2) COMMENT '提现手续费',
    net_profit DECIMAL(12, 2) COMMENT '净利润',
    profit_rate DECIMAL(8, 4) COMMENT '利润率',
    annualized_return DECIMAL(8, 4) COMMENT '年化收益率',
    hold_days INT DEFAULT 7 COMMENT '持有天数',
    price_source VARCHAR(16) DEFAULT 'predicted' COMMENT '价格来源：predicted/actual',
    user_id VARCHAR(255) DEFAULT NULL COMMENT '关联用户',
    note TEXT DEFAULT NULL COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_market_hash_name (market_hash_name),
    INDEX idx_profit_rate (profit_rate),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='搬砖收益计算记录'
"""


class ProfitProcessor:
    def __init__(self):
        self.config = {
            "host": os.getenv("HOST"),
            "port": int(os.getenv("PORT", 3306)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DATABASE"),
            "charset": os.getenv("CHARSET", "utf8mb4"),
        }

    def get_db_connection(self):
        return pymysql.connect(**self.config)

    # ── 表创建 ────────────────────────────────────────────────────────────

    def ensure_tables(self):
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(_CREATE_PLATFORM_FEES_TABLE)
                cursor.execute(_CREATE_PROFIT_CALCULATIONS_TABLE)
            conn.commit()
            self._seed_platform_fees(conn)
            logger.info("profit 相关表已确保存在")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def _seed_platform_fees(self, conn):
        """如果 platform_fees 表为空，插入默认费率数据。"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM platform_fees")
                count = cursor.fetchone()[0]
                if count > 0:
                    return
                display_names = {
                    "BUFF": "网易 BUFF",
                    "IGXE": "IGXE",
                    "C5": "C5GAME",
                    "YOUPIN": "悠悠有品",
                    "CSFLOAT": "CSFloat（海外）",
                }
                for platform, fees in DEFAULT_PLATFORM_FEES.items():
                    cursor.execute(
                        "INSERT INTO platform_fees "
                        "(platform_name, display_name, sell_fee_rate, withdraw_fee_rate, "
                        "withdraw_min_fee, withdraw_max_single) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            platform,
                            display_names.get(platform, platform),
                            fees["sell_fee_rate"],
                            fees["withdraw_fee_rate"],
                            fees["withdraw_min_fee"],
                            fees["withdraw_max_single"],
                        ),
                    )
                conn.commit()
                logger.info(f"已初始化 {len(DEFAULT_PLATFORM_FEES)} 个平台的默认费率")
        except Exception as e:
            logger.error(f"初始化平台费率失败: {e}")
            conn.rollback()

    # ── 平台费率查询 ──────────────────────────────────────────────────────

    def get_all_platform_fees(self) -> List[Dict]:
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT platform_name, display_name, sell_fee_rate, "
                    "withdraw_fee_rate, withdraw_min_fee, withdraw_max_single "
                    "FROM platform_fees ORDER BY id"
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询平台费率失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_platform_fees(self, platform: str) -> Optional[Dict]:
        """获取单个平台的费率配置。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT platform_name, sell_fee_rate, withdraw_fee_rate, "
                    "withdraw_min_fee, withdraw_max_single "
                    "FROM platform_fees WHERE platform_name = %s",
                    (platform,),
                )
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"查询平台 {platform} 费率失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ── 利润计算核心 ──────────────────────────────────────────────────────

    @staticmethod
    def calc_profit(
        buy_price: float,
        sell_price: float,
        sell_fee_rate: float,
        withdraw_fee_rate: float,
        withdraw_min_fee: float,
        hold_days: int = 7,
    ) -> Dict:
        """
        计算搬砖净利润。

        公式：
          卖出手续费 = 卖出价格 × 卖出费率
          实际到账 = 卖出价格 - 卖出手续费
          提现手续费 = max(实际到账 × 提现费率, 最低提现费)
          净利润 = 实际到账 - 提现手续费 - 买入价格
          利润率 = 净利润 / 买入价格
          年化收益率 = 利润率 × (365 / 持有天数)
        """
        sell_fee = sell_price * sell_fee_rate
        actual_receive = sell_price - sell_fee
        withdraw_fee = max(actual_receive * withdraw_fee_rate, withdraw_min_fee)
        net_profit = actual_receive - withdraw_fee - buy_price
        profit_rate = net_profit / buy_price if buy_price > 0 else 0
        annualized = profit_rate * (365 / hold_days) if hold_days > 0 else 0

        return {
            "buy_price": round(buy_price, 2),
            "sell_price": round(sell_price, 2),
            "sell_fee": round(sell_fee, 2),
            "actual_receive": round(actual_receive, 2),
            "withdraw_fee": round(withdraw_fee, 2),
            "net_profit": round(net_profit, 2),
            "profit_rate": round(profit_rate * 100, 4),
            "annualized_return": round(annualized * 100, 4),
            "hold_days": hold_days,
        }

    def calc_profit_for_platform(
        self,
        buy_price: float,
        sell_price: float,
        sell_platform: str,
        hold_days: int = 7,
    ) -> Optional[Dict]:
        """根据卖出平台的费率计算利润。"""
        fees = self.get_platform_fees(sell_platform)
        if not fees:
            logger.error(f"未找到平台 {sell_platform} 的费率配置")
            return None
        return self.calc_profit(
            buy_price=buy_price,
            sell_price=sell_price,
            sell_fee_rate=float(fees["sell_fee_rate"]),
            withdraw_fee_rate=float(fees["withdraw_fee_rate"]),
            withdraw_min_fee=float(fees["withdraw_min_fee"]),
            hold_days=hold_days,
        )

    def calc_all_platforms_profit(
        self,
        buy_price: float,
        sell_price: float,
        hold_days: int = 7,
    ) -> Dict[str, Dict]:
        """计算在所有平台卖出的利润对比。"""
        all_fees = self.get_all_platform_fees()
        results = {}
        for platform_fee in all_fees:
            pname = platform_fee["platform_name"]
            result = self.calc_profit(
                buy_price=buy_price,
                sell_price=sell_price,
                sell_fee_rate=float(platform_fee["sell_fee_rate"]),
                withdraw_fee_rate=float(platform_fee["withdraw_fee_rate"]),
                withdraw_min_fee=float(platform_fee["withdraw_min_fee"]),
                hold_days=hold_days,
            )
            result["platform"] = pname
            result["display_name"] = platform_fee.get("display_name", pname)
            results[pname] = result
        return results

    # ── 计算记录存储 ──────────────────────────────────────────────────────

    def save_calculation(
        self,
        market_hash_name: str,
        buy_platform: str,
        sell_platform: str,
        buy_price: float,
        sell_price: float,
        net_profit: float,
        profit_rate: float,
        annualized_return: float,
        sell_fee: float = None,
        withdraw_fee: float = None,
        hold_days: int = 7,
        price_source: str = "predicted",
        user_id: str = None,
    ) -> Optional[int]:
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO profit_calculations "
                    "(market_hash_name, buy_platform, sell_platform, buy_price, sell_price, "
                    "sell_fee, withdraw_fee, net_profit, profit_rate, annualized_return, "
                    "hold_days, price_source, user_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        market_hash_name,
                        buy_platform,
                        sell_platform,
                        buy_price,
                        sell_price,
                        sell_fee,
                        withdraw_fee,
                        net_profit,
                        profit_rate,
                        annualized_return,
                        hold_days,
                        price_source,
                        user_id,
                    ),
                )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"保存计算记录失败: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    # ── 追踪饰品利润预测 ──────────────────────────────────────────────────

    def get_tracked_items_with_profit(
        self, email: str, predicted_prices: Dict[str, float] = None
    ) -> List[Dict]:
        """
        获取用户追踪的所有饰品，附加各平台预测利润。
        predicted_prices: {market_hash_name: predicted_7d_price} 外部传入的预测价格
        """
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT t.market_hash_name, "
                    "COALESCE(c.name, t.market_hash_name) as name, "
                    "ik.price as current_price "
                    "FROM track t "
                    "LEFT JOIN cs2_items c "
                    "  ON t.market_hash_name COLLATE utf8mb4_unicode_ci = c.market_hash_name "
                    "LEFT JOIN ("
                    "  SELECT market_hash_name, price "
                    "  FROM item_kline_day ik2 "
                    "  WHERE (market_hash_name, timestamp) IN ("
                    "    SELECT market_hash_name, MAX(timestamp) "
                    "    FROM item_kline_day GROUP BY market_hash_name"
                    "  )"
                    ") ik ON t.market_hash_name COLLATE utf8mb4_unicode_ci = ik.market_hash_name "
                    "WHERE t.email = %s",
                    (email,),
                )
                items = cursor.fetchall()

            all_fees = self.get_all_platform_fees()
            for item in items:
                current_price = float(item["current_price"]) if item["current_price"] else None
                item["current_price"] = current_price
                pred_price = (
                    predicted_prices.get(item["market_hash_name"])
                    if predicted_prices
                    else None
                )
                item["predicted_price_7d"] = pred_price
                item["profit_by_platform"] = {}

                if current_price and pred_price and pred_price > 0:
                    for pf in all_fees:
                        result = self.calc_profit(
                            buy_price=current_price,
                            sell_price=pred_price,
                            sell_fee_rate=float(pf["sell_fee_rate"]),
                            withdraw_fee_rate=float(pf["withdraw_fee_rate"]),
                            withdraw_min_fee=float(pf["withdraw_min_fee"]),
                        )
                        result["platform"] = pf["platform_name"]
                        result["display_name"] = pf.get("display_name", pf["platform_name"])
                        item["profit_by_platform"][pf["platform_name"]] = result

            return items
        except Exception as e:
            logger.error(f"获取追踪饰品利润失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
