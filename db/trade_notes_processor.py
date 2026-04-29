"""
trade_notes_processor.py - Personal buy/sell ledger for CS2 items.
"""

import logging
import os
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

import pymysql
from dotenv import load_dotenv

from db.profit_processor import ProfitProcessor

logger = logging.getLogger(__name__)

load_dotenv()


MONEY = Decimal("0.01")
QTY = Decimal("0.0001")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _qty(value: Decimal) -> Decimal:
    return value.quantize(QTY, rounding=ROUND_HALF_UP)


def _to_decimal(value, default: str = "0") -> Decimal:
    if value is None or value == "":
        value = default
    return Decimal(str(value))


def _to_float(value):
    if value is None:
        return None
    return float(value)


_CREATE_TRADE_NOTES_TABLE = """
CREATE TABLE IF NOT EXISTS trade_note_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    market_hash_name VARCHAR(255) NOT NULL,
    item_name VARCHAR(255) DEFAULT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    platform VARCHAR(32) NOT NULL DEFAULT 'BUFF',
    trade_date DATE NOT NULL,
    quantity DECIMAL(18, 4) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    gross_amount DECIMAL(14, 2) NOT NULL,
    sell_fee_rate DECIMAL(8, 4) NOT NULL DEFAULT 0,
    sell_fee DECIMAL(14, 2) NOT NULL DEFAULT 0,
    withdraw_fee_rate DECIMAL(8, 4) NOT NULL DEFAULT 0,
    withdraw_fee DECIMAL(14, 2) NOT NULL DEFAULT 0,
    withdraw_min_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
    net_amount DECIMAL(14, 2) NOT NULL,
    note TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trade_note_user (email),
    INDEX idx_trade_note_item (email, market_hash_name),
    INDEX idx_trade_note_date (email, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='买卖笔记流水表'
"""


