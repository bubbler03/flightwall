"""Hardware-Knopf am GPIO (optional).

Auf dem Pi 5 laeuft gpiozero ueber lgpio:
    sudo apt install python3-lgpio
    pip install gpiozero lgpio

Ohne Knopf funktioniert das Display genauso - dann schaltet die Leertaste,
ein Klick oder ein Fingertipp auf dem Touchscreen um.
"""
from __future__ import annotations

import asyncio
import logging

from .config import Button as ButtonConfig
from .hub import Hub

log = logging.getLogger(__name__)


class ButtonWatcher:
    def __init__(self, config: ButtonConfig, hub: Hub) -> None:
        self.cfg = config
        self.hub = hub
        self._button = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        if not self.cfg.enabled:
            return
        try:
            from gpiozero import Button as GpioButton
        except ImportError:
            log.warning("gpiozero nicht installiert - Hardware-Knopf bleibt aus")
            return

        try:
            self._loop = asyncio.get_running_loop()
            # bounce_time entprellt den Taster
            self._button = GpioButton(self.cfg.gpio_pin, pull_up=True, bounce_time=0.08)
            self._button.when_pressed = self._on_press
            log.info("Knopf an GPIO %s aktiv (%s)", self.cfg.gpio_pin, self.cfg.action)
        except Exception as exc:
            log.warning("Knopf konnte nicht eingerichtet werden: %s", exc)

    def _on_press(self) -> None:
        """Laeuft im gpiozero-Thread - deshalb zurueck in die Event-Loop reichen."""
        if not self._loop:
            return
        self._loop.call_soon_threadsafe(self._toggle)

    def _toggle(self) -> None:
        view = self.hub.toggle_view(by_user=True)
        log.info("Knopf gedrueckt -> Ansicht %s", view)

    def stop(self) -> None:
        if self._button is not None:
            try:
                self._button.close()
            except Exception:
                pass
            self._button = None
