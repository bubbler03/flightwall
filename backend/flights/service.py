"""Haelt dauerhaft die naechsten Flugzeuge ueber dir nach (bis zu max_tracked)."""
from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Any

from ..config import Config
from ..hub import Hub
from ..store import (
    aircraft_model_catalog,
    record_aircraft_model,
    record_sighting,
    sighting_stats,
    update_aircraft_model_artwork,
)
from . import geo
from .adsb import AdsbClient, normalise
from .artwork import FAMILIES, ArtworkIndex, family_for

log = logging.getLogger(__name__)


class FlightService:
    def __init__(self, config: Config, hub: Hub, enricher, client: AdsbClient | None = None) -> None:
        self.cfg = config
        self.hub = hub
        self.client = client or AdsbClient()
        self.enricher = enricher
        self.artwork = ArtworkIndex()
        self.fleet: list[dict[str, Any]] = []      # naechstes zuerst, bis zu max_tracked
        self.current: dict[str, Any] | None = None  # = fleet[0], fuer alte Schnittstellen
        self.last_seen_at: float = 0.0
        self.last_error: str | None = None
        self.active_radius_nm = max(1, config.location.radius_nm)
        self.last_query_radius_nm = self.active_radius_nm
        self.candidate_count = 0
        self.nearest_candidate_hexes: list[str] = []
        self.radius_exhausted = False
        self._failed_polls = 0
        self._task: asyncio.Task | None = None

    # -- Lebenszyklus --------------------------------------------------
    def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="flight-service")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.aclose()

    async def _loop(self) -> None:
        while True:
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # Schleife darf nie sterben
                self.last_error = str(exc)
                log.exception("Fehler im Flug-Loop: %s", exc)
            await asyncio.sleep(self._next_delay())

    def _next_delay(self) -> float:
        """Antwortet keine Quelle, wird der Abstand schrittweise groesser.

        So laeuft der Pi nach einer Sperre nicht dauerhaft dagegen an, kommt aber
        von selbst zurueck, sobald wieder Daten fliessen (hoechstens 5 Minuten).
        """
        base = self.cfg.flights.poll_seconds
        if self._failed_polls <= 3:
            return base
        return min(base * 2 ** min(self._failed_polls - 3, 5), 300)

    # -- Ein Durchlauf -------------------------------------------------
    async def tick(self) -> dict[str, Any] | None:
        loc = self.cfg.location
        base_radius = max(1, loc.radius_nm)
        max_radius = max(base_radius, self.cfg.flights.max_radius_nm)
        step = max(1, self.cfg.flights.radius_step_nm)
        target = max(1, self.cfg.flights.max_tracked)
        radius = max(base_radius, min(self.active_radius_nm, max_radius))
        raw = await self.client.aircraft_near(loc.lat, loc.lon, radius)

        if raw is None:
            self._failed_polls += 1
            self.last_error = "Keine Flugquelle erreichbar"
            self.candidate_count = 0
            self.nearest_candidate_hexes = []
            log.warning("Keine Antwort von einer Flugquelle (%s. Versuch), naechste Abfrage in %.0fs",
                        self._failed_polls, self._next_delay())
            await self._update_fleet([])
            return self.current

        self._failed_polls = 0
        self.last_error = None
        ranked = self._rank(raw)

        # Reicht der normale Radius nicht, noch im selben Durchlauf erweitern.
        # Der vergroesserte Radius bleibt fuer den naechsten Poll aktiv, damit
        # nicht bei jeder Abfrage wieder mehrere HTTP-Anfragen noetig sind.
        while len(ranked) < target and radius < max_radius:
            radius = min(max_radius, radius + step)
            expanded = await self.client.aircraft_near(loc.lat, loc.lon, radius)
            if expanded is None:
                log.warning("Radius-Erweiterung auf %s nm ohne Antwort", radius)
                break
            ranked = self._rank(expanded)

        self.last_query_radius_nm = radius
        self.candidate_count = len(ranked)
        self.nearest_candidate_hexes = [
            aircraft["hex"] for aircraft in ranked[:target] if aircraft.get("hex")
        ]
        self.radius_exhausted = len(ranked) < target and radius >= max_radius
        self.active_radius_nm = radius

        # Wenn alle drei wieder deutlich innerhalb eines kleineren Radius
        # liegen, wird pro Poll nur eine Stufe zurueckgenommen.
        if len(ranked) >= target and radius > base_radius:
            third_ground_nm = ranked[target - 1]["ground_distance_km"] / 1.852
            desired = max(
                base_radius,
                min(max_radius, math.ceil(third_ground_nm + self.cfg.flights.radius_margin_nm)),
            )
            if desired <= radius - step:
                self.active_radius_nm = max(desired, radius - step)

        await self._update_fleet(ranked)
        return self.current

    # -- Die Flotte ----------------------------------------------------
    async def _update_fleet(self, candidates: list[dict[str, Any]]) -> None:
        """Zeigt exakt die naechsten Kandidaten; Linger fuellt nur Datenluecken."""
        now = time.time()
        max_tracked = max(1, self.cfg.flights.max_tracked)
        linger = self.cfg.flights.linger_seconds
        existing = {member["hex"]: member for member in self.fleet}
        kept: list[dict[str, Any]] = []
        selected: set[str] = set()

        # Sobald mindestens drei Live-Kandidaten vorliegen, ist dies ohne
        # Hysterese exakt candidates[:3] und damit die echte Naehe-Reihenfolge.
        for fresh in candidates:
            if len(kept) >= max_tracked:
                break
            hex_code = fresh.get("hex")
            if not hex_code or hex_code in selected:
                continue
            member = existing.get(hex_code)
            if member is None:
                member = await self._join(fresh, now)
            else:
                self._refresh_member(member, fresh, now)
            kept.append(member)
            selected.add(hex_code)

        # Nur falls die Quelle weniger als drei Live-Kandidaten liefert, kurze
        # ADS-B-Aussetzer mit den zuletzt gesehenen Flugzeugen ueberbruecken.
        if len(kept) < max_tracked:
            for member in self.fleet:
                if member["hex"] in selected:
                    continue
                if now - member.get("last_seen", now) <= linger:
                    member["is_stale"] = True
                    kept.append(member)
                    selected.add(member["hex"])
                    if len(kept) >= max_tracked:
                        break
                else:
                    log.info("Aus dem Radar verschwunden: %s", self._label(member))

        kept.sort(key=lambda aircraft: aircraft["distance_km"])

        self.fleet = kept
        self.current = kept[0] if kept else None
        self.last_seen_at = max((m.get("last_seen", 0.0) for m in kept), default=0.0)
        self.hub.set_fleet(self.fleet)
        self.hub.set_flight(self.current)

    @staticmethod
    def _refresh_member(member: dict[str, Any], fresh: dict[str, Any], now: float) -> None:
        positional = (
            "lat", "lon", "altitude_ft", "ground_speed_kt", "track_deg",
            "vertical_rate_fpm", "ground_distance_km", "distance_km",
            "bearing_deg", "compass", "elevation_deg", "climb_state",
            "squawk", "emergency", "category",
        )
        member.update({key: fresh.get(key) for key in positional})
        for key in ("callsign", "registration", "type_code"):
            if fresh.get(key):
                member[key] = fresh[key]
        member["updated_at"] = now
        member["last_seen"] = now
        member["is_stale"] = False

    async def _join(self, ac: dict[str, Any], now: float) -> dict[str, Any]:
        """Neues Mitglied: Metadaten ergaenzen, Sichtung notieren."""
        enriched = await self._enrich(ac)
        enriched["last_seen"] = now
        enriched["is_stale"] = False
        record_sighting(enriched)
        record_aircraft_model(enriched)
        log.info("Neues Flugzeug: %s (%s) %.1f km, %s ft",
                 self._label(enriched), enriched.get("type_code"),
                 enriched.get("distance_km", 0), enriched.get("altitude_ft"))
        return enriched

    @staticmethod
    def _label(ac: dict[str, Any]) -> str:
        return ac.get("callsign") or ac.get("registration") or ac.get("hex") or "?"

    def _rank(self, raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Alle brauchbaren Flugzeuge im Radius, sortiert nach Naehe.

        Es zaehlt allein die Entfernung: das Display zeigt immer die bis zu
        max_tracked naechsten, ohne Hoehen- oder Richtungsfilter.
        """
        loc = self.cfg.location
        out: list[dict[str, Any]] = []
        for raw in raw_list:
            ac = normalise(raw)
            if ac["lat"] is None or ac["lon"] is None or ac["on_ground"]:
                continue
            ground_km = geo.haversine_km(loc.lat, loc.lon, ac["lat"], ac["lon"])
            elev = geo.elevation_deg(ground_km, ac["altitude_ft"])
            alt_km = (ac["altitude_ft"] or 0) * geo.FEET_TO_KM
            bearing = geo.bearing_deg(loc.lat, loc.lon, ac["lat"], ac["lon"])
            vr = ac.get("vertical_rate_fpm") or 0
            ac.update({
                "ground_distance_km": round(ground_km, 2),
                "distance_km": round(math.hypot(ground_km, alt_km), 2),
                "bearing_deg": round(bearing, 1),
                "compass": geo.compass_point(bearing),
                "elevation_deg": round(elev, 1),
                "climb_state": "steigt" if vr > 300 else "sinkt" if vr < -300 else "Reiseflug",
                "updated_at": time.time(),
            })
            out.append(ac)
        out.sort(key=lambda a: a["distance_km"])
        return out

    async def _enrich(self, ac: dict[str, Any]) -> dict[str, Any]:
        """Metadaten, Route und passendes Bild ergaenzen."""
        meta_task = self.enricher.aircraft(ac["hex"])
        route_task = self.enricher.route(ac["callsign"]) if ac.get("callsign") else _empty()
        meta, route = await asyncio.gather(meta_task, route_task)

        ac["registration"] = ac.get("registration") or meta.get("registration")
        ac["type_code"] = ac.get("type_code") or meta.get("type_code")
        ac["type_name"] = meta.get("type_name")
        ac["manufacturer"] = meta.get("manufacturer")
        ac["operator"] = meta.get("operator")
        ac.update(self._validated_route(ac, route))

        airline = ac.get("airline") or {}
        route_airline = airline.get("name") if isinstance(airline, dict) else None
        ac["display_operator"] = route_airline or ac.get("operator") or "Unbekannter Betreiber"

        slug, label, category = family_for(ac.get("type_code"), ac.get("category"))
        ac["art_family"] = slug
        ac["art_label"] = label
        ac["art_category"] = category
        self._assign_artwork(ac)
        # Der type_name aus der Datenbank ist oft ein Werkscode ("321 271NXSL"),
        # deshalb steht der kuratierte Familienname im Titel.
        ac["display_title"] = label
        return ac

    def _assign_artwork(self, ac: dict[str, Any]) -> None:
        airline = ac.get("airline") or {}
        route_airline = airline.get("name") if isinstance(airline, dict) else None
        match = self.artwork.match(
            ac["art_family"],
            ac["art_category"],
            airlines=[route_airline, ac.get("display_operator"), ac.get("operator")],
            seed=ac.get("registration") or ac.get("hex"),
            type_code=ac.get("type_code"),
        )
        ac["art_url"] = match["url"]
        ac["art_file"] = match["file"]
        ac["art_match"] = match["match"]
        ac["art_operator"] = match["operator"]

    @staticmethod
    def _validated_route(ac: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        """Offensichtlich veraltete Callsign-Routen nicht als Fakten anzeigen."""
        if not route:
            return {}

        origin = route.get("origin") or {}
        destination = route.get("destination") or {}
        try:
            plausible = geo.route_position_plausible(
                float(ac["lat"]),
                float(ac["lon"]),
                float(origin["lat"]),
                float(origin["lon"]),
                float(destination["lat"]),
                float(destination["lon"]),
            )
        except (KeyError, TypeError, ValueError):
            plausible = False

        if plausible:
            return {**route, "route_status": "verified"}

        # Die Airline bleibt als vorsichtige Callsign-Einordnung erhalten; die
        # unplausiblen Flughaefen und die daraus abgeleitete IATA-Flugnummer
        # werden nicht an UI oder Sichtungsspeicher weitergereicht.
        cleaned = {"route_status": "unverified"}
        if route.get("airline"):
            cleaned["airline"] = route["airline"]
        log.info(
            "Unplausible Route ausgeblendet: %s %s -> %s bei %.3f, %.3f",
            ac.get("callsign"),
            origin.get("iata") or origin.get("icao") or "?",
            destination.get("iata") or destination.get("icao") or "?",
            ac.get("lat", 0),
            ac.get("lon", 0),
        )
        return cleaned

    def refresh_artwork(self) -> dict[str, Any]:
        """Manifest neu lesen und sichtbare wie gespeicherte Modelle neu zuordnen."""
        self.artwork.refresh()

        catalog_updates: list[tuple[str | None, str, str, str]] = []
        for model in aircraft_model_catalog(limit=2000):
            family = (model.get("family") or "").strip().lower()
            type_code = (model.get("type_code") or "").strip().upper() or None
            if family in FAMILIES:
                category = FAMILIES[family][1]
            else:
                family, _, category = family_for(type_code)
            match = self.artwork.match(
                family,
                category,
                [model.get("airline")],
                seed=f"catalog:{model.get('model_key')}:{model.get('airline_key')}",
                type_code=type_code,
            )
            catalog_updates.append((
                match["file"],
                match["match"] or "none",
                model["model_key"],
                model["airline_key"],
            ))
        catalog_updated = update_aircraft_model_artwork(catalog_updates)

        for aircraft in self.fleet:
            self._assign_artwork(aircraft)
            record_aircraft_model(aircraft, count_sighting=False)
        self.hub.set_fleet(self.fleet)
        self.hub.set_flight(self.current)
        return {**self.artwork.coverage(), "catalog_updated": catalog_updated}

    def status(self) -> dict[str, Any]:
        fleet_hexes = [aircraft.get("hex") for aircraft in self.fleet]
        target = max(1, self.cfg.flights.max_tracked)
        return {
            "has_flight": self.current is not None,
            "fleet": len(self.fleet),
            "target_fleet": target,
            "candidate_count": self.candidate_count,
            "nearest_candidate_hexes": self.nearest_candidate_hexes,
            "fleet_hexes": fleet_hexes,
            "exact_nearest_verified": (
                len(self.nearest_candidate_hexes) == target
                and fleet_hexes == self.nearest_candidate_hexes
            ),
            "source": self.client.active_source,
            "base_radius_nm": self.cfg.location.radius_nm,
            "query_radius_nm": self.last_query_radius_nm,
            "next_radius_nm": self.active_radius_nm,
            "max_radius_nm": max(self.cfg.location.radius_nm, self.cfg.flights.max_radius_nm),
            "radius_exhausted": self.radius_exhausted,
            "poll_seconds": self._next_delay(),
            "failed_polls": self._failed_polls,
            "last_seen_at": self.last_seen_at,
            "last_error": self.last_error,
            "artwork": self.artwork.coverage(),
            "stats": sighting_stats(),
        }


async def _empty() -> dict[str, Any]:
    return {}