class TradeNotesProcessor:
    def __init__(self):
        self.config = {
            "host": os.getenv("HOST"),
            "port": int(os.getenv("PORT", 3306)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DATABASE"),
            "charset": os.getenv("CHARSET", "utf8mb4"),
        }
        self.profit_processor = ProfitProcessor()
        self._tables_ready = False

    def get_db_connection(self):
        return pymysql.connect(**self.config)

    def ensure_tables(self) -> bool:
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(_CREATE_TRADE_NOTES_TABLE)
            conn.commit()
            self._tables_ready = True
            return True
        except Exception as e:
            logger.error(f"创建买卖笔记表失败: {e}")
            if conn:
                conn.rollback()
            self._tables_ready = False
            return False
        finally:
            if conn:
                conn.close()

    def _ensure_tables_once(self) -> bool:
        if self._tables_ready:
            return True
        return self.ensure_tables()

    def add_entry(self, payload: Dict) -> Dict:
        side = str(payload.get("side", "")).upper()
        if side not in {"BUY", "SELL"}:
            return {"success": False, "message": "side 必须是 BUY 或 SELL"}

        email = str(payload.get("email") or "").strip()
        market_hash_name = str(payload.get("market_hash_name") or "").strip()
        if not email or not market_hash_name:
            return {"success": False, "message": "缺少 email 或 market_hash_name"}

        try:
            quantity = _qty(_to_decimal(payload.get("quantity")))
            unit_price = _money(_to_decimal(payload.get("unit_price")))
        except Exception:
            return {"success": False, "message": "数量或价格格式不正确"}

        if quantity <= 0 or unit_price <= 0:
            return {"success": False, "message": "数量和价格必须大于 0"}

        platform = self.profit_processor.normalize_platform(payload.get("platform") or "BUFF")
        trade_date = payload.get("trade_date") or date.today().isoformat()
        item_name = payload.get("item_name") or market_hash_name
        note = payload.get("note")

        if not self._ensure_tables_once():
            return {"success": False, "message": "买卖笔记表初始化失败，请检查数据库连接"}

        fees = None

        if side == "SELL":
            fees = self.profit_processor.get_platform_fees(platform)
            if not fees:
                return {"success": False, "message": f"未找到平台 {platform} 的费率配置"}
            try:
                current_remaining = self.get_remaining_quantity(email, market_hash_name)
            except Exception as e:
                logger.error(f"读取当前持仓失败: {e}")
                return {"success": False, "message": "读取当前持仓失败，请稍后重试"}
            if quantity > current_remaining:
                return {
                    "success": False,
                    "message": f"卖出数量不能超过当前持仓 {current_remaining}",
                }

        amounts = self.calculate_entry_amounts(side, quantity, unit_price, fees)
        gross_amount = amounts["gross_amount"]
        sell_fee_rate = amounts["sell_fee_rate"]
        sell_fee = amounts["sell_fee"]
        withdraw_fee_rate = amounts["withdraw_fee_rate"]
        withdraw_fee = amounts["withdraw_fee"]
        withdraw_min_fee = amounts["withdraw_min_fee"]
        net_amount = amounts["net_amount"]

        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_note_entries
                    (email, market_hash_name, item_name, side, platform, trade_date,
                     quantity, unit_price, gross_amount, sell_fee_rate, sell_fee,
                     withdraw_fee_rate, withdraw_fee, withdraw_min_fee, net_amount, note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        email,
                        market_hash_name,
                        item_name,
                        side,
                        platform,
                        trade_date,
                        quantity,
                        unit_price,
                        gross_amount,
                        sell_fee_rate,
                        sell_fee,
                        withdraw_fee_rate,
                        withdraw_fee,
                        withdraw_min_fee,
                        net_amount,
                        note,
                    ),
                )
                entry_id = cursor.lastrowid
            conn.commit()
            fallback_entry = self._serialize_entry(
                {
                    "id": entry_id,
                    "email": email,
                    "market_hash_name": market_hash_name,
                    "item_name": item_name,
                    "side": side,
                    "platform": platform,
                    "trade_date": trade_date,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "gross_amount": gross_amount,
                    "sell_fee_rate": sell_fee_rate,
                    "sell_fee": sell_fee,
                    "withdraw_fee_rate": withdraw_fee_rate,
                    "withdraw_fee": withdraw_fee,
                    "withdraw_min_fee": withdraw_min_fee,
                    "net_amount": net_amount,
                    "note": note,
                }
            )
            try:
                return {"success": True, "data": self.get_entry(email, entry_id) or fallback_entry}
            except Exception as e:
                logger.warning(f"新增买卖笔记成功，但读取新记录失败: {e}")
                return {"success": True, "data": fallback_entry}
        except Exception as e:
            logger.error(f"新增买卖笔记失败: {e}")
            if conn:
                conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            if conn:
                conn.close()

    def get_entry(self, email: str, entry_id: int) -> Optional[Dict]:
        if not self._ensure_tables_once():
            raise RuntimeError("买卖笔记表初始化失败")
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM trade_note_entries WHERE email = %s AND id = %s",
                    (email, entry_id),
                )
                row = cursor.fetchone()
                return self._serialize_entry(row) if row else None
        finally:
            if conn:
                conn.close()

    def list_entries(self, email: str, market_hash_name: str = None) -> List[Dict]:
        if not self._ensure_tables_once():
            raise RuntimeError("买卖笔记表初始化失败")
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if market_hash_name:
                    cursor.execute(
                        """
                        SELECT * FROM trade_note_entries
                        WHERE email = %s AND market_hash_name = %s
                        ORDER BY trade_date DESC, id DESC
                        """,
                        (email, market_hash_name),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM trade_note_entries
                        WHERE email = %s
                        ORDER BY trade_date DESC, id DESC
                        """,
                        (email,),
                    )
                return [self._serialize_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"读取买卖笔记失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def list_positions(self, email: str) -> List[Dict]:
        entries = self.list_entries(email)
        return self.summarize_entries(entries)

    def get_remaining_quantity(self, email: str, market_hash_name: str) -> Decimal:
        positions = self.summarize_entries(self.list_entries(email, market_hash_name))
        if not positions:
            return Decimal("0")
        return _to_decimal(positions[0].get("remaining_quantity"))

    def delete_entry(self, email: str, entry_id: int) -> bool:
        if not self._ensure_tables_once():
            raise RuntimeError("买卖笔记表初始化失败")
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM trade_note_entries WHERE email = %s AND id = %s",
                    (email, entry_id),
                )
                deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"删除买卖笔记失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def summarize_entries(cls, entries: List[Dict]) -> List[Dict]:
        grouped: Dict[str, Dict] = {}
        for entry in entries:
            key = entry["market_hash_name"]
            position = grouped.setdefault(
                key,
                {
                    "market_hash_name": key,
                    "item_name": entry.get("item_name") or key,
                    "buy_quantity": Decimal("0"),
                    "sell_quantity": Decimal("0"),
                    "remaining_quantity": Decimal("0"),
                    "buy_cost": Decimal("0"),
                    "sell_gross": Decimal("0"),
                    "sell_fee": Decimal("0"),
                    "withdraw_fee": Decimal("0"),
                    "sell_net": Decimal("0"),
                    "realized_profit": Decimal("0"),
                    "average_cost": Decimal("0"),
                    "remaining_cost": Decimal("0"),
                    "entry_count": 0,
                    "last_trade_date": None,
                },
            )

            side = entry["side"]
            quantity = _to_decimal(entry["quantity"])
            gross_amount = _to_decimal(entry["gross_amount"])
            if side == "BUY":
                position["buy_quantity"] += quantity
                position["buy_cost"] += gross_amount
            elif side == "SELL":
                position["sell_quantity"] += quantity
                position["sell_gross"] += gross_amount
                position["sell_fee"] += _to_decimal(entry["sell_fee"])
                position["withdraw_fee"] += _to_decimal(entry["withdraw_fee"])
                position["sell_net"] += _to_decimal(entry["net_amount"])

            position["entry_count"] += 1
            trade_date = entry.get("trade_date")
            if not position["last_trade_date"] or trade_date > position["last_trade_date"]:
                position["last_trade_date"] = trade_date

        positions = []
        for position in grouped.values():
            buy_quantity = position["buy_quantity"]
            sell_quantity = position["sell_quantity"]
            average_cost = (
                _money(position["buy_cost"] / buy_quantity)
                if buy_quantity > 0
                else Decimal("0")
            )
            remaining_quantity = buy_quantity - sell_quantity
            sold_cost_basis = _money(average_cost * sell_quantity) if sell_quantity > 0 else Decimal("0")
            realized_profit = _money(position["sell_net"] - sold_cost_basis)
            remaining_cost = _money(max(remaining_quantity, Decimal("0")) * average_cost)

            position.update(
                {
                    "average_cost": average_cost,
                    "remaining_quantity": _qty(remaining_quantity),
                    "remaining_cost": remaining_cost,
                    "realized_profit": realized_profit,
                    "realized_profit_rate": (
                        float((realized_profit / sold_cost_basis * 100).quantize(Decimal("0.0001")))
                        if sold_cost_basis > 0
                        else 0,
                    ),
                }
            )
            positions.append(cls._serialize_position(position))

        positions.sort(
            key=lambda item: (
                item["remaining_quantity"] > 0,
                item["last_trade_date"] or "",
            ),
            reverse=True,
        )
        return positions

    @staticmethod
    def calculate_entry_amounts(
        side: str,
        quantity: Decimal,
        unit_price: Decimal,
        fees: Optional[Dict] = None,
    ) -> Dict[str, Decimal]:
        side = str(side).upper()
        gross_amount = _money(quantity * unit_price)
        sell_fee_rate = Decimal("0")
        sell_fee = Decimal("0")
        withdraw_fee_rate = Decimal("0")
        withdraw_fee = Decimal("0")
        withdraw_min_fee = Decimal("0")
        net_amount = -gross_amount

        if side == "SELL":
            fees = fees or {}
            sell_fee_rate = _to_decimal(fees.get("sell_fee_rate"))
            withdraw_fee_rate = _to_decimal(fees.get("withdraw_fee_rate"))
            withdraw_min_fee = _money(_to_decimal(fees.get("withdraw_min_fee")))
            sell_fee = _money(gross_amount * sell_fee_rate)
            after_trade_fee = gross_amount - sell_fee
            withdraw_fee = max(_money(after_trade_fee * withdraw_fee_rate), withdraw_min_fee)
            net_amount = _money(after_trade_fee - withdraw_fee)

        return {
            "gross_amount": gross_amount,
            "sell_fee_rate": sell_fee_rate,
            "sell_fee": sell_fee,
            "withdraw_fee_rate": withdraw_fee_rate,
            "withdraw_fee": withdraw_fee,
            "withdraw_min_fee": withdraw_min_fee,
            "net_amount": net_amount,
        }

    @staticmethod
    def _serialize_entry(row: Dict) -> Dict:
        if not row:
            return row
        result = dict(row)
        for key in (
            "quantity",
            "unit_price",
            "gross_amount",
            "sell_fee_rate",
            "sell_fee",
            "withdraw_fee_rate",
            "withdraw_fee",
            "withdraw_min_fee",
            "net_amount",
        ):
            result[key] = _to_float(result.get(key))
        if result.get("trade_date") is not None:
            result["trade_date"] = str(result["trade_date"])
        if result.get("created_at") is not None:
            result["created_at"] = str(result["created_at"])
        if result.get("updated_at") is not None:
            result["updated_at"] = str(result["updated_at"])
        return result

    @staticmethod
    def _serialize_position(position: Dict) -> Dict:
        result = dict(position)
        for key in (
            "buy_quantity",
            "sell_quantity",
            "remaining_quantity",
            "buy_cost",
            "sell_gross",
            "sell_fee",
            "withdraw_fee",
            "sell_net",
            "realized_profit",
            "average_cost",
            "remaining_cost",
        ):
            result[key] = _to_float(result.get(key))
        return result
