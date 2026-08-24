"""Schlagzeilen zu einem Symbol - ueber oeffentliche RSS-Feeds.

X/Twitter braucht seit 2023 ein kostenpflichtiges API-Abo und StockTwits
blockt anonyme Zugriffe. Google News deckt beides praktisch ab: Meldungen von
Reuters, Bloomberg, CNBC & Co. tauchen dort innerhalb von Minuten auf.
Ein X-Client kann spaeter in fetch() ergaenzt werden.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from urllib.parse import quote_plus

import feedparser

from ..http import Http
from ..store import cache_get, cache_set

log = logging.getLogger(__name__)

GOOGLE_NEWS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
YAHOO_NEWS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
NEWS_TTL = 300  # 5 Minuten


class NewsClient:
    def __init__(self, timeout: float = 12.0) -> None:
        self._http = Http(timeout=timeout, max_parallel=2, min_interval=0.3)

    async def _feed(self, url: str) -> list[dict[str, Any]]:
        raw = await self._http.bytes(url)
        if not raw:
            return []
        parsed = await asyncio.to_thread(feedparser.parse, raw)
        out = []
        for entry in parsed.entries:
            published = None
            if getattr(entry, "published_parsed", None):
                published = time.mktime(entry.published_parsed)
            out.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link"),
                "source": (entry.get("source") or {}).get("title") if isinstance(entry.get("source"), dict) else entry.get("source"),
                "published": published,
            })
        return out

    async def headlines(self, symbol: str, name: str = "", limit: int = 6) -> list[dict[str, Any]]:
        """Aktuelle Schlagzeilen zu einem Ticker, nach Aktualitaet sortiert."""
        key = f"news:{symbol}"
        cached = cache_get(key)
        if cached is not None:
            return cached[:limit]

        query = f'"{name}" OR {symbol} stock' if name else f"{symbol} stock"
        feeds = await asyncio.gather(
            self._feed(GOOGLE_NEWS.format(query=quote_plus(query))),
            self._feed(YAHOO_NEWS.format(symbol=symbol)),
            return_exceptions=True,
        )

        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        for feed in feeds:
            if isinstance(feed, Exception):
                continue
            for item in feed:
                title = item["title"]
                if not title or title.lower() in seen:
                    continue
                seen.add(title.lower())
                items.append(item)

        items.sort(key=lambda i: i.get("published") or 0, reverse=True)
        items = items[:12]
        cache_set(key, items, NEWS_TTL)
        return items[:limit]

    async def aclose(self) -> None:
        await self._http.aclose()
