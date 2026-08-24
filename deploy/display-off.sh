#!/usr/bin/env bash
# Schaltet den angeschlossenen FlightWall-Monitor per DDC/CI aus.
set -euo pipefail

if ! command -v ddcutil >/dev/null 2>&1; then
    echo "FlightWall display-off: ddcutil fehlt" >&2
    exit 1
fi

# D6=05 ist laut MCCS der Befehl "Display ausschalten". Fuer den systemd-Lauf
# deaktivieren wir nur den nutzerspezifischen Cache; das LG-Display bestaetigt
# den gesetzten Zustand weiterhin ueber DDC.
export HOME="${HOME:-/root}"
ddcutil --noconfig --disable-dynamic-sleep --syslog=NEVER \
    setvcp D6 05 --display 1
