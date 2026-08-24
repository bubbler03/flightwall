# Bild-Prompts für die Flugzeug-Motive

30 Motive für die gängigsten Typen über Deutschland, plus 7 Notfall-Motive.
Alles im selben Retro-Poster-Stil, damit der Wechsel an der Wand ruhig wirkt.

## So gehst du vor

1. **In einem einzigen ChatGPT-Chat bleiben.** Der Stil bleibt nur dann über alle
   30 Bilder gleich. Beim zweiten Bild reicht: *"gleicher Stil, jetzt einen Airbus A321"*.
2. **Querformat wählen** (1536×1024 oder 1792×1024). Das Display zeigt die Fläche quer.
3. **Datei speichern als** `<name>-01.png` — die Namen stehen unten in der Tabelle.
   Mehrere Motive pro Typ? Dann `-02`, `-03` … Das Display wechselt dann automatisch durch.
4. **Dateien ablegen** in `frontend/art/` und danach einmal:

   ```bash
   curl -X POST localhost:8000/api/art/refresh
   ```

   Kein Neustart nötig. Die Antwort sagt dir, welche Typen noch fehlen.

> **Wichtig:** keine Airline-Bemalung und keine Schrift im Bild. Ein Motiv wird für
> alle Airlines dieses Typs verwendet — eine Lufthansa-Lackierung unter einem
> Ryanair-Flug sähe falsch aus. Betreiber und Kennung setzt das Display selbst darüber.

> **Hintergrundfarbe:** `#B8402C` ist die Terracotta-Fläche des Displays. Bleibt sie
> im Bild gleich, verschmilzt das Motiv nahtlos mit der Fläche. Willst du je Typ eine
> andere Farbe, ändere `--accent` in `frontend/css/style.css` oder lass die Fläche im
> Bild einfach mitfärben — beides sieht gut aus.

---

## Der Stil-Block

Dieser Text bleibt bei allen 30 Bildern **identisch**, nur die erste Zeile ändert sich:

