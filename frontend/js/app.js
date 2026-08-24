/* =========================================================================
   FlightWall - Anzeigelogik
   Holt den Anfangszustand per /api/state und bleibt danach ueber
   Server-Sent-Events auf dem Laufenden.
   ========================================================================= */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { view: "flight", flight: null, fleet: [], market: null, alert: null, nightDim: null };

  /* ----------------------------- Hilfsmittel ---------------------------- */
  const nf = (value, digits = 0) =>
    value === null || value === undefined || Number.isNaN(value)
      ? "—"
      : Number(value).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits });

  const feetToMeters = (ft) => (ft == null ? null : ft * 0.3048);
  const knotsToKmh = (kt) => (kt == null ? null : kt * 1.852);

  function toast(message, ms = 3200) {
    const el = $("toast");
    el.textContent = message;
    el.hidden = false;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toast._t);
    toast._t = setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => (el.hidden = true), 320);
    }, ms);
  }

  /* --------------------------- Flug-Ansicht ----------------------------- */
  /* Das Display wird von der Flotte gesteuert: den bis zu drei naechsten
     Flugzeugen. Bei einem einzelnen laeuft alles ueber renderFlight wie
     bisher, ab zwei zeigt der Stapel alle untereinander. */
  function renderFleet(fleet, changed) {
    const list = (Array.isArray(fleet) ? fleet : []).filter((f) => f && f.hex);
    state.fleet = list;
    const multi = list.length >= 2;
    $("flight-view").classList.toggle("multi", multi);

    if (!multi) {
      $("stage-caption").textContent = "Fig. 01 — Himmel über dir";
      renderFlight(list[0] || null, changed);
      return;
    }

    $("stage-caption").textContent = "";
    updateBands(list);
  }

  function updateBands(list) {
    const stack = $("fleet-stack");
    const seen = new Set();
    list.forEach((f, i) => {
      seen.add(f.hex);
      let band = stack.querySelector(`.band[data-hex="${f.hex}"]`);
      if (!band) {
        band = document.createElement("figure");
        band.className = "band";
        band.dataset.hex = f.hex;
        band.innerHTML = `
          <div class="band-visual">
            <img class="band-art" alt="" hidden>
            <span class="band-fallback" hidden></span>
          </div>
          <figcaption class="band-caption">
            <div class="band-heading">
              <span class="band-index"></span>
              <div class="band-identity">
                <span class="band-title"></span>
                <span class="band-model"></span>
              </div>
            </div>
            <div class="band-route" aria-label="Flugroute">
              <div class="route-stop">
                <span class="route-label">Herkunft</span>
                <strong class="route-code route-origin"></strong>
                <span class="route-place route-origin-place"></span>
              </div>
              <span class="band-route-line" aria-hidden="true"><i></i><b>→</b><i></i></span>
              <div class="route-stop route-stop-destination">
                <span class="route-label">Ziel</span>
                <strong class="route-code route-destination"></strong>
                <span class="route-place route-destination-place"></span>
              </div>
            </div>
            <dl class="band-specs">
              <div><dt>Höhe</dt><dd class="band-altitude"></dd></div>
              <div><dt>Entfernung</dt><dd class="band-distance"></dd></div>
              <div><dt>Richtung</dt><dd class="band-direction"></dd></div>
            </dl>
          </figcaption>`;
        stack.appendChild(band);
      }
      band.style.order = i;                    // Reihenfolge = Naehe
      fillBand(band, f, i);
    });
    stack.querySelectorAll(".band").forEach((b) => { if (!seen.has(b.dataset.hex)) b.remove(); });
  }

  function fillBand(band, f, index) {
    const origin = f.origin || {};
    const destination = f.destination || {};
    const originCode = origin.iata || origin.icao || "—";
    const destinationCode = destination.iata || destination.icao || "—";
    const originPlace = origin.city || origin.municipality || origin.name || "Nicht verfügbar";
    const destinationPlace = destination.city || destination.municipality || destination.name || "Nicht verfügbar";
    const meters = feetToMeters(f.altitude_ft);

    band.querySelector(".band-index").textContent = String(index + 1).padStart(2, "0");
    band.querySelector(".band-title").textContent = f.display_operator || "Unbekannter Betreiber";
    band.querySelector(".band-model").textContent = [
      f.display_title || f.art_label || f.type_code || "Flugzeug",
      f.registration || f.callsign,
    ].filter(Boolean).join("  ·  ");
    band.querySelector(".route-origin").textContent = originCode;
    band.querySelector(".route-destination").textContent = destinationCode;
    band.querySelector(".route-origin-place").textContent = originPlace;
    band.querySelector(".route-destination-place").textContent = destinationPlace;
    band.querySelector(".band-altitude").textContent = meters ? `${nf(meters)} m` : "—";
    band.querySelector(".band-distance").textContent = f.distance_km != null ? `${nf(f.distance_km, 1)} km` : "—";
    band.querySelector(".band-direction").textContent = f.compass
      ? `${f.compass} · ${nf(f.bearing_deg, 0)}°`
      : "—";

    const img = band.querySelector(".band-art");
    const fallback = band.querySelector(".band-fallback");
    band.classList.toggle("is-fallback", !f.art_file || f.art_file.startsWith("fallback-"));
    if (f.art_url) {
      if (img.getAttribute("src") !== f.art_url) img.src = f.art_url;
      img.hidden = false;
      fallback.hidden = true;
    } else {
      img.hidden = true;
      fallback.hidden = false;
      fallback.textContent = f.type_code || "✈";
    }
  }

  function renderFlight(flight, changed) {
    if (!flight) {
      $("aircraft-title").textContent = "Kein Flugzeug in Reichweite";
      $("operator").textContent = "Der Himmel ist gerade leer";
      $("registration").textContent = "";
      $("origin").textContent = "—";
      $("destination").textContent = "—";
      ["altitude", "distance", "bearing", "speed", "state"].forEach((k) => ($(`spec-${k}`).textContent = "—"));
      showArtwork(null, "✈", "");
      return;
    }

    $("aircraft-title").textContent = flight.display_title || flight.art_label || "Flugzeug";
    $("operator").textContent = flight.display_operator || "";
    $("registration").textContent = [flight.registration || flight.callsign, flight.type_code]
      .filter(Boolean).join("  ·  ");

    const origin = flight.origin?.iata || flight.origin?.icao;
    const destination = flight.destination?.iata || flight.destination?.icao;
    $("origin").textContent = origin || "—";
    $("destination").textContent = destination || "—";
    $("route").title = [flight.origin?.city, flight.destination?.city].filter(Boolean).join(" → ");

    const meters = feetToMeters(flight.altitude_ft);
    $("spec-altitude").textContent = meters ? `${nf(meters)} m` : "—";
    $("spec-distance").textContent = flight.distance_km != null ? `${nf(flight.distance_km, 1)} km` : "—";
    $("spec-bearing").textContent = flight.compass
      ? `${flight.compass} ${nf(flight.elevation_deg, 0)}°`
      : "—";
    const kmh = knotsToKmh(flight.ground_speed_kt);
    $("spec-speed").textContent = kmh ? `${nf(kmh)} km/h` : "—";
    $("spec-state").textContent = flight.climb_state || "—";

    showArtwork(flight.art_url, flight.type_code || "✈", flight.art_label || "", changed);
  }

  function showArtwork(url, fallbackLabel, note, animate = true) {
    const img = $("artwork");
    const placeholder = $("artwork-placeholder");

    if (!url) {
      img.hidden = true;
      img.removeAttribute("src");
      placeholder.hidden = false;
      $("placeholder-type").textContent = fallbackLabel;
      $("placeholder-note").textContent = note ? `${note} · noch kein Bild hinterlegt` : "noch kein Bild hinterlegt";
      return;
    }

    if (img.getAttribute("src") === url) return;

    const swap = () => {
      img.src = url;
      img.hidden = false;
      placeholder.hidden = true;
      img.classList.remove("swap");
    };

    if (animate && !img.hidden) {
      img.classList.add("swap");
      setTimeout(swap, 420);
    } else {
      swap();
    }
  }

  /* -------------------------- Aktien-Ansicht ---------------------------- */
  function renderMarket(market) {
    if (!market) return;

    const stateEl = $("market-state");
    const open = market.market_state === "REGULAR";
    stateEl.textContent = { REGULAR: "Börse offen", CLOSED: "Börse zu", PRE: "vorbörslich", POST: "nachbörslich" }[market.market_state] || market.market_state || "—";
    stateEl.classList.toggle("open", open);

    if (market.updated_at) {
      const d = new Date(market.updated_at * 1000);
      $("market-updated").textContent = `Stand ${d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}`;
    }

    const list = $("movers-list");
    const movers = market.movers || [];
    if (!movers.length) {
      list.innerHTML = '<li class="empty">Gerade keine auffälligen Bewegungen</li>';
    } else {
      list.innerHTML = movers.map(moverRow).join("");
    }

    $("watchlist").innerHTML = (market.watchlist || [])
      .slice(0, 10)
      .map((q) => {
        const dir = (q.change_pct || 0) >= 0 ? "up" : "down";
        return `<li><span class="w-sym">${esc(q.symbol)}</span><span class="${dir}">${signed(q.change_pct)}</span></li>`;
      })
      .join("");
  }

  function moverRow(quote) {
    const dir = (quote.change_pct || 0) >= 0 ? "up" : "down";
    return `<li>
      <span class="sym">${esc(quote.symbol || "")}</span>
      <span class="company">${esc(quote.name || "")}</span>
      ${sparkline(quote.spark, dir)}
      <span class="change ${dir}">${signed(quote.change_pct)}</span>
    </li>`;
  }

  function sparkline(points, dir) {
    if (!points || points.length < 3) return "<span></span>";
    const min = Math.min(...points);
    const max = Math.max(...points);
    const span = max - min || 1;
    const path = points
      .map((p, i) => `${(i / (points.length - 1)) * 100},${20 - ((p - min) / span) * 20}`)
      .join(" L ");
    const color = dir === "up" ? "var(--up)" : "var(--down)";
    return `<svg class="spark" viewBox="0 0 100 20" preserveAspectRatio="none"><path d="M ${path}" stroke="${color}"/></svg>`;
  }

  function renderAlert(alert) {
    const panel = $("alert-panel");
    if (!alert) {
      panel.hidden = true;
      return;
    }
    const negative = (alert.change_pct || 0) < 0;
    panel.hidden = false;
    panel.classList.toggle("negative", negative);
    $("alert-mark").textContent = negative ? "▼" : "▲";
    $("alert-symbol").textContent = alert.symbol || "";
    $("alert-change").textContent = signed(alert.change_pct);
    $("alert-name").textContent = alert.name || "";
    $("alert-explanation").textContent = alert.explanation || "";
    $("alert-driver").textContent = alert.driver || "";
    $("alert-confidence").textContent = alert.confidence ? `Sicherheit: ${alert.confidence}` : "";
    $("alert-source").textContent = alert.source === "claude" ? "Einordnung: Claude" : "Quelle: Schlagzeile";
  }

  const signed = (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${nf(v, 2)} %`);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ----------------------------- Ansichten ------------------------------ */
  function setView(view) {
    state.view = view;
    document.body.classList.toggle("view-flight", view === "flight");
    document.body.classList.toggle("view-stocks", view === "stocks");
  }

  async function toggleView() {
    try {
      const res = await fetch("/api/view/toggle", { method: "POST" });
      const data = await res.json();
      setView(data.view);
    } catch {
      setView(state.view === "flight" ? "stocks" : "flight");   // notfalls lokal
    }
  }

  /* ------------------------------ Uhr / Nacht --------------------------- */
  function tickClock() {
    $("clock").textContent = new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
    applyNightDim();
  }

  function applyNightDim() {
    const cfg = state.nightDim;
    if (!cfg || !cfg.enabled) return;
    const hour = new Date().getHours();
    const night = cfg.start_hour > cfg.end_hour
      ? hour >= cfg.start_hour || hour < cfg.end_hour     // z.B. 22 bis 7
      : hour >= cfg.start_hour && hour < cfg.end_hour;
    $("night-veil").style.opacity = night ? String(1 - (cfg.opacity ?? 0.55)) : "0";
  }

  /* ------------------------- Datenanbindung ----------------------------- */
  function apply(event, data) {
    switch (event) {
      case "snapshot":
        setView(data.view);
        state.flight = data.flight;
        state.market = data.market;
        renderFleet(data.fleet || (data.flight ? [data.flight] : []), false);
        renderMarket(data.market);
        renderAlert(data.alert);
        break;
      case "fleet":
        renderFleet(data.fleet, data.changed);
        break;
      case "market":
        state.market = data;
        renderMarket(data);
        break;
      case "alert":
        state.alert = data;
        renderAlert(data);
        toast(`${data.symbol} ${signed(data.change_pct)} — ${data.driver || "Marktmeldung"}`, 8000);
        break;
      case "view":
        setView(data.view);
        break;
    }
  }

  let source = null;
  let retry = 0;

  function connect() {
    source?.close();
    source = new EventSource("/api/stream");

    source.onopen = () => {
      retry = 0;
      $("connection").hidden = true;
    };

    source.onmessage = (msg) => {
      try {
        const { event, data } = JSON.parse(msg.data);
        apply(event, data);
      } catch (err) {
        console.warn("Ereignis nicht lesbar", err);
      }
    };

    source.onerror = () => {
      $("connection").hidden = false;
      source.close();
      retry = Math.min(retry + 1, 6);
      setTimeout(connect, 1000 * 2 ** retry);      // 2s, 4s, 8s ... max ~64s
    };
  }

  async function bootstrap() {
    try {
      const res = await fetch("/api/state");
      const data = await res.json();
      state.nightDim = data.config?.night_dim;
      $("place").textContent = data.config?.location || "";
      apply("snapshot", data);
    } catch (err) {
      console.warn("Anfangszustand nicht erreichbar", err);
    }
    connect();
  }

  /* ------------------------------ Bedienung ----------------------------- */
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" || e.code === "Enter" || e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      toggleView();
    }
    if (e.key === "r") location.reload();
  });
  document.addEventListener("click", toggleView);
  document.addEventListener("touchend", (e) => { e.preventDefault(); toggleView(); }, { passive: false });

  tickClock();
  setInterval(tickClock, 15000);
  bootstrap();
})();
