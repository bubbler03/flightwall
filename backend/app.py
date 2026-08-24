"""FastAPI-Server: liefert das Display-Frontend und die Live-Daten."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .button import ButtonWatcher
from .config import CONFIG, ROOT
from .flights.adsb import AdsbClient
from .flights.enrich import Enricher
from .flights.service import FlightService
from .hub import Hub
from .market.service import MarketService
from .store import aircraft_model_catalog, recent_sightings

log = logging.getLogger(__name__)
FRONTEND = ROOT / "frontend"

hub = Hub(CONFIG.display.default_view, CONFIG.display.return_to_default_after)
enricher = Enricher()
flight_service = FlightService(CONFIG, hub, enricher, AdsbClient())
market_service = MarketService(CONFIG, hub)
button_watcher = ButtonWatcher(CONFIG.button, hub)


async def _view_timeout_loop() -> None:
    """Bringt das Display nach der Ruhezeit zurueck zur Flug-Ansicht."""
    while True:
        await asyncio.sleep(5)
        hub.maybe_return_to_default()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Standort: %s (%.4f, %.4f), Radius %s nm",
             CONFIG.location.label or "-", CONFIG.location.lat, CONFIG.location.lon,
             CONFIG.location.radius_nm)
    flight_service.start()
    market_service.start()
    button_watcher.start()
    timeout_task = asyncio.create_task(_view_timeout_loop(), name="view-timeout")
    try:
        yield
    finally:
        timeout_task.cancel()
        button_watcher.stop()
        await asyncio.gather(
            flight_service.stop(), market_service.stop(), enricher.aclose(),
            return_exceptions=True,
        )


app = FastAPI(title="FlightWall", lifespan=lifespan)


# --- Seite und Dateien ---------------------------------------------------
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


app.mount("/art", StaticFiles(directory=FRONTEND / "art"), name="art")
app.mount("/css", StaticFiles(directory=FRONTEND / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND / "js"), name="js")


# --- Daten ---------------------------------------------------------------
@app.get("/api/state")
async def state() -> dict:
    """Alles, was das Display fuer den Kaltstart braucht."""
    return {
        **hub.snapshot(),
        "config": {
            "location": CONFIG.location.label,
            "night_dim": {
                "enabled": CONFIG.display.night_dim.enabled,
                "start_hour": CONFIG.display.night_dim.start_hour,
                "end_hour": CONFIG.display.night_dim.end_hour,
                "opacity": CONFIG.display.night_dim.opacity,
            },
        },
    }


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    """Server-Sent Events: Flugzeug, Kurse, Meldungen, Ansichtswechsel."""
    queue = hub.subscribe()

    async def generator():
        try:
            yield f"data: {_json_snapshot()}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"   # haelt die Verbindung offen
        finally:
            hub.unsubscribe(queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


def _json_snapshot() -> str:
    import json
    return json.dumps({"event": "snapshot", "data": hub.snapshot()})


@app.get("/api/flight")
async def flight() -> dict:
    return {"flight": hub.state.get("flight")}


@app.get("/api/flight/history")
async def flight_history(limit: int = 20) -> dict:
    return {"sightings": recent_sightings(limit)}


@app.get("/api/flight/models")
async def flight_models(limit: int = 500) -> dict:
    """Gesehene Modell/Airline-Paare als Arbeitsliste fuer neue Poster."""
    models = aircraft_model_catalog(limit)
    return {
        "models": models,
        "total": len(models),
        "needs_artwork": sum(int(model["needs_artwork"]) for model in models),
    }


@app.get("/api/market")
async def market() -> dict:
    return hub.state.get("market") or {"movers": [], "watchlist": []}


@app.get("/api/market/explain/{symbol}")
async def explain(symbol: str) -> dict:
    """Einordnung zu einem Symbol - der Agent auf Zuruf."""
    return await market_service.explain(symbol.upper())


# --- Steuerung -----------------------------------------------------------
@app.post("/api/view/toggle")
async def toggle_view() -> dict:
    return {"view": hub.toggle_view(by_user=True)}


@app.post("/api/view/{view}")
async def set_view(view: str) -> dict:
    if view not in ("flight", "stocks"):
        raise HTTPException(status_code=400, detail="Ansicht muss 'flight' oder 'stocks' sein")
    return {"view": hub.set_view(view, by_user=True, reason="api")}


@app.post("/api/refresh")
async def refresh() -> dict:
    """Beide Quellen sofort neu abfragen (Debug/Test)."""
    flight, _ = await asyncio.gather(
        flight_service.tick(), market_service.tick(), return_exceptions=True
    )
    return {"ok": True}


@app.post("/api/art/refresh")
async def refresh_art() -> dict:
    """Nach dem Kopieren neuer Bilder aufrufen - kein Neustart noetig."""
    return flight_service.refresh_artwork()


@app.get("/api/status")
async def status() -> dict:
    return {
        "flights": flight_service.status(),
        "market": market_service.status(),
        "view": hub.view,
        "listeners": hub.listener_count,
    }
