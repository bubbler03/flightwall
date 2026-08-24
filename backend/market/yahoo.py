"""Kursdaten von Yahoo Finance - ohne API-Key.

Zwei Endpunkte reichen:
  * screener  -> Tagesgewinner/-verlierer/meistgehandelt (fertig sortiert)
  * chart     -> Einzelkurs samt Intraday-Verlauf fuer die Mini-Charts
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..http import Http

log = logging.getLogger(__name__)

SCREENER_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"Accept": "application/json"}

SCREENS = {
    "gainers": "day_gainers",
    "losers": "day_losers",
    "actives": "most_actives",
}


class YahooClient:
    def __init__(self, timeout: float = 15.0) -> None:
        # Yahoo mag keine Anfrageschwaerme: hoechstens zwei gleichzeitig,
        # dazwischen eine kurze Pause.
        self._http = Http(timeout=timeout, max_parallel=2, min_interval=0.4, headers=HEADERS)

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        return await self._http.json(url, params)

    async def screen(self, screen: str, count: int = 50) -> list[dict[str, Any]]:
        """Vorgefertigte Liste abrufen ('gainers', 'losers', 'actives')."""
        scr_id = SCREENS.get(screen, screen)
        data = await self._get(SCREENER_URL, {"scrIds": scr_id, "count": count})
        try:
            quotes = data["finance"]["result"][0]["quotes"]
        except (TypeError, KeyError, IndexError):
            return []
        return [_quote(q, source=screen) for q in quotes]

    async def quote(self, symbol: str, *, with_history: bool = False) -> dict[str, Any] | None:
        """Einzelkurs; optional mit Intraday-Verlauf fuer den Chart."""
        params = {"range": "1d", "interval": "5m"} if with_history else {"range": "1d", "interval": "1d"}
        data = await self._get(CHART_URL.format(symbol=symbol), params)
        try:
            result = data["chart"]["result"][0]
        except (TypeError, KeyError, IndexError):
            return None

        meta = result.get("meta") or {}
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        change_pct = ((price - prev) / prev * 100) if price and prev else None

        out = {
            "symbol": meta.get("symbol", symbol),
            "name": meta.get("longName") or meta.get("shortName") or symbol,
            "price": price,
            "previous_close": prev,
            "change": round(price - prev, 4) if price and prev else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "currency": meta.get("currency"),
            "exchange": meta.get("fullExchangeName"),
            "market_state": meta.get("marketState"),
            "volume": meta.get("regularMarketVolume"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "source": "watchlist",
        }
        if with_history:
            out["spark"] = _spark(result)
        return out

    async def quotes(self, symbols: list[str], *, with_history: bool = False) -> list[dict[str, Any]]:
        results = await asyncio.gather(
            *(self.quote(s, with_history=with_history) for s in symbols), return_exceptions=True
        )
        return [r for r in results if isinstance(r, dict)]

    async def spark(self, symbol: str) -> list[float]:
        data = await self._get(CHART_URL.format(symbol=symbol), {"range": "1d", "interval": "5m"})
        try:
            return _spark(data["chart"]["result"][0])
        except (TypeError, KeyError, IndexError):
            return []

    async def aclose(self) -> None:
        await self._http.aclose()


def _quote(q: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "symbol": q.get("symbol"),
        "name": q.get("longName") or q.get("shortName") or q.get("symbol"),
        "price": q.get("regularMarketPrice"),
        "change": q.get("regularMarketChange"),
        "change_pct": round(q.get("regularMarketChangePercent") or 0, 2),
        "volume": q.get("regularMarketVolume"),
        "avg_volume": q.get("averageDailyVolume3Month"),
        "market_cap": q.get("marketCap"),
        "currency": q.get("currency"),
        "exchange": q.get("fullExchangeName"),
        "market_state": q.get("marketState"),
        "previous_close": q.get("regularMarketPreviousClose"),
        "fifty_two_week_high": q.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": q.get("fiftyTwoWeekLow"),
        "post_change_pct": round(q.get("postMarketChangePercent"), 2) if q.get("postMarketChangePercent") else None,
        "pre_change_pct": round(q.get("preMarketChangePercent"), 2) if q.get("preMarketChangePercent") else None,
        "source": source,
    }


def _spark(result: dict[str, Any], points: int = 60) -> list[float]:
    """Intraday-Kurve auf wenige Punkte eindampfen."""
    try:
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return []
    clean = [c for c in closes if isinstance(c, (int, float))]
    if len(clean) <= points:
        return [round(c, 4) for c in clean]
    step = len(clean) / points
    return [round(clean[int(i * step)], 4) for i in range(points)]
