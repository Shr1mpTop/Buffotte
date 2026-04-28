from app.integrations.bufftracker import BuffTrackerClient


def test_container_base_builds_api_path():
    client = BuffTrackerClient(base_url="http://buff-tracker-api-1:8001")

    assert (
        client.build_url("item/kline-data/AK-47%20%7C%20Redline")
        == "http://buff-tracker-api-1:8001/api/item/kline-data/AK-47%20%7C%20Redline"
    )


def test_proxy_base_does_not_duplicate_api_prefix():
    client = BuffTrackerClient(
        base_url="https://buffotte.hezhili.online/api/bufftracker"
    )

    assert (
        client.build_url("item/kline-data/AK-47%20%7C%20Redline")
        == "https://buffotte.hezhili.online/api/bufftracker/item/kline-data/AK-47%20%7C%20Redline"
    )


def test_build_url_accepts_existing_api_prefix_without_duplication():
    client = BuffTrackerClient(base_url="http://buff-tracker-api-1:8001/")

    assert (
        client.build_url("/api/item/kline-data/AK-47")
        == "http://buff-tracker-api-1:8001/api/item/kline-data/AK-47"
    )

