#!/usr/bin/env bash
# Einrichtung auf dem Raspberry Pi.
#   bash deploy/install.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_NAME="$(whoami)"

echo "==> FlightWall wird eingerichtet in $PROJECT_DIR (Benutzer: $USER_NAME)"

# --- Systempakete --------------------------------------------------------
echo "==> Systempakete"
sudo apt update
sudo apt install -y python3-venv python3-dev curl ddcutil
if apt-cache show chromium >/dev/null 2>&1; then
    sudo apt install -y chromium
else
    sudo apt install -y chromium-browser
fi
# Kiosk-Browser ohne Uebersetzungs-/Werbe-Popups. Distributionen ignorieren
# einzelne Chromium-Flags teilweise; die verwaltete Linux-Policy ist stabiler.
sudo install -d -m 755 /etc/chromium/policies/managed
sudo install -m 644 deploy/chromium-policy.json \
    /etc/chromium/policies/managed/flightwall.json
# lgpio wird fuer den Hardware-Knopf am Pi 5 gebraucht
sudo apt install -y python3-lgpio || echo "   (python3-lgpio nicht verfuegbar - nur noetig fuer den Knopf)"

# Der HDMI-DDC-Bus wird fuer das echte Ausschalten des Monitors gebraucht.
echo i2c-dev | sudo tee /etc/modules-load.d/flightwall-ddc.conf >/dev/null
sudo modprobe i2c-dev

# --- Python-Umgebung -----------------------------------------------------
echo "==> Python-Umgebung"
cd "$PROJECT_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# --- Konfiguration -------------------------------------------------------
if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "==> config.yaml angelegt - TRAG DEINE KOORDINATEN EIN!"
fi

# --- Platzhalterbilder ---------------------------------------------------
.venv/bin/python tools/make_fallback_art.py

# --- Dienst --------------------------------------------------------------
echo "==> Systemd-Dienst"
sudo sed -e "s|/home/pi/flightwall|$PROJECT_DIR|g" \
         -e "s|^User=pi|User=$USER_NAME|" \
         -e "s|^Group=pi|Group=$USER_NAME|" \
         deploy/flightwall.service | sudo tee /etc/systemd/system/flightwall.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now flightwall

# --- Kiosk-Autostart -----------------------------------------------------
echo "==> Kiosk-Autostart"
if systemctl status display-manager.service >/dev/null 2>&1; then
    # Bestehende Desktop-Installation: Chromium in deren Sitzung starten.
    DESKTOP_FILE="$HOME/.config/autostart/flightwall-kiosk.desktop"
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=FlightWall Kiosk
Exec=$PROJECT_DIR/deploy/kiosk.sh
X-GNOME-Autostart-enabled=true
DESKTOP

    # labwc (Pi OS Bookworm) nutzt eine eigene Autostart-Datei
    LABWC="$HOME/.config/labwc/autostart"
    if [ -d "$HOME/.config/labwc" ] && ! grep -q flightwall "$LABWC" 2>/dev/null; then
        echo "$PROJECT_DIR/deploy/kiosk.sh &" >> "$LABWC"
    fi
    # wayfire (aeltere Bookworm-Images)
    WAYFIRE="$HOME/.config/wayfire.ini"
    if [ -f "$WAYFIRE" ] && ! grep -q flightwall "$WAYFIRE"; then
        printf '\n[autostart]\nflightwall = %s/deploy/kiosk.sh\n' "$PROJECT_DIR" >> "$WAYFIRE"
    fi
else
    # Schlankes/headless Debian: nur den Wayland-Kiosk installieren, keine
    # vollstaendige Desktop-Umgebung. Cage belegt exklusiv tty7 und HDMI.
    sudo apt install -y cage
    sudo tee /etc/pam.d/flightwall-kiosk >/dev/null <<'PAM'
auth       sufficient pam_permit.so
account    sufficient pam_permit.so
session    required   pam_unix.so
session    required   pam_systemd.so
PAM
    sudo sed -e "s|/home/pi/flightwall|$PROJECT_DIR|g" \
             -e "s|^User=pi|User=$USER_NAME|" \
             -e "s|^Group=pi|Group=$USER_NAME|" \
             deploy/flightwall-kiosk@.service | \
        sudo tee /etc/systemd/system/flightwall-kiosk@.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl set-default graphical.target
    sudo systemctl enable --now flightwall-kiosk@tty7.service
fi

# --- Display-Zeitplan ----------------------------------------------------
echo "==> Display-Zeitplan (taeglich 22:30)"
sudo sed -e "s|/home/pi/flightwall|$PROJECT_DIR|g" \
         deploy/flightwall-display-off.service | \
    sudo tee /etc/systemd/system/flightwall-display-off.service >/dev/null
sudo install -m 644 deploy/flightwall-display-off.timer \
    /etc/systemd/system/flightwall-display-off.timer
sudo systemctl daemon-reload
sudo systemctl enable --now flightwall-display-off.timer

echo
echo "==> Fertig."
echo "    Status ansehen:   systemctl status flightwall"
echo "    Log mitlesen:     journalctl -u flightwall -f"
echo "    Im Browser:       http://$(hostname -I | awk '{print $1}'):8000"
echo
echo "    NICHT VERGESSEN: Koordinaten in config.yaml eintragen, dann"
echo "                     sudo systemctl restart flightwall"
