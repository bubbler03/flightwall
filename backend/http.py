"""Gemeinsamer HTTP-Client.

Yahoo Finance blockt Python-Standardclients anhand ihres TLS-Fingerabdrucks
(die Antwort ist dann 429, unabhaengig von der Anfragerate). curl_cffi spricht
mit dem Fingerabdruck eines echten Chrome und kommt damit durch. Ist das Paket
nicht installiert, faellt alles auf httpx zurueck - dann funktionieren die
Flug- und News-Quellen weiter, nur Yahoo antwortet moeglicherweise mit 429.
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

log = logging.getLogger(__name__)

try:
    from curl_cffi import AsyncSession as _CurlSession

    HAS_CURL_CFFI = True
except ImportError:  # pragma: no cover
    _CurlSession = None
    HAS_CURL_CFFI = False

import httpx

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class Http:
    """Duenne Huelle um curl_cffi bzw. httpx mit Drosselung und Wiederholversuchen."""

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        max_parallel: int = 3,
        min_interval: float = 0.25,
        retries: int = 3,
        headers: dict[str, str] | None = None,
        impersonate: str = "chrome",
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.min_interval = min_interval
        self._headers = {"User-Agent": DEFAULT_UA, **(headers or {})}
        self._sem = asyncio.Semaphore(max_parallel)
        self._lock = asyncio.Lock()
        self._last_request = 0.0
        self._impersonate = impersonate
        self._session: Any = None

    async def _ensure_session(self) -> Any:
        if self._session is None:
            if HAS_CURL_CFFI:
                self._session = _CurlSession(impersonate=self._impersonate, headers=self._headers)
            else:
                self._session = httpx.AsyncClient(
                    timeout=self.timeout, headers=self._headers, follow_redirects=True
                )
        return self._session

    async def _throttle(self) -> None:
        """Mindestabstand zwischen zwei Anfragen einhalten."""
        async with self._lock:
            loop = asyncio.get_running_loop()
            wait = self.min_interval - (loop.time() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = loop.time()

    async def get(self, url: str, params: dict[str, Any] | None = None) -> Any | None:
        """GET mit Wiederholversuch; gibt das Response-Objekt oder None zurueck."""
        session = await self._ensure_session()
        for attempt in range(self.retries):
            async with self._sem:
                await self._throttle()
                try:
                    if HAS_CURL_CFFI:
                        resp = await session.get(url, params=params, timeout=self.timeout)
                    else:
                        resp = await session.get(url, params=params)
                except Exception as exc:
                    log.debug("Anfrage fehlgeschlagen (%s): %s", url, exc)
                    resp = None

            if resp is not None and resp.status_code == 200:
                return resp
            if resp is not None and resp.status_code in (401, 403, 404):
                log.debug("Endpunkt liefert %s: %s", resp.status_code, url)
                return None

            if attempt < self.retries - 1:
                backoff = 1.5 * (2 ** attempt) + random.uniform(0, 0.6)
                status = resp.status_code if resp is not None else "Netzwerkfehler"
                log.debug("Antwort %s, neuer Versuch in %.1fs (%s)", status, backoff, url)
                await asyncio.sleep(backoff)

        log.warning("Anfrage endgueltig fehlgeschlagen: %s", url)
        return None

    async def json(self, url: str, params: dict[str, Any] | None = None) -> Any | None:
        resp = await self.get(url, params)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            log.debug("Antwort war kein JSON: %s", url)
            return None

    async def bytes(self, url: str, params: dict[str, Any] | None = None) -> bytes | None:
        resp = await self.get(url, params)
        return resp.content if resp is not None else None

    async def aclose(self) -> None:
        if self._session is None:
            return
        try:
            close = self._session.aclose if hasattr(self._session, "aclose") else self._session.close
            result = close()
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            pass
        self._session = None
