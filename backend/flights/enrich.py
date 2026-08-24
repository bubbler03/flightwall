"""Flugzeug- und Routendaten nachschlagen (adsbdb, hexdb als Fallback).

Beides kostenlos und ohne Key. Ergebnisse werden lange gecached - eine
Registrierung aendert ihren Flugzeugtyp nicht mehr.
"""
from __future__ import annotations

import logging
from typing import Any

from ..http import Http
from ..store import cache_get, cache_set

log = logging.getLogger(__name__)

ADSBDB_AIRCRAFT = "https://api.adsbdb.com/v0/aircraft/{hex}"
ADSBDB_CALLSIGN = "https://api.adsbdb.com/v0/callsign/{callsign}"
HEXDB_AIRCRAFT = "https://hexdb.io/api/v1/aircraft/{hex}"

AIRCRAFT_TTL = 60 * 60 * 24 * 30      # 30 Tage
ROUTE_TTL = 60 * 60 * 24 * 3         # 3 Tage
NEGATIVE_TTL = 60 * 60 * 6           # nichts gefunden: in 6h nochmal probieren


class Enricher:
    def __init__(self, timeout: float = 8.0) -> None:
        self._http = Http(timeout=timeout, max_parallel=2, min_interval=0.3,
                          headers={"Accept": "application/json"})

    async def _get_json(self, url: str) -> dict[str, Any] | None:
        return await self._http.json(url)

    async def aircraft(self, hex_code: str) -> dict[str, Any]:
        """Hersteller, Typ, Halter zu einem ICAO-Hex."""
        if not hex_code:
            return {}
        key = f"ac:{hex_code}"
        cached = cache_get(key)
        if cached is not None:
            return cached

        info: dict[str, Any] = {}
        data = await self._get_json(ADSBDB_AIRCRAFT.format(hex=hex_code))
        ac = ((data or {}).get("response") or {}).get("aircraft") or {}
        if ac:
            info = {
                "registration": ac.get("registration"),
                "type_code": ac.get("icao_type"),
                "type_name": ac.get("type"),
                "manufacturer": ac.get("manufacturer"),
                "operator": ac.get("registered_owner"),
                "operator_country": ac.get("registered_owner_country_name"),
            }
        else:
            data = await self._get_json(HEXDB_AIRCRAFT.format(hex=hex_code))
            if data:
                info = {
                    "registration": data.get("Registration"),
                    "type_code": data.get("ICAOTypeCode"),
                    "type_name": data.get("Type"),
                    "manufacturer": data.get("Manufacturer"),
                    "operator": data.get("RegisteredOwners"),
                    "operator_country": None,
                }

        info = {k: v for k, v in info.items() if v}
        cache_set(key, info, AIRCRAFT_TTL if info else NEGATIVE_TTL)
        return info

    async def route(self, callsign: str) -> dict[str, Any]:
        """Airline, Start- und Zielflughafen zu einem Callsign."""
        if not callsign:
            return {}
        key = f"rt:{callsign}"
        cached = cache_get(key)
        if cached is not None:
            return cached

        data = await self._get_json(ADSBDB_CALLSIGN.format(callsign=callsign))
        fr = ((data or {}).get("response") or {}).get("flightroute") or {}
        info: dict[str, Any] = {}
        if fr:
            airline = fr.get("airline") or {}
            info = {
                "airline": {
                    "name": airline.get("name"),
                    "icao": airline.get("icao"),
                    "iata": airline.get("iata"),
                    "country": airline.get("country"),
                } if airline.get("name") else None,
                "callsign_iata": fr.get("callsign_iata"),
                "origin": _airport(fr.get("origin")),
                "destination": _airport(fr.get("destination")),
            }
            info = {k: v for k, v in info.items() if v}

        cache_set(key, info, ROUTE_TTL if info else NEGATIVE_TTL)
        return info

    async def aclose(self) -> None:
        await self._http.aclose()


def _airport(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return {
        "iata": raw.get("iata_code"),
        "icao": raw.get("icao_code"),
        "name": raw.get("name"),
        "city": raw.get("municipality"),
        "country": raw.get("country_name"),
        "country_iso": raw.get("country_iso_name"),
        "lat": raw.get("latitude"),
        "lon": raw.get("longitude"),
    }
