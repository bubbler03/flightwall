# FlightWall

Ein Wanddisplay für den Raspberry Pi mit zwei Ansichten:

**Flug-Ansicht** (Ruhezustand) — zeigt die Flugzeuge, die gerade am nächsten über dir
fliegen: als Retro-Poster mit Airline, Route, Höhe, Entfernung und Richtung. Sind
mehrere gleichzeitig unterwegs, stapelt das Poster bis zu drei davon untereinander,
jeweils mit eigener Bildunterschrift.

**Aktien-Ansicht** — auffällige Kursbewegungen großer Firmen mit Mini-Charts. Ein
Agent sammelt dazu die Schlagzeilen und lässt Claude in einem Satz erklären, warum
sich der Kurs bewegt. Bei einer wirklich wichtigen Meldung schaltet das Display von
selbst um und kehrt danach zum Flugzeug zurück.

Umgeschaltet wird per Knopf am GPIO, per Leertaste oder per Fingertipp.

---

## Schnellstart

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config.example.yaml config.yaml     # Koordinaten eintragen!
.venv/bin/python tools/make_fallback_art.py
.venv/bin/python run.py
```

Dann [http://localhost:8000](http://localhost:8000) öffnen.

## Auf dem Raspberry Pi

```bash
bash deploy/install.sh
```

Das Skript legt die Python-Umgebung an, richtet den Systemd-Dienst ein und sorgt
dafür, dass Chromium beim Booten im Vollbild startet. Auf einem schlanken Debian
ohne Desktop installiert es dafür nur den kleinen Wayland-Kiosk Cage; vorhandene
Desktop-Installationen verwenden weiter ihren normalen Autostart. Eine verwaltete
Chromium-Policy verhindert Übersetzungs- und Werbeeinblendungen im Bilderrahmen.
Danach nur noch die Koordinaten in `config.yaml` eintragen und
`sudo systemctl restart flightwall`.

---

## Konfiguration

Alles steckt in `config.yaml`. Die wichtigsten Punkte:

| Einstellung | Bedeutung |
|---|---|
| `location.lat` / `lon` | **Dein Standort.** In Google Maps rechtsklicken → Koordinaten kopieren. |
| `location.radius_nm` | Suchradius in nautischen Meilen. 25 nm ≈ 46 km. |
| `flights.max_tracked` | Bis zu so viele der nächsten Flugzeuge zeigt das Poster gleichzeitig (Standard: 3). |
| `flights.max_radius_nm` | Bis hierhin erweitert FlightWall die Suche automatisch, wenn im normalen Radius weniger als drei Flugzeuge liegen. |
| `flights.radius_step_nm` | Schrittweite der automatischen Radius-Erweiterung. |
| `market.min_market_cap` | Ab welcher Firmengröße Bewegungen zählen (Standard: 10 Mrd. USD). |
| `market.alert_threshold_pct` | Ab welcher Tagesbewegung das Display selbsttätig umschaltet. |
| `agent.anthropic_api_key` | Optional. Ohne Key läuft alles weiter, nur ohne die KI-Erklärung. |
| `button.enabled` | Hardware-Knopf am GPIO ein-/ausschalten. |

Nach Änderungen: `sudo systemctl restart flightwall`

---

## Die Flugzeugbilder

Das Display sucht zu Typ **und Airline** (`B744` + Cathay Cargo, `A21N` +
Lufthansa, …) ein passendes Bild in `frontend/art/`. 22 transparente Retro-
Freisteller sind bereits unter `frontend/art/display/` eingebunden; für noch nicht
vorhandene Kombinationen bleibt bewusst die neutrale SVG-Silhouette sichtbar,
damit nie eine falsche Lackierung erscheint.

**Alle 30 Prompts stehen in [`tools/art_prompts.md`](tools/art_prompts.md).**

Ablauf für neue Motive:

1. `GET /api/flight/models` zeigt dauerhaft gespeicherte Modell/Airline-Paare;
   `needs_artwork: 1` ist die Arbeitsliste für die nächsten Bilder.
2. Bild als `<familie>--<airline>-01.png` in `frontend/art/` legen und eine Zeile
   mit Airline-Aliases in `frontend/art/manifest.tsv` ergänzen.
3. `curl -X POST localhost:8000/api/art/refresh` aufrufen. Die sichtbaren
   Flugzeuge werden ohne Neustart sofort neu zugeordnet.

Mehrere Bilder derselben Kombination (`-01`, `-02`, …) wechseln sich stabil pro
Registrierung ab.

Die roten 16:9-Master bleiben lokal und werden nicht ins öffentliche Repository
geschoben. Neue Masters lassen sich reproduzierbar freistellen:

```bash
.venv/bin/pip install -r tools/requirements-art.txt
.venv/bin/python tools/make_display_cutouts.py --all
```

Das Skript entfernt ausschließlich die vom Bildrand zusammenhängende rote Fläche,
schneidet transparente Ränder zu und bewahrt Lackierung, Logos und Retro-Raster.

---

## Der Knopf

Taster zwischen **GPIO 17** und **GND** klemmen — mehr braucht es nicht, der interne
Pull-up-Widerstand ist aktiv. Dann in `config.yaml`:

```yaml
button:
  enabled: true
  gpio_pin: 17
