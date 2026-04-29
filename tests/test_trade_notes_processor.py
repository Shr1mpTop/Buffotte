from decimal import Decimal

from db.trade_notes_processor import TradeNotesProcessor


def test_sell_amounts_deduct_trade_fee_before_withdraw_fee():
    amounts = TradeNotesProcessor.calculate_entry_amounts(
        side="SELL",
        quantity=Decimal("1"),
        unit_price=Decimal("200"),
        fees={
            "sell_fee_rate": 0.015,
            "withdraw_fee_rate": 0.01,
            "withdraw_min_fee": 2.0,
        },
    )

    assert amounts["gross_amount"] == Decimal("200.00")
    assert amounts["sell_fee"] == Decimal("3.00")
    assert amounts["withdraw_fee"] == Decimal("2.00")
    assert amounts["net_amount"] == Decimal("195.00")


def test_trade_note_summary_uses_average_cost_and_net_sell_amount():
    positions = TradeNotesProcessor.summarize_entries(
        [
            {
                "market_hash_name": "AK-47 | Redline",
                "item_name": "AK-47 | Redline",
                "side": "BUY",
                "trade_date": "2026-04-20",
                "quantity": 2,
                "gross_amount": 200,
            },
            {
                "market_hash_name": "AK-47 | Redline",
                "item_name": "AK-47 | Redline",
                "side": "SELL",
                "trade_date": "2026-04-21",
                "quantity": 1,
                "gross_amount": 130,
                "sell_fee": 1.95,
                "withdraw_fee": 2,
                "net_amount": 126.05,
            },
        ]
    )

    assert len(positions) == 1
    position = positions[0]
    assert position["buy_quantity"] == 2.0
    assert position["sell_quantity"] == 1.0
    assert position["remaining_quantity"] == 1.0
    assert position["buy_cost"] == 200.0
    assert position["average_cost"] == 100.0
    assert position["sell_net"] == 126.05
    assert position["remaining_cost"] == 100.0
    assert position["realized_profit"] == 26.05


def test_trade_note_summary_keeps_closed_position_history():
    positions = TradeNotesProcessor.summarize_entries(
        [
            {
                "market_hash_name": "AK-47 | Redline",
                "item_name": "AK-47 | Redline",
                "side": "BUY",
                "trade_date": "2026-04-20",
                "quantity": 1,
                "gross_amount": 100,
            },
            {
                "market_hash_name": "AK-47 | Redline",
                "item_name": "AK-47 | Redline",
                "side": "SELL",
                "trade_date": "2026-04-21",
                "quantity": 1,
                "gross_amount": 120,
                "sell_fee": 1.8,
                "withdraw_fee": 2,
                "net_amount": 116.2,
            },
        ]
    )

    assert len(positions) == 1
    assert positions[0]["remaining_quantity"] == 0.0
    assert positions[0]["sell_quantity"] == 1.0
    assert positions[0]["realized_profit"] == 16.2
