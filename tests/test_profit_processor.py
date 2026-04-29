from db.profit_processor import DEFAULT_PLATFORM_FEES, ProfitProcessor
from api import _current_price_nodes, _estimate_future_bidding_node


def test_calc_profit_paths_uses_distinct_buy_and_sell_nodes():
    processor = ProfitProcessor()
    processor.get_all_platform_fees = lambda: [
        {
            "platform_name": "BUFF",
            "display_name": "网易 BUFF",
            "sell_fee_rate": 0.015,
            "withdraw_fee_rate": 0.01,
            "withdraw_min_fee": 2.0,
            "withdraw_max_single": 50000.0,
        }
    ]

    buy_nodes = [
        {"id": "current_lowest_bidding", "label": "最低求购", "price": 90, "platform": "BUFF"},
        {"id": "current_lowest_sell", "label": "最低卖价", "price": 100, "platform": "BUFF"},
    ]
    sell_nodes = [
        {"id": "future_predicted_bidding", "label": "预测求购", "price": 105, "platform": "BUFF"},
        {"id": "future_predicted_sell", "label": "预测卖价", "price": 110, "platform": "BUFF"},
    ]

    paths = processor.calc_profit_paths(buy_nodes, sell_nodes, hold_days=7)

    assert len(paths) == 4
    assert {path["id"] for path in paths} == {
        "current_lowest_bidding_to_future_predicted_bidding",
        "current_lowest_bidding_to_future_predicted_sell",
        "current_lowest_sell_to_future_predicted_bidding",
        "current_lowest_sell_to_future_predicted_sell",
    }
    assert paths[0]["id"] == "current_lowest_bidding_to_future_predicted_sell"
    assert paths[0]["name"] == "最低求购 -> 预测卖价"
    assert paths[0]["buy_price"] == 90
    assert paths[0]["sell_price"] == 110
    assert paths[0]["platform_route"] == "BUFF -> BUFF"
    assert paths[0]["sell_fee_rate"] == 1.5
    assert paths[0]["withdraw_fee_rate"] == 1.0


def test_calc_profit_paths_effectivizes_zero_seeded_platform_fee():
    processor = ProfitProcessor()
    processor.get_all_platform_fees = lambda: [
        {
            "platform_name": "YOUPIN",
            "display_name": "悠悠有品",
            "sell_fee_rate": 0.0,
            "withdraw_fee_rate": 0.01,
            "withdraw_min_fee": 2.0,
            "withdraw_max_single": 20000.0,
        }
    ]

    paths = processor.calc_profit_paths(
        buy_nodes=[{"id": "buy", "label": "最低卖价", "price": 100, "platform": "BUFF"}],
        sell_nodes=[{"id": "sell", "label": "最高卖价", "price": 120, "platform": "悠悠有品"}],
    )

    assert paths[0]["sell_platform"] == "YOUPIN"
    assert paths[0]["platform_route"] == "BUFF -> 悠悠有品"
    assert paths[0]["sell_fee_rate"] == 1.0
    assert paths[0]["sell_fee"] == 1.2


def test_estimated_future_bidding_keeps_current_bid_platform():
    node = _estimate_future_bidding_node(
        200,
        {"price": 100, "platform": "BUFF"},
        {"price": 90, "platform": "悠悠有品"},
    )

    assert node["platform"] == "悠悠有品"
    assert node["platform_key"] == "YOUPIN"


def test_current_price_nodes_do_not_fallback_from_explicit_zero_prices():
    nodes = _current_price_nodes(
        [
            {
                "platform": "BUFF",
                "sellPrice": 0,
                "price": 999,
                "biddingPrice": 0,
                "buyPrice": 888,
            },
            {"platform": "IGXE", "sellPrice": 100, "biddingPrice": 90},
            {"platform": "C5", "sellPrice": 110, "biddingPrice": 95},
        ]
    )

    lowest_bid, lowest_sell, highest_bid, highest_sell = nodes

    assert lowest_sell["platform"] == "IGXE"
    assert lowest_sell["price"] == 100
    assert highest_sell["platform"] == "C5"
    assert highest_sell["price"] == 110
    assert lowest_bid["platform"] == "IGXE"
    assert highest_bid["platform"] == "C5"


def test_platform_fee_rows_merge_missing_defaults_and_repair_zero_seeded_values():
    rows = ProfitProcessor._merge_fee_rows_with_defaults(
        [
            {
                "platform_name": "YOUPIN",
                "display_name": "悠悠有品",
                "sell_fee_rate": 0,
                "withdraw_fee_rate": 0,
                "withdraw_min_fee": 0,
                "withdraw_max_single": 20000,
            }
        ]
    )

    by_platform = {row["platform_name"]: row for row in rows}

    assert set(DEFAULT_PLATFORM_FEES).issubset(by_platform)
    assert by_platform["YOUPIN"]["sell_fee_rate"] == DEFAULT_PLATFORM_FEES["YOUPIN"]["sell_fee_rate"]
    assert by_platform["YOUPIN"]["withdraw_fee_rate"] == DEFAULT_PLATFORM_FEES["YOUPIN"]["withdraw_fee_rate"]
    assert by_platform["YOUPIN"]["withdraw_min_fee"] == DEFAULT_PLATFORM_FEES["YOUPIN"]["withdraw_min_fee"]
