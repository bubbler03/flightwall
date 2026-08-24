"""Beobachtet den Markt und meldet auffaellige Bewegungen ans Display."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ..config import Config
from ..hub import Hub
from ..store import alert_sent_recently, record_alert
from .agent import MarketAgent
from .news import NewsClient
from .yahoo import YahooClient

log = logging.getLogger(__name__)

ALERT_COOLDOWN = 60 * 60 * 3   # dasselbe Symbol hoechstens alle 3 Stunden melden
TOP_MOVERS = 8                 # so viele Zeilen zeigt die Aktien-Ansicht
SPARK_COUNT = 6                # fuer so viele davon wird ein Mini-Chart geladen


class MarketService:
    def __init__(self, config: Config, hub: Hub) -> None:
        self.cfg = config
        self.hub = hub
        self.yahoo = YahooClient()
        self.news = NewsClient()
        self.agent = MarketAgent(config.agent)
        self.last_update: float = 0.0
        self.last_error: str | None = None
        self._task: asyncio.Task | None = None

    # -- Lebenszyklus --------------------------------------------------
    def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="market-service")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await asyncio.gather(self.yahoo.aclose(), self.news.aclose(), return_exceptions=True)

    async def _loop(self) -> None:
        while True:
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = str(exc)
                log.exception("Fehler im Markt-Loop: %s", exc)
            await asyncio.sleep(self.cfg.market.poll_seconds)

    # -- Ein Durchlauf -------------------------------------------------
    async def tick(self) -> dict[str, Any]:
        m = self.cfg.market
        gainers, losers, watch = await asyncio.gather(
            self.yahoo.screen("gainers", count=50),
            self.yahoo.screen("losers", count=50),
            self.yahoo.quotes(m.watchlist) if m.watchlist else _empty_list(),
        )

        movers = self._filter_movers(gainers + losers)
        watch_movers = [w for w in watch if abs(w.get("change_pct") or 0) >= m.move_threshold_pct]

        merged: dict[str, dict[str, Any]] = {}
        for q in movers + watch_movers:
            symbol = q.get("symbol")
            if not symbol:
                continue
            # Screener-Datensaetze sind reichhaltiger, deshalb nicht ueberschreiben
            if symbol not in merged or q.get("market_cap"):
                merged[symbol] = {**merged.get(symbol, {}), **q}

        ranked = sorted(merged.values(), key=lambda q: abs(q.get("change_pct") or 0), reverse=True)
        top = ranked[:TOP_MOVERS]
        await self._add_sparklines(top[:SPARK_COUNT])

        payload = {
            "movers": top,
            "watchlist": sorted(watch, key=lambda q: abs(q.get("change_pct") or 0), reverse=True),
            "market_state": (gainers[0].get("market_state") if gainers else None),
            "updated_at": time.time(),
            "agent_active": self.agent.active,
        }
        self.last_update = time.time()
        self.last_error = None
        self.hub.set_market(payload)

        await self._check_alerts(ranked)
        return payload

    def _filter_movers(self, quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Nur groessere Firmen mit echtem Handelsvolumen."""
        m = self.cfg.market
        out = []
        for q in quotes:
            if (q.get("market_cap") or 0) < m.min_market_cap:
                continue
            if (q.get("volume") or 0) < m.min_volume:
                continue
            if abs(q.get("change_pct") or 0) < m.move_threshold_pct:
                continue
            out.append(q)
        return out

    async def _add_sparklines(self, quotes: list[dict[str, Any]]) -> None:
        sparks = await asyncio.gather(
            *(self.yahoo.spark(q["symbol"]) for q in quotes), return_exceptions=True
        )
        for quote, spark in zip(quotes, sparks):
            if isinstance(spark, list):
                quote["spark"] = spark

    async def _check_alerts(self, ranked: list[dict[str, Any]]) -> None:
        """Starke Bewegung + echte Nachricht = Display schaltet um."""
        threshold = self.cfg.market.alert_threshold_pct
        for quote in ranked[:3]:
            symbol = quote.get("symbol")
            change = abs(quote.get("change_pct") or 0)
            if not symbol or change < threshold:
                continue
            if alert_sent_recently(symbol, ALERT_COOLDOWN):
                continue

            headlines = await self.news.headlines(
                symbol, quote.get("name", ""), limit=self.cfg.agent.headlines_per_symbol
            )
            brief = await self.agent.brief(quote, headlines)

            if not brief.get("worth_alert"):
                log.info("%s bewegt sich %.1f %%, aber ohne meldenswerten Grund", symbol, change)
                continue

            alert = {
                "symbol": symbol,
                "name": quote.get("name"),
                "change_pct": quote.get("change_pct"),
                "price": quote.get("price"),
                "currency": quote.get("currency"),
                "explanation": brief.get("explanation"),
                "driver": brief.get("driver"),
                "confidence": brief.get("confidence"),
                "sentiment": brief.get("sentiment"),
                "headlines": brief.get("headlines", []),
                "source": brief.get("source"),
                "created_at": time.time(),
            }
            record_alert(symbol, quote.get("change_pct") or 0, alert)
            log.info("MELDUNG: %s %.1f %% - %s", symbol, quote.get("change_pct") or 0, brief.get("driver"))
            self.hub.raise_alert(alert)
            return  # pro Durchlauf hoechstens eine Meldung

    async def explain(self, symbol: str) -> dict[str, Any]:
        """Einordnung zu einem Symbol auf Anfrage (Klick im Display)."""
        quote = await self.yahoo.quote(symbol, with_history=True)
        if not quote:
            return {"error": f"Kein Kurs zu {symbol} gefunden"}
        headlines = await self.news.headlines(symbol, quote.get("name", ""))
        brief = await self.agent.brief(quote, headlines)
        return {"quote": quote, "brief": brief}

    def status(self) -> dict[str, Any]:
        return {
            "last_update": self.last_update,
            "last_error": self.last_error,
            "agent_active": self.agent.active,
            "agent_model": self.cfg.agent.model if self.agent.active else None,
        }


async def _empty_list() -> list[dict[str, Any]]:
    return []
