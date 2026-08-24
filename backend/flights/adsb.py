"""ADS-B-Positionsdaten, kostenlos und ohne API-Key.

Abgefragt wird der Reihe nach: adsb.lol, dann adsb.fi - beide liefern das
readsb/dump1090-Format, die erste antwortende Quelle gewinnt. Wer spaeter
einen eigenen RTL-SDR anschliesst, uebergibt dem Client die lokale
dump1090-URL - die Feldnamen sind identisch.
"""
from __future__ import annotations

import logging
from typing import Any

from ..http import Http

log = logging.getLogger(__name__)

# Freie Quellen im readsb-Format. Die Reihenfolge ist die Fallback-Kette.
SOURCES = (
    ("adsb.lol", "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist}"),
    ("adsb.fi", "https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{dist}"),
)
USER_AGENT = "flightwall/1.0 (raspberry pi wall display)"


class AdsbClient:
    def __init__(self, timeout: float = 12.0, base_url: str | None = None) -> None:
        # Wie Yahoo weist auch adsb.lol Standard-Python-Clients ab, sobald man
        # einmal ins Rate-Limit gelaufen ist - dann bleiben die Verbindungen
        # haengen. Ueber den gemeinsamen Client kommen die Anfragen durch.
        self._http = Http(timeout=timeout, max_parallel=1, min_interval=1.0,
                          retries=2, headers={"Accept": "application/json"})
        self._base_url = base_url
        self.active_source = SOURCES[0][0]

    async def aircraft_near(self, lat: float, lon: float, dist_nm: int) -> list[dict[str, Any]] | None:
        """Alle Flugzeuge im Radius.

        Leere Liste = niemand unterwegs. None = keine Quelle hat geantwortet.
        Der Unterschied ist wichtig: nachts ist der Himmel oft wirklich leer,
        das ist kein Grund, seltener nachzufragen.
        """
        if self._base_url:  # eigener Empfaenger (dump1090): nur diese URL
            data = await self._http.json(self._base_url)
            return None if data is None else (data.get("ac") or data.get("aircraft") or [])

        # Die zuletzt erfolgreiche Quelle zuerst probieren. Sonst wuerde ein
        # laengerer Ausfall der Primaerquelle jeden 10-Sekunden-Poll um deren
        # kompletten Timeout verzoegern, obwohl der Fallback gesund ist.
        ordered_sources = sorted(SOURCES, key=lambda source: source[0] != self.active_source)
        for name, template in ordered_sources:
            data = await self._http.json(template.format(lat=lat, lon=lon, dist=dist_nm))
            if data is not None:
                if name != self.active_source:
                    log.info("Flugquelle gewechselt: %s", name)
                    self.active_source = name
                return data.get("ac") or data.get("aircraft") or []
            log.warning("%s antwortet nicht - naechste Quelle wird versucht", name)
        return None

    async def aclose(self) -> None:
        await self._http.aclose()


def normalise(raw: dict[str, Any]) -> dict[str, Any]:
    """Rohdatensatz auf die Felder reduzieren, die das Display braucht."""
    alt = raw.get("alt_baro")
    if alt == "ground":
        alt = 0
    return {
        "hex": (raw.get("hex") or "").strip().lower(),
        "callsign": (raw.get("flight") or "").strip() or None,
        "registration": (raw.get("r") or "").strip() or None,
        "type_code": (raw.get("t") or "").strip().upper() or None,
        "lat": raw.get("lat"),
        "lon": raw.get("lon"),
        "altitude_ft": int(alt) if isinstance(alt, (int, float)) else None,
        "ground_speed_kt": raw.get("gs"),
        "track_deg": raw.get("track"),
        "vertical_rate_fpm": raw.get("baro_rate") or raw.get("geom_rate"),
        "squawk": raw.get("squawk"),
        "category": raw.get("category"),
        "emergency": raw.get("emergency") if raw.get("emergency") not in (None, "none") else None,
        "on_ground": alt == 0,
    }
