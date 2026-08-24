#!/usr/bin/env python3
"""FlightWall starten:  python run.py"""
from __future__ import annotations

import logging

import uvicorn

from backend.config import CONFIG


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)-28s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    uvicorn.run(
        "backend.app:app",
        host=CONFIG.server.host,
        port=CONFIG.server.port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
