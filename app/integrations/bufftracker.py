from __future__ import annotations

from typing import Any, Iterable, Mapping
from urllib.parse import quote

import httpx

from app.core.config import settings


_HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
_PROXY_RESPONSE_HEADER_BLOCKLIST = _HOP_BY_HOP_HEADERS | {"content-encoding"}


class BuffTrackerClient:
    """HTTP adapter for the external buff-tracker service."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base_url = (base_url or settings.bufftracker_url).rstrip("/")
        self.timeout = timeout

    def build_url(self, path: str) -> str:
        normalized_path = self._normalize_path(path)
        if self.base_url.endswith("/api/bufftracker"):
            return self._join(self.base_url, normalized_path)
        return self._join(self.base_url, "api", normalized_path)

    async def proxy_request(
        self,
        method: str,
        path: str,
        query: str | bytes | None = None,
        headers: Mapping[str, str] | Iterable[tuple[str, str]] | None = None,
        body: bytes | None = None,
    ) -> httpx.Response:
        target_url = self._append_query(self.build_url(path), query)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.request(
                method=method,
                url=target_url,
                headers=self._forward_headers(headers),
                content=body,
            )

    async def get_item_kline_data(
        self,
        market_hash_name: str,
        platform: str = "BUFF",
        type_day: str = "1",
        date_type: int = 3,
    ) -> dict[str, Any]:
        encoded_name = quote(market_hash_name, safe="")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.build_url(f"item/kline-data/{encoded_name}"),
                params={"platform": platform, "type_day": type_day, "date_type": date_type},
            )
            return response.json()

    def get_item_kline_data_sync(
        self,
        market_hash_name: str,
        platform: str = "BUFF",
        type_day: str = "1",
        date_type: int = 3,
    ) -> dict[str, Any]:
        encoded_name = quote(market_hash_name, safe="")
        response = httpx.get(
            self.build_url(f"item/kline-data/{encoded_name}"),
            params={"platform": platform, "type_day": type_day, "date_type": date_type},
            timeout=self.timeout,
        )
        return response.json()

    async def search_items(self, name: str, num: int = 10) -> dict[str, Any]:
        return await self._get_json("search", params={"name": name, "num": num})

    async def get_price(self, market_hash_name: str) -> dict[str, Any]:
        encoded_name = quote(market_hash_name, safe="")
        return await self._get_json(f"price/{encoded_name}")

    async def get_quota(self) -> dict[str, Any]:
        return await self._get_json("quota")

    def get_base_items_sync(self) -> dict[str, Any]:
        response = httpx.get(self.build_url("base"), timeout=max(self.timeout, 60.0))
        response.raise_for_status()
        return response.json()

    async def _get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.build_url(path), params=params)
            return response.json()

    @staticmethod
    def _join(*parts: str) -> str:
        cleaned = [part.strip("/") for part in parts if part and part.strip("/")]
        if not cleaned:
            return ""
        first, *rest = cleaned
        if not rest:
            return first
        return "/".join([first, *rest])

    @staticmethod
    def _append_query(url: str, query: str | bytes | None) -> str:
        if not query:
            return url
        query_string = query.decode() if isinstance(query, bytes) else query
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{query_string}"

    @staticmethod
    def _forward_headers(
        headers: Mapping[str, str] | Iterable[tuple[str, str]] | None,
    ) -> dict[str, str]:
        if not headers:
            return {}
        items = headers.items() if hasattr(headers, "items") else headers
        return {
            key: value
            for key, value in items
            if key.lower() not in _HOP_BY_HOP_HEADERS
        }

    @staticmethod
    def response_headers(
        headers: Mapping[str, str] | Iterable[tuple[str, str]],
    ) -> dict[str, str]:
        items = headers.items() if hasattr(headers, "items") else headers
        return {
            key: value
            for key, value in items
            if key.lower() not in _PROXY_RESPONSE_HEADER_BLOCKLIST
        }

    @staticmethod
    def _normalize_path(path: str) -> str:
        normalized = (path or "").lstrip("/")
        if normalized == "api/bufftracker":
            return ""
        if normalized.startswith("api/bufftracker/"):
            return normalized.removeprefix("api/bufftracker/")
        if normalized == "api":
            return ""
        if normalized.startswith("api/"):
            return normalized.removeprefix("api/")
        return normalized