```text
Flat mid-century screen-print illustration of <HIER DAS FLUGZEUG EINSETZEN>.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

---

## Die 30 Motive

| # | Dateiname | Flugzeug | Wofür es einspringt |
|---|-----------|----------|---------------------|
| 1 | `a319-01.png` | Airbus A319 | A318, A319, A19N |
| 2 | `a320-01.png` | Airbus A320 | A320, A20N |
| 3 | `a321-01.png` | Airbus A321 | A321, A21N |
| 4 | `a220-01.png` | Airbus A220 | BCS1, BCS3, A220 |
| 5 | `b737c-01.png` | Boeing 737 Classic | B731, B732, B733, B734, B735 |
| 6 | `b738-01.png` | Boeing 737NG | B736, B737, B738, B739, B73H |
| 7 | `b38m-01.png` | Boeing 737 MAX | B37M, B38M, B39M, B3XM |
| 8 | `b757-01.png` | Boeing 757 | B752, B753, B757 |
| 9 | `e190-01.png` | Embraer E-Jet E2 | E190, E195, E290, E295, E90, E95 |
| 10 | `e175-01.png` | Embraer E175 | E170, E175, E75L, E75S, E70 |
| 11 | `crj-01.png` | Bombardier CRJ | CRJ1, CRJ2, CRJ7, CRJ9, CRJX, CRJ |
| 12 | `a330-01.png` | Airbus A330 | A332, A333, A338, A339, A330, A33X |
| 13 | `a340-01.png` | Airbus A340 | A342, A343, A345, A346, A340 |
| 14 | `a350-01.png` | Airbus A350 | A359, A35K, A350 |
| 15 | `a380-01.png` | Airbus A380 | A388, A380 |
| 16 | `b767-01.png` | Boeing 767 | B762, B763, B764, B767 |
| 17 | `b777-01.png` | Boeing 777 | B772, B773, B77L, B77W, B778, B779 … |
| 18 | `b787-01.png` | Boeing 787 | B788, B789, B78X, B787 |
| 19 | `b747-01.png` | Boeing 747 | B741, B742, B743, B744, B748, B74F … |
| 20 | `md11-01.png` | McDonnell Douglas MD-11 | MD11, MD1F, DC10, MD82, MD83, MD88 |
| 21 | `at72-01.png` | ATR 72 | AT43, AT44, AT45, AT46, AT72, AT73 … |
| 22 | `dh8d-01.png` | De Havilland Dash 8 | DH8A, DH8B, DH8C, DH8D, DHC8 |
| 23 | `b350-01.png` | Beechcraft King Air | BE20, B350, BE9L, BE10, C441 |
| 24 | `c208-01.png` | Cessna Caravan | C208, C20T, PC12, TBM7, TBM8, TBM9 … |
| 25 | `cl35-01.png` | Bombardier Challenger | CL30, CL35, CL60, CL64, GLEX, GL5T … |
| 26 | `c56x-01.png` | Cessna Citation | C25A, C25B, C25C, C500, C510, C525 … |
| 27 | `e55p-01.png` | Embraer Phenom / PC-24 | E50P, E55P, PC24, HDJT, LJ35, LJ45 … |
| 28 | `c172-01.png` | Kleinflugzeug | C152, C162, C172, C177, C182, C206 … |
| 29 | `heli-01.png` | Hubschrauber | EC20, EC25, EC30, EC35, EC45, EC55 … |
| 30 | `mil-01.png` | Militaer | A400, C130, C30J, C17, K35R, KC30 … |

## Notfall-Motive (7 Stück)

Springen ein, wenn ein Typ auftaucht, für den es kein eigenes Bild gibt.
Als SVG-Platzhalter sind sie schon da — ersetze sie, wenn du magst:

| Dateiname | Wofür |
|-----------|-------|
| `fallback-bizjet-01.png` | bizjet |
| `fallback-ga-01.png` | ga |
| `fallback-heli-01.png` | heli |
| `fallback-narrowbody-01.png` | narrowbody, regional, military |
| `fallback-turboprop-01.png` | turboprop |
| `fallback-unknown-01.png` | unknown |
| `fallback-widebody-01.png` | widebody |

---

## Alle Prompts zum Kopieren

### 1. Airbus A319 → `a319-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A319: short narrow-body twinjet, two underwing engines, upward-curved sharklet wingtips, rounded nose, tall fin with curved leading edge.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 2. Airbus A320 → `a320-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A320: medium-length narrow-body twinjet, two underwing engines, upward-curved sharklet wingtips, rounded nose, tall fin with curved leading edge.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 3. Airbus A321 → `a321-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A321: stretched narrow-body twinjet, noticeably long slim fuselage, two underwing engines, sharklet wingtips.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 4. Airbus A220 → `a220-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A220: slender narrow-body twinjet with a pointed nose and oversized underwing engines, small swept fin.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 5. Boeing 737 Classic → `b737c-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 737 Classic: narrow-body twinjet with flattened oval engine nacelles mounted close under the wings, plain wingtips without winglets, pointed nose.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 6. Boeing 737NG → `b738-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 737-800: narrow-body twinjet with tall blended winglets, oval engine nacelles hugging the wing, pointed nose, straight fin.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 7. Boeing 737 MAX → `b38m-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 737 MAX: narrow-body twinjet with split-tip winglets pointing up and down, large engine nacelles with scalloped rear edges.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 8. Boeing 757 → `b757-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 757: long slim narrow-body twinjet on tall landing gear, pointed nose, large swept fin.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 9. Embraer E-Jet E2 → `e190-01.png`

```text
Flat mid-century screen-print illustration of an Embraer E195: regional jet with two underwing engines, slim fuselage, swept wings with small winglets, T-shaped tail area.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 10. Embraer E175 → `e175-01.png`

```text
Flat mid-century screen-print illustration of an Embraer E175: compact regional jet, two underwing engines, distinctive upward-and-downward wingtip fences.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 11. Bombardier CRJ → `crj-01.png`

```text
Flat mid-century screen-print illustration of a Bombardier CRJ900: slim regional jet with two engines mounted on the rear fuselage and a T-tail.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 12. Airbus A330 → `a330-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A330: wide-body twinjet, two large underwing engines, long fuselage, winglets, tall fin.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 13. Airbus A340 → `a340-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A340: wide-body with four underwing engines and a long slim fuselage.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 14. Airbus A350 → `a350-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A350: modern wide-body twinjet with curved upswept wingtips and a dark curved cockpit window mask.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 15. Airbus A380 → `a380-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A380: enormous double-deck wide-body with four underwing engines, two full rows of windows, very tall fin.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 16. Boeing 767 → `b767-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 767: wide-body twinjet, two underwing engines, medium-length fuselage, pointed nose, winglets.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 17. Boeing 777 → `b777-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 777-300ER: very long wide-body twinjet with two huge engines, raked wingtips, long main landing gear.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 18. Boeing 787 → `b787-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 787 Dreamliner: wide-body twinjet with gracefully raked wingtips, engine nacelles with scalloped rear edges, smooth nose.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 19. Boeing 747 → `b747-01.png`

```text
Flat mid-century screen-print illustration of a Boeing 747: iconic wide-body with an upper-deck hump behind the cockpit and four underwing engines.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 20. McDonnell Douglas MD-11 → `md11-01.png`

