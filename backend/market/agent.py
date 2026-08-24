"""Der autonome Teil: Claude liest die Schlagzeilen zu einer Kursbewegung,
erklaert sie in einem Satz und entscheidet, ob es das Display wert ist.

Ohne API-Key laeuft alles weiter - dann wird einfach die aktuellste
Schlagzeile angezeigt statt einer Einordnung.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from ..config import Agent as AgentConfig
from ..store import cache_get, cache_set

log = logging.getLogger(__name__)

BRIEF_TTL = 600  # eine Einordnung 10 Minuten lang wiederverwenden

SYSTEM_PROMPT = """Du bist ein Markt-Analyst fuer ein Wanddisplay im Wohnzimmer.
Du bekommst eine auffaellige Kursbewegung und die dazu gefundenen Schlagzeilen.

Deine Aufgabe:
1. Erklaere in EINEM kurzen deutschen Satz, warum sich die Aktie bewegt.
2. Sage ehrlich, wie sicher der Zusammenhang ist. Wenn die Schlagzeilen die
   Bewegung nicht erklaeren, schreibe das ("kein klarer Ausloeser erkennbar")
   und setze confidence auf "niedrig". Erfinde niemals einen Grund.
3. Entscheide, ob die Meldung wichtig genug ist, das Display vom Flugzeugbild
   auf die Aktien-Ansicht umzuschalten. Umschalten lohnt bei echten Nachrichten
   (Quartalszahlen, Uebernahme, Prognose, Rueckruf, Regulierung, Leitungswechsel),
   nicht bei blossem Marktrauschen oder wenn nur Kursbewegung ohne Grund vorliegt.

Schreibe knapp und sachlich - der Text steht in grosser Schrift an einer Wand.
Keine Anlageberatung, keine Empfehlungen, keine Kursziele."""


class MarketAgent:
    def __init__(self, config: AgentConfig) -> None:
        self.cfg = config
        self._client = None
        if config.active:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=config.api_key)
                log.info("Markt-Agent aktiv (%s)", config.model)
            except ImportError:
                log.warning("Paket 'anthropic' fehlt - Agent laeuft ohne KI-Einordnung")
        elif config.enabled:
            log.info("Markt-Agent ohne API-Key - zeige nur Schlagzeilen")

    @property
    def active(self) -> bool:
        return self._client is not None

    async def brief(self, quote: dict[str, Any], headlines: list[dict[str, Any]]) -> dict[str, Any]:
        """Einordnung zu einer Kursbewegung."""
        symbol = quote.get("symbol", "?")
        key = f"brief:{symbol}:{round(quote.get('change_pct') or 0, 1)}"
        cached = cache_get(key)
        if cached is not None:
            return cached

        result = await self._ask_claude(quote, headlines) if self._client else None
        if result is None:
            result = _fallback(quote, headlines)

        result["headlines"] = headlines[:4]
        cache_set(key, result, BRIEF_TTL)
        return result

    async def _ask_claude(self, quote: dict[str, Any], headlines: list[dict[str, Any]]) -> dict[str, Any] | None:
        news_block = "\n".join(
            f"- {h['title']}" + (f" ({h.get('source')})" if h.get("source") else "")
            for h in headlines[: self.cfg.headlines_per_symbol]
        ) or "(keine Schlagzeilen gefunden)"

        vol = quote.get("volume")
        avg = quote.get("avg_volume")
        vol_note = ""
        if vol and avg:
            vol_note = f"\nHandelsvolumen: {vol:,} (Schnitt: {avg:,}, also {vol / avg:.1f}-faches Volumen)"

        user_msg = (
            f"Aktie: {quote.get('name')} ({quote.get('symbol')})\n"
            f"Kurs: {quote.get('price')} {quote.get('currency') or ''}\n"
            f"Tagesveraenderung: {quote.get('change_pct')} %"
            f"{vol_note}\n"
            f"Marktkapitalisierung: {_human_cap(quote.get('market_cap'))}\n\n"
            f"Schlagzeilen der letzten Stunden:\n{news_block}"
        )

        try:
            response = await self._client.messages.create(
                model=self.cfg.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                output_config={
                    "effort": "low",
                    "format": {
                        "type": "json_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "explanation": {
                                    "type": "string",
                                    "description": "Ein Satz auf Deutsch, warum sich der Kurs bewegt.",
                                },
                                "driver": {
                                    "type": "string",
                                    "description": "Ausloeser in 2-4 Woertern, z.B. 'Quartalszahlen ueber Erwartung'.",
                                },
                                "confidence": {"type": "string", "enum": ["hoch", "mittel", "niedrig"]},
                                "sentiment": {"type": "string", "enum": ["positiv", "negativ", "neutral"]},
                                "worth_alert": {"type": "boolean"},
                            },
                            "required": ["explanation", "driver", "confidence", "sentiment", "worth_alert"],
                            "additionalProperties": False,
                        },
                    },
                },
            )
            text = next((b.text for b in response.content if b.type == "text"), None)
            if not text:
                return None
            data = json.loads(text)
            data["source"] = "claude"
            return data
        except Exception as exc:  # Netzwerk, Rate-Limit, Key ungueltig
            log.warning("Claude-Einordnung fehlgeschlagen (%s): %s", quote.get("symbol"), exc)
            return None


def _fallback(quote: dict[str, Any], headlines: list[dict[str, Any]]) -> dict[str, Any]:
    """Ohne KI: aktuellste Schlagzeile zeigen, Bewegung selbst einordnen."""
    change = quote.get("change_pct") or 0
    top = headlines[0]["title"] if headlines else None
    return {
        "explanation": top or "Kursbewegung ohne begleitende Meldung.",
        "driver": "aktuelle Schlagzeile" if top else "kein Ausloeser gefunden",
        "confidence": "niedrig",
        "sentiment": "positiv" if change > 0 else "negativ" if change < 0 else "neutral",
        "worth_alert": bool(headlines),
        "source": "headline",
    }


def _human_cap(cap: float | None) -> str:
    if not cap:
        return "unbekannt"
    for unit, size in (("Bio.", 1e12), ("Mrd.", 1e9), ("Mio.", 1e6)):
        if cap >= size:
            return f"{cap / size:.1f} {unit} USD"
    return f"{cap:.0f} USD"
