"""Kleiner SQLite-Speicher: Metadaten-Cache und Kurshistorie."""
from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from typing import Any

from .config import ROOT

DB_PATH = ROOT / "data" / "flightwall.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_conn = _connect()
_conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS cache (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        expires_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sightings (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        seen_at   REAL NOT NULL,
        hex       TEXT,
        callsign  TEXT,
        registration TEXT,
        type_code TEXT,
        airline   TEXT,
        origin    TEXT,
        destination TEXT,
        altitude_ft INTEGER,
        distance_km REAL
    );
    CREATE TABLE IF NOT EXISTS alerts (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL NOT NULL,
        symbol    TEXT NOT NULL,
        change_pct REAL,
        payload   TEXT
    );
    CREATE TABLE IF NOT EXISTS aircraft_models (
        model_key     TEXT NOT NULL,
        type_code     TEXT,
        family        TEXT,
        type_name     TEXT,
        manufacturer  TEXT,
        airline       TEXT NOT NULL,
        airline_key   TEXT NOT NULL,
        first_seen    REAL NOT NULL,
        last_seen     REAL NOT NULL,
        sightings     INTEGER NOT NULL DEFAULT 1,
        artwork_file  TEXT,
        artwork_match TEXT NOT NULL DEFAULT 'none',
        PRIMARY KEY (model_key, airline_key)
    );
    CREATE INDEX IF NOT EXISTS idx_sightings_seen ON sightings(seen_at);
    CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
    CREATE INDEX IF NOT EXISTS idx_aircraft_models_seen ON aircraft_models(last_seen);
    """
)
_conn.commit()


def cache_get(key: str) -> Any | None:
    row = _conn.execute(
        "SELECT value FROM cache WHERE key = ? AND expires_at > ?", (key, time.time())
    ).fetchone()
    return json.loads(row["value"]) if row else None


def cache_set(key: str, value: Any, ttl_seconds: float) -> None:
    _conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time() + ttl_seconds),
    )
    _conn.commit()


def record_sighting(flight: dict[str, Any]) -> None:
    _conn.execute(
        """INSERT INTO sightings
           (seen_at, hex, callsign, registration, type_code, airline,
            origin, destination, altitude_ft, distance_km)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            time.time(),
            flight.get("hex"),
            flight.get("callsign"),
            flight.get("registration"),
            flight.get("type_code"),
            (flight.get("airline") or {}).get("name") if isinstance(flight.get("airline"), dict) else flight.get("airline"),
            (flight.get("origin") or {}).get("iata") if isinstance(flight.get("origin"), dict) else None,
            (flight.get("destination") or {}).get("iata") if isinstance(flight.get("destination"), dict) else None,
            flight.get("altitude_ft"),
            flight.get("distance_km"),
        ),
    )
    _conn.commit()


def recent_sightings(limit: int = 20) -> list[dict[str, Any]]:
    rows = _conn.execute(
        "SELECT * FROM sightings ORDER BY seen_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def sighting_stats() -> dict[str, Any]:
    row = _conn.execute("SELECT COUNT(*) c, COUNT(DISTINCT registration) r FROM sightings").fetchone()
    today = _conn.execute(
        "SELECT COUNT(*) c FROM sightings WHERE seen_at > ?", (time.time() - 86400,)
    ).fetchone()
    return {"total": row["c"], "unique_aircraft": row["r"], "last_24h": today["c"]}


def record_aircraft_model(flight: dict[str, Any], *, count_sighting: bool = True) -> None:
    """Modell/Airline-Kombination dauerhaft fuer die Artwork-Pipeline merken."""
    type_code = (flight.get("type_code") or "").strip().upper() or None
    family = (flight.get("art_family") or "unknown").strip().lower()
    model_key = type_code or family.upper()
    airline = (
        flight.get("display_operator")
        or _airline_name(flight.get("airline"))
        or flight.get("operator")
        or "Unbekannter Betreiber"
    ).strip()
    airline_key = _catalog_key(airline) or "unknown"
    now = time.time()
    artwork_match = flight.get("art_match") or "none"
    artwork_file = flight.get("art_file")
    increment = 1 if count_sighting else 0
    _conn.execute(
        """INSERT INTO aircraft_models
           (model_key, type_code, family, type_name, manufacturer, airline,
            airline_key, first_seen, last_seen, sightings, artwork_file, artwork_match)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(model_key, airline_key) DO UPDATE SET
             type_code = COALESCE(excluded.type_code, aircraft_models.type_code),
             family = COALESCE(NULLIF(excluded.family, ''), aircraft_models.family),
             type_name = COALESCE(NULLIF(excluded.type_name, ''), aircraft_models.type_name),
             manufacturer = COALESCE(NULLIF(excluded.manufacturer, ''), aircraft_models.manufacturer),
             airline = excluded.airline,
             last_seen = excluded.last_seen,
             sightings = aircraft_models.sightings + ?,
             artwork_file = CASE
               WHEN excluded.artwork_match = 'airline' THEN excluded.artwork_file
               ELSE aircraft_models.artwork_file
             END,
             artwork_match = CASE
               WHEN excluded.artwork_match = 'airline' THEN 'airline'
               ELSE aircraft_models.artwork_match
             END""",
        (
            model_key,
            type_code,
            family,
            flight.get("type_name"),
            flight.get("manufacturer"),
            airline,
            airline_key,
            now,
            now,
            increment,
            artwork_file,
            artwork_match,
            increment,
        ),
    )
    _conn.commit()


def aircraft_model_catalog(limit: int = 500) -> list[dict[str, Any]]:
    """Zuletzt gesehene Kombinationen, fehlende Airline-Poster zuerst."""
    rows = _conn.execute(
        """SELECT *, artwork_match != 'airline' AS needs_artwork
           FROM aircraft_models
           ORDER BY needs_artwork DESC, last_seen DESC
           LIMIT ?""",
        (max(1, min(limit, 2000)),),
    ).fetchall()
    return [dict(row) for row in rows]


def _airline_name(value: Any) -> str | None:
    return value.get("name") if isinstance(value, dict) else value


def _catalog_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", ascii_text.casefold())


def record_alert(symbol: str, change_pct: float, payload: dict[str, Any]) -> None:
    _conn.execute(
        "INSERT INTO alerts (created_at, symbol, change_pct, payload) VALUES (?,?,?,?)",
        (time.time(), symbol, change_pct, json.dumps(payload)),
    )
    _conn.commit()


def alert_sent_recently(symbol: str, within_seconds: float) -> bool:
    row = _conn.execute(
        "SELECT 1 FROM alerts WHERE symbol = ? AND created_at > ? LIMIT 1",
        (symbol, time.time() - within_seconds),
    ).fetchone()
    return row is not None
