#!/usr/bin/env bash
# Schaltet den angeschlossenen FlightWall-Monitor per DDC/CI aus.
set -euo pipefail

if ! command -v ddcutil >/dev/null 2>&1; then
    echo "FlightWall display-off: ddcutil fehlt" >&2
    exit 1
fi

# D6=05 ist laut MCCS der schreibgeschuetzte Befehl "Display ausschalten".
# --noverify ist erforderlich, weil ein ausgeschaltetes Display nicht mehr auf
# die anschliessende Ruecklesepruefung antwortet.
ddcutil setvcp D6 05 --display 1 --noverify