```text
Flat mid-century screen-print illustration of an McDonnell Douglas MD-11: tri-jet with one engine mounted in the tail fin base and two underwing engines, long fuselage.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 21. ATR 72 → `at72-01.png`

```text
Flat mid-century screen-print illustration of an ATR 72: high-wing turboprop with two large four-blade propellers, T-tail, boxy fuselage with a tall stance.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 22. De Havilland Dash 8 → `dh8d-01.png`

```text
Flat mid-century screen-print illustration of a De Havilland Dash 8 Q400: high-wing turboprop with two six-blade propellers, T-tail, long landing gear pods under the engines.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 23. Beechcraft King Air → `b350-01.png`

```text
Flat mid-century screen-print illustration of a Beechcraft King Air 350: small low-wing twin turboprop with winglets and a T-tail.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 24. Cessna Caravan → `c208-01.png`

```text
Flat mid-century screen-print illustration of a Cessna Caravan: single-engine high-wing turboprop with fixed landing gear and a cargo pod under the fuselage.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 25. Bombardier Challenger → `cl35-01.png`

```text
Flat mid-century screen-print illustration of a Bombardier Challenger business jet: two engines mounted on the rear fuselage, T-tail, wide oval cabin windows.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 26. Cessna Citation → `c56x-01.png`

```text
Flat mid-century screen-print illustration of a Cessna Citation business jet: compact fuselage, two rear-mounted engines, swept T-tail, small round windows.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 27. Embraer Phenom / PC-24 → `e55p-01.png`

```text
Flat mid-century screen-print illustration of an Embraer Phenom 300 light business jet: slim fuselage, two rear-mounted engines, swept winglets, T-tail.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 28. Kleinflugzeug → `c172-01.png`

```text
Flat mid-century screen-print illustration of a Cessna 172: small single-engine high-wing propeller plane with wing struts and fixed tricycle landing gear.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 29. Hubschrauber → `heli-01.png`

```text
Flat mid-century screen-print illustration of a twin-engine passenger helicopter (Airbus H145 style): main rotor with slightly drooping blades, shrouded fenestron tail rotor, skids.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### 30. Militaer → `mil-01.png`

```text
Flat mid-century screen-print illustration of an Airbus A400M military transport: high-wing four-engine turboprop with eight-blade scimitar propellers, upswept rear cargo ramp, tall T-tail.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

---

## Notfall-Motive

### `fallback-narrowbody-01.png`

```text
Flat mid-century screen-print illustration of a generic modern narrow-body airliner, two underwing engines, no distinctive model features.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-widebody-01.png`

```text
Flat mid-century screen-print illustration of a generic large wide-body airliner, two big underwing engines, long fuselage.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-turboprop-01.png`

```text
Flat mid-century screen-print illustration of a generic high-wing twin turboprop airliner with propellers.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-bizjet-01.png`

```text
Flat mid-century screen-print illustration of a generic small business jet with rear-mounted engines and a T-tail.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-ga-01.png`

```text
Flat mid-century screen-print illustration of a generic small single-engine propeller plane with fixed landing gear.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-heli-01.png`

```text
Flat mid-century screen-print illustration of a generic light helicopter with skids.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

### `fallback-unknown-01.png`

```text
Flat mid-century screen-print illustration of a generic airliner silhouette, side view, no distinctive features.
Strict side elevation (exact profile view), nose pointing right, the whole aircraft
fully inside the frame with even margins left and right.
Style: limited flat colour palette, warm cream (#F2ECE1) aircraft body on a solid
terracotta background (#B8402C), soft off-white and muted grey-blue accents, subtle
paper grain, gentle screen-print texture, thin darker outlines where shapes meet.
No gradients, no photorealism, no 3D rendering, no drop shadows, no perspective.
No airline logos, no livery markings, no registration codes, no text or lettering
anywhere in the image. Clean vintage travel-poster feel, 1960s airline poster aesthetic.
Landscape format, wide composition.
```

---

## Wenn der Stil auseinanderläuft

Nach ein paar Bildern driftet ChatGPT gern ab. Was hilft:

- Das zuletzt gelungene Bild erneut hochladen: *"exakt dieser Stil, nur jetzt ein …"*
- Immer denselben Chat verwenden, nie zwischendurch das Thema wechseln
- Bei Abweichung sofort korrigieren statt später — der Chat lernt die Abweichung sonst mit
- Kontrolle: Alle Bilder nebeneinander in einem Ordner ansehen. Was herausfällt, neu machen.
