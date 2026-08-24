"""Event-Bus und Ansichts-Zustand.

Der Hub haelt fest, was gerade auf dem Display zu sehen ist (Flugzeug oder
Aktien) und verteilt Aenderungen per Server-Sent-Events an alle offenen
Browser-Fenster.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

log = logging.getLogger(__name__)

VIEWS = ("flight", "stocks")


class Hub:
    def __init__(self, default_view: str = "flight", return_after: int = 180) -> None:
        self.default_view = default_view if default_view in VIEWS else "flight"
        self.return_after = return_after
        self.view = self.default_view
        self.view_changed_at = time.time()
        self.view_pinned_by_user = False
        self.state: dict[str, Any] = {"flight": None, "fleet": [], "market": None, "alert": None}
        self._subscribers: set[asyncio.Queue] = set()

    # -- Abonnenten ---------------------------------------------------
    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    @property
    def listener_count(self) -> int:
        return len(self._subscribers)

    def publish(self, event: str, data: Any) -> None:
        """Ereignis an alle offenen Browser schicken."""
        payload = json.dumps({"event": event, "data": data, "ts": time.time()})
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                log.debug("Abonnent zu langsam, Ereignis verworfen")

    # -- Zustand ------------------------------------------------------
    def set_flight(self, flight: dict[str, Any] | None) -> None:
        previous = self.state.get("flight")
        self.state["flight"] = flight
        prev_key = (previous or {}).get("hex")
        new_key = (flight or {}).get("hex")
        self.publish("flight", {"flight": flight, "changed": prev_key != new_key})

    def set_fleet(self, fleet: list[dict[str, Any]]) -> None:
        """Die bis zu drei naechsten Flugzeuge, naechstes zuerst."""
        previous = self.state.get("fleet") or []
        self.state["fleet"] = fleet
        prev_keys = [f.get("hex") for f in previous]
        new_keys = [f.get("hex") for f in fleet]
        self.publish("fleet", {"fleet": fleet, "changed": prev_keys != new_keys})

    def set_market(self, market: dict[str, Any]) -> None:
        self.state["market"] = market
        self.publish("market", market)

    # -- Ansicht ------------------------------------------------------
    def set_view(self, view: str, *, by_user: bool = False, reason: str = "") -> str:
        if view not in VIEWS:
            return self.view
        self.view = view
        self.view_changed_at = time.time()
        self.view_pinned_by_user = by_user and view != self.default_view
        self.publish("view", {"view": view, "by_user": by_user, "reason": reason})
        return self.view

    def toggle_view(self, *, by_user: bool = True) -> str:
        nxt = VIEWS[(VIEWS.index(self.view) + 1) % len(VIEWS)]
        return self.set_view(nxt, by_user=by_user, reason="toggle")

    def raise_alert(self, alert: dict[str, Any]) -> None:
        """Marktmeldung: Display springt auf die Aktien-Ansicht."""
        self.state["alert"] = alert
        self.publish("alert", alert)
        self.set_view("stocks", by_user=False, reason="alert")

    def maybe_return_to_default(self) -> None:
        """Nach der Ruhezeit zurueck auf die Flug-Ansicht (Screensaver)."""
        if self.view == self.default_view or self.return_after <= 0:
            return
        if time.time() - self.view_changed_at >= self.return_after:
            self.set_view(self.default_view, by_user=False, reason="timeout")

    def snapshot(self) -> dict[str, Any]:
        return {
            "view": self.view,
            "default_view": self.default_view,
            "view_changed_at": self.view_changed_at,
            "flight": self.state.get("flight"),
            "fleet": self.state.get("fleet") or [],
            "market": self.state.get("market"),
            "alert": self.state.get("alert"),
        }
