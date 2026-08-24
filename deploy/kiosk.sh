#!/usr/bin/env bash
# Startet Chromium im Vollbild auf dem FlightWall-Display.
# Wird vom Autostart der grafischen Sitzung aufgerufen (siehe install.sh).
set -u

URL="${FLIGHTWALL_URL:-http://localhost:8000}"

# Warten, bis der Dienst antwortet (nach dem Booten dauert das ein paar Sekunden)
for _ in $(seq 1 60); do
    if curl -sf -m 2 "$URL/api/status" >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Bildschirmschoner und Energiesparen aus
if command -v wlr-randr >/dev/null 2>&1; then
    :   # Wayland: uebernimmt der Compositor
elif [ -z "${WAYLAND_DISPLAY:-}" ] && command -v xset >/dev/null 2>&1; then
    xset s off
    xset -dpms
    xset s noblank
fi

# Reste eines harten Ausschaltens entfernen, sonst kommt der
# "Wiederherstellen"-Balken hoch
PROFILE="$HOME/.config/chromium/Default/Preferences"
if [ -f "$PROFILE" ]; then
    sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/; s/"exited_cleanly":false/"exited_cleanly":true/' "$PROFILE" 2>/dev/null || true
fi

BROWSER=$(command -v chromium-browser || command -v chromium || echo chromium)

exec "$BROWSER" \
    --kiosk \
    --no-first-run \
    --start-maximized \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=Translate,TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    --hide-crash-restore-bubble \
    --ozone-platform-hint=auto \
    "$URL"
