import asyncio

from api import app
from app.routers.system import get_system_stats


def test_api_app_imports_without_startup_database_connection():
    assert app.title == "FastAPI"


def test_core_route_paths_are_registered():
    paths = {route.path for route in app.routes}
    expected = {
        "/api/register",
        "/api/login",
        "/api/user/profile",
        "/api/user/details/{email}",
        "/api/kline/chart-data",
        "/api/bufftracker/{path:path}",
        "/api/item/kline-data/{market_hash_name}",
        "/api/item/kline-refresh/{market_hash_name}",
        "/api/track/add",
        "/api/trade-notes/{email}/positions",
        "/api/trade-notes/{email}/entries",
        "/api/trade-notes",
        "/api/trade-notes/{email}/entries/{entry_id}",
        "/api/system/stats",
        "/api/profit/calculate",
    }
    assert expected.issubset(paths)


def test_system_stats_returns_success_payload_without_database():
    result = asyncio.run(get_system_stats())
    assert result["success"] is True
    assert "cpu_percent" in result["data"]
