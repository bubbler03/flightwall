"""Konfiguration aus config.yaml laden."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
EXAMPLE_PATH = ROOT / "config.example.yaml"


@dataclass
class Location:
    lat: float = 50.11
    lon: float = 8.68
    label: str = ""
    radius_nm: int = 25


@dataclass
class Flights:
    poll_seconds: int = 10
    switch_hysteresis_km: float = 2.0
    linger_seconds: int = 90
    max_tracked: int = 3
    max_radius_nm: int = 150
    radius_step_nm: int = 25
    radius_margin_nm: int = 5


@dataclass
class Market:
    poll_seconds: int = 60
    min_market_cap: float = 10_000_000_000
    min_volume: int = 500_000
    move_threshold_pct: float = 4.0
    alert_threshold_pct: float = 7.0
    watchlist: list[str] = field(default_factory=list)


@dataclass
class Agent:
    enabled: bool = True
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-5"
    headlines_per_symbol: int = 6

    @property
    def api_key(self) -> str:
        return self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def active(self) -> bool:
        return self.enabled and bool(self.api_key)


@dataclass
class NightDim:
    enabled: bool = True
    start_hour: int = 22
    end_hour: int = 7
    opacity: float = 0.55


@dataclass
class Display:
    default_view: str = "flight"
    return_to_default_after: int = 180
    night_dim: NightDim = field(default_factory=NightDim)


@dataclass
class Button:
    enabled: bool = False
    gpio_pin: int = 17
    action: str = "toggle"


@dataclass
class Server:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class Config:
    location: Location = field(default_factory=Location)
    flights: Flights = field(default_factory=Flights)
    market: Market = field(default_factory=Market)
    agent: Agent = field(default_factory=Agent)
    display: Display = field(default_factory=Display)
    button: Button = field(default_factory=Button)
    server: Server = field(default_factory=Server)


def _build(cls, data: dict[str, Any] | None):
    """Dataclass aus dict bauen, unbekannte Keys ignorieren."""
    data = data or {}
    known = {f.name for f in cls.__dataclass_fields__.values()}
    return cls(**{k: v for k, v in data.items() if k in known})


def load(path: Path | None = None) -> Config:
    path = path or CONFIG_PATH
    if not path.exists():
        path = EXAMPLE_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    display_raw = raw.get("display") or {}
    display = _build(Display, {k: v for k, v in display_raw.items() if k != "night_dim"})
    display.night_dim = _build(NightDim, display_raw.get("night_dim"))

    return Config(
        location=_build(Location, raw.get("location")),
        flights=_build(Flights, raw.get("flights")),
        market=_build(Market, raw.get("market")),
        agent=_build(Agent, raw.get("agent")),
        display=display,
        button=_build(Button, raw.get("button")),
        server=_build(Server, raw.get("server")),
    )


CONFIG = load()