```

Auf dem Pi 5 zusätzlich `sudo apt install python3-lgpio` und
`.venv/bin/pip install gpiozero lgpio`.

Ohne Knopf: Leertaste, Mausklick oder Fingertipp auf dem Touchscreen.

---

## Woher die Daten kommen

| Quelle | Wofür | Kosten |
|---|---|---|
| [adsb.lol](https://api.adsb.lol) | Flugzeugpositionen (Primärquelle) | kostenlos, kein Schlüssel |
| [adsb.fi](https://opendata.adsb.fi) | Flugzeugpositionen (springt automatisch ein, falls adsb.lol nicht antwortet) | kostenlos, kein Schlüssel |
| [adsbdb.com](https://api.adsbdb.com) | Flugzeugtyp, Airline, Route | kostenlos, kein Schlüssel |
| [hexdb.io](https://hexdb.io) | Ersatzquelle für Flugzeugdaten | kostenlos |
| Yahoo Finance | Kurse, Tagesgewinner und -verlierer | kostenlos, kein Schlüssel |
| Google News / Yahoo Finance RSS | Schlagzeilen zu Kursbewegungen | kostenlos |
| Claude API | Einordnung der Bewegung | optional, nach Verbrauch |

**Warum kein X/Twitter?** Die X-API kostet seit 2023 mindestens rund 100 $ im Monat,
und StockTwits blockt anonyme Zugriffe. Google News deckt dasselbe ab: Meldungen von
Reuters, Bloomberg und CNBC stehen dort binnen Minuten. Ein X-Client lässt sich in
`backend/market/news.py` nachrüsten, wenn du später ein Abo hast — die Stelle ist
dort vermerkt.

**Eigener ADS-B-Empfänger:** Mit einem RTL-SDR-Stick (~30 €) und dump1090 empfängst
du selbst statt über die API. In `backend/flights/adsb.py` die `base_url` auf
`http://localhost:8080/data/aircraft.json` setzen — das Format ist identisch.

---

## Bedienung im Browser

| Taste / Geste | Wirkung |
|---|---|
| Leertaste, Enter, ←/→ | zwischen den Ansichten wechseln |
| Klick / Tipp | dasselbe |
| `r` | Seite neu laden |

## Schnittstellen

| Pfad | Zweck |
|---|---|
| `GET /api/state` | kompletter Zustand |
| `GET /api/stream` | Live-Ereignisse (SSE) |
| `GET /api/status` | Diagnose: Fehler, Bildabdeckung, Statistik |
| `POST /api/view/toggle` | Ansicht umschalten |
| `POST /api/refresh` | beide Quellen sofort neu abfragen |
| `POST /api/art/refresh` | Bildordner neu einlesen |
| `GET /api/market/explain/{symbol}` | Einordnung zu einem Kürzel |
| `GET /api/flight/history` | zuletzt gesehene Flugzeuge |
| `GET /api/flight/models` | gespeicherte Modell/Airline-Paare und fehlende Poster |

---

## Wenn etwas klemmt

**Weniger als drei Flugzeuge zu sehen** — FlightWall erweitert den Radius bis
`flights.max_radius_nm` automatisch. `curl localhost:8000/api/status` zeigt
`candidate_count`, `query_radius_nm` und `radius_exhausted`. Sind selbst am
Maximalradius keine drei ADS-B-Kandidaten vorhanden, werden nur kurz ausgefallene
Flugzeuge bis zu `linger_seconds` überbrückt; es werden keine erfunden.

**Keine Kursdaten, keine Flugzeuge** — Yahoo *und* adsb.lol weisen
Standard-Python-Clients anhand ihres TLS-Fingerabdrucks ab (Antwort 429, danach
hängende Verbindungen). Deshalb läuft aller Verkehr über `curl_cffi`, das sich als
Chrome ausgibt. Fehlt das Paket, versiegen beide Quellen:
`.venv/bin/pip install curl_cffi`.

Antworten beide Flugquellen nicht, fragt das Display von selbst immer seltener
nach — bis zu einmal alle fünf Minuten — und kehrt zum normalen Takt zurück, sobald
wieder Daten kommen. Ein *leerer* Himmel bremst den Takt nicht.

**Display bleibt schwarz** — `journalctl -u flightwall -f` zeigt den Dienst,
`systemctl status flightwall` den Zustand. Auf einer Headless-Installation zeigt
`systemctl status flightwall-kiosk@tty7` zusätzlich den HDMI-Kiosk. Dieser wartet,
bis der Webdienst antwortet.

**Bilder erscheinen nicht** — Dateiname und passende Zeile in
`frontend/art/manifest.tsv` prüfen. Danach `/api/art/refresh` aufrufen.

---

## Aufbau

```
backend/
  app.py            FastAPI-Server, Schnittstellen, SSE
  hub.py            Ansichtszustand und Ereignisverteilung
  http.py           gemeinsamer HTTP-Client (umgeht die Yahoo-Sperre)
  store.py          SQLite: Cache, Sichtungen, Modell/Airline-Katalog, Meldungen
  button.py         Hardware-Knopf am GPIO
  flights/
    adsb.py         Positionen von adsb.lol
    enrich.py       Typ, Airline und Route nachschlagen
    artwork.py      Typcode + Airline → Poster/Fallback
    service.py      sucht laufend die drei nächsten Flugzeuge
    geo.py          Entfernung, Peilung, Höhenwinkel
  market/
    yahoo.py        Kurse und Tagesbewegungen
    news.py         Schlagzeilen aus RSS-Feeds
    agent.py        Claude ordnet die Bewegung ein
    service.py      beobachtet den Markt, löst Meldungen aus
frontend/
  index.html, css/, js/, art/
tools/
  art_prompts.md        die 30 Bild-Prompts
  make_fallback_art.py  erzeugt die Platzhalter-Silhouetten
deploy/
  install.sh, flightwall.service, flightwall-kiosk@.service, kiosk.sh
```
