#!/usr/bin/env python3
"""Erzeugt schlichte Flugzeug-Silhouetten als Platzhalter.

Diese SVGs springen ein, solange fuer einen Typ noch kein eigenes Bild
hinterlegt ist - und dauerhaft fuer seltene Typen, fuer die sich ein
eigenes Motiv nicht lohnt.

    python tools/make_fallback_art.py

Schreibt nach frontend/art/fallback-*.svg
"""
from __future__ import annotations

from pathlib import Path

ART = Path(__file__).resolve().parent.parent / "frontend" / "art"

INK = "#f2ece1"          # Silhouette: Papierton auf der farbigen Posterflaeche
DETAIL = "#d9cdb8"       # Fenster, Fugen
SHADE = "#00000022"      # leichte Tiefe

W, H = 1200, 420


def _frame(body: str, caption: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{caption}">
  <g fill="{INK}" stroke="none">
{body}
  </g>
</svg>
"""


def _windows(x_start: float, x_end: float, y: float, step: float = 40, r: float = 7) -> str:
    out = []
    x = x_start
    while x <= x_end:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{DETAIL}" opacity="0.55"/>')
        x += step
    return "    " + "\n    ".join(out)


def airliner(*, nose=1090.0, tail=150.0, top=168.0, bottom=252.0, engines=1,
             double_deck=False, hump=False, caption="") -> str:
    """Klassisches Verkehrsflugzeug im Seitenprofil, Blickrichtung rechts."""
    mid = (top + bottom) / 2
    parts = []

    # Rumpf: Nase rechts, Heck links mit hochgezogenem Konus
    fuselage = (
        f'M {nose},{mid} '
        f'C {nose - 30},{top + 4} {nose - 90},{top} {nose - 150},{top} '
        f'L {tail + 190},{top} '
        f'C {tail + 120},{top} {tail + 70},{top - 12} {tail + 40},{top - 52} '
        f'L {tail},{top - 62} '
        f'L {tail + 26},{top - 8} '
        f'C {tail + 40},{bottom - 40} {tail + 90},{bottom} {tail + 175},{bottom} '
        f'L {nose - 150},{bottom} '
        f'C {nose - 80},{bottom} {nose - 26},{mid + 30} {nose},{mid} Z'
    )
    parts.append(f'    <path d="{fuselage}"/>')

    if hump:  # 747-Buckel
        parts.append(
            f'    <path d="M {nose - 210},{top} C {nose - 190},{top - 46} {nose - 120},{top - 52} '
            f'{nose - 60},{top - 44} C {nose - 30},{top - 40} {nose - 12},{top - 20} {nose - 4},{top - 4} Z"/>'
        )

    # Seitenleitwerk
    parts.append(
        f'    <path d="M {tail + 175},{top + 2} L {tail + 118},{top - 128} '
        f'L {tail + 34},{top - 128} L {tail + 40},{top - 50} Z"/>'
    )
    # Hoehenleitwerk
    parts.append(
        f'    <path d="M {tail + 52},{top - 44} L {tail - 26},{top - 72} '
        f'L {tail - 40},{top - 52} L {tail + 44},{top - 14} Z"/>'
    )

    # Fluegel, nach hinten gepfeilt
    wing_root = (nose + tail) / 2 + 70
    parts.append(
        f'    <path d="M {wing_root},{bottom - 14} L {wing_root - 300},{bottom + 70} '
        f'L {wing_root - 400},{bottom + 72} L {wing_root - 120},{bottom - 16} Z" opacity="0.92"/>'
    )

    # Triebwerksgondeln
    for i in range(engines):
        ex = wing_root - 110 - i * 150
        parts.append(
            f'    <rect x="{ex - 96:.0f}" y="{bottom + 6:.0f}" width="132" height="52" rx="26"/>'
            f'<rect x="{ex - 24:.0f}" y="{bottom + 14:.0f}" width="12" height="36" rx="6" fill="{SHADE}"/>'
        )

    # Fenster
    parts.append(_windows(tail + 250, nose - 190, mid - 6))
    if double_deck:
        parts.append(_windows(tail + 280, nose - 220, mid - 40, step=44, r=6))
    # Cockpit
    parts.append(
        f'    <path d="M {nose - 118},{top + 12} L {nose - 44},{top + 16} L {nose - 30},{mid - 12} '
        f'L {nose - 118},{mid - 16} Z" fill="{DETAIL}" opacity="0.75"/>'
    )
    return _frame("\n".join(parts), caption)


def turboprop(caption: str) -> str:
    top, bottom, nose, tail = 176.0, 250.0, 1010.0, 240.0
    mid = (top + bottom) / 2
    parts = [
        f'    <path d="M {nose},{mid} C {nose - 26},{top + 6} {nose - 70},{top} {nose - 120},{top} '
        f'L {tail + 150},{top} C {tail + 90},{top} {tail + 52},{top - 14} {tail + 30},{top - 56} '
        f'L {tail},{top - 66} L {tail + 20},{top - 6} C {tail + 34},{bottom - 34} {tail + 80},{bottom} '
        f'{tail + 140},{bottom} L {nose - 120},{bottom} C {nose - 66},{bottom} {nose - 22},{mid + 26} {nose},{mid} Z"/>',
        # T-Leitwerk
        f'    <path d="M {tail + 140},{top} L {tail + 96},{top - 150} L {tail + 44},{top - 150} L {tail + 30},{top - 52} Z"/>',
        f'    <rect x="{tail - 30:.0f}" y="{top - 164:.0f}" width="220" height="20" rx="9"/>',
        # Hochdecker-Fluegel mit Motorgondel und Propeller
        f'    <path d="M {mid + 380},{top + 4} L {mid + 250},{top - 26} L {mid - 20},{top - 26} '
        f'L {mid + 150},{top + 6} Z"/>',
        f'    <rect x="{mid + 150:.0f}" y="{top - 40:.0f}" width="190" height="46" rx="22"/>',
        f'    <rect x="{mid + 336:.0f}" y="{top - 96:.0f}" width="11" height="158" rx="5" opacity="0.55"/>',
        # Fahrwerksgondeln
        f'    <path d="M {mid + 190},{bottom - 4} q 60,0 60,42 l -120,0 q 0,-42 60,-42 Z" opacity="0.9"/>',
        _windows(tail + 190, nose - 150, mid - 4, step=44, r=6),
        f'    <path d="M {nose - 104},{top + 12} L {nose - 40},{top + 16} L {nose - 28},{mid - 10} '
        f'L {nose - 104},{mid - 14} Z" fill="{DETAIL}" opacity="0.75"/>',
    ]
    return _frame("\n".join(parts), caption)


def bizjet(caption: str) -> str:
    top, bottom, nose, tail = 186.0, 246.0, 1000.0, 280.0
    mid = (top + bottom) / 2
    parts = [
        f'    <path d="M {nose},{mid} C {nose - 24},{top + 4} {nose - 66},{top} {nose - 110},{top} '
        f'L {tail + 130},{top} C {tail + 80},{top} {tail + 46},{top - 12} {tail + 26},{top - 46} '
        f'L {tail},{top - 54} L {tail + 18},{top - 4} C {tail + 30},{bottom - 26} {tail + 70},{bottom} '
        f'{tail + 120},{bottom} L {nose - 110},{bottom} C {nose - 60},{bottom} {nose - 20},{mid + 20} {nose},{mid} Z"/>',
        f'    <path d="M {tail + 120},{top} L {tail + 84},{top - 140} L {tail + 38},{top - 140} L {tail + 26},{top - 44} Z"/>',
        f'    <rect x="{tail - 34:.0f}" y="{top - 154:.0f}" width="230" height="18" rx="8"/>',
        # heckmontierte Triebwerke
        f'    <rect x="{tail + 120:.0f}" y="{top - 6:.0f}" width="150" height="58" rx="28"/>',
        f'    <path d="M {mid + 400},{bottom - 8} L {mid + 150},{bottom + 56} L {mid + 60},{bottom + 56} '
        f'L {mid + 300},{bottom - 10} Z" opacity="0.92"/>',
        _windows(tail + 180, nose - 150, mid - 2, step=52, r=6),
        f'    <path d="M {nose - 96},{top + 10} L {nose - 38},{top + 14} L {nose - 26},{mid - 8} '
        f'L {nose - 96},{mid - 12} Z" fill="{DETAIL}" opacity="0.75"/>',
    ]
    return _frame("\n".join(parts), caption)


def light_aircraft(caption: str) -> str:
    top, bottom, nose, tail = 196.0, 252.0, 940.0, 300.0
    mid = (top + bottom) / 2
    parts = [
        f'    <path d="M {nose},{mid} C {nose - 20},{top + 4} {nose - 54},{top} {nose - 90},{top} '
        f'L {tail + 120},{top} C {tail + 70},{top} {tail + 40},{top - 10} {tail + 22},{top - 40} '
        f'L {tail},{top - 46} L {tail + 16},{top - 2} C {tail + 26},{bottom - 22} {tail + 60},{bottom} '
        f'{tail + 110},{bottom} L {nose - 90},{bottom} C {nose - 50},{bottom} {nose - 16},{mid + 18} {nose},{mid} Z"/>',
        f'    <path d="M {tail + 110},{top} L {tail + 76},{top - 118} L {tail + 34},{top - 118} L {tail + 22},{top - 38} Z"/>',
        f'    <path d="M {tail + 22},{top - 34} L {tail - 76},{top - 60} L {tail - 88},{top - 44} L {tail + 14},{top - 6} Z"/>',
        # Hochdecker-Fluegel
        f'    <path d="M {mid + 420},{top - 4} L {mid + 300},{top - 30} L {mid - 60},{top - 30} '
        f'L {mid + 120},{top - 2} Z"/>',
        f'    <rect x="{mid + 140:.0f}" y="{top - 30:.0f}" width="14" height="{bottom - top + 26:.0f}" rx="6" opacity="0.7"/>',
        # Propeller vorn
        f'    <rect x="{nose - 6:.0f}" y="{mid - 92:.0f}" width="12" height="184" rx="6" opacity="0.55"/>',
        # festes Fahrwerk
        f'    <rect x="{mid + 170:.0f}" y="{bottom:.0f}" width="12" height="46" rx="5"/>'
        f'<circle cx="{mid + 176:.0f}" cy="{bottom + 52:.0f}" r="18"/>',
        f'    <rect x="{nose - 150:.0f}" y="{bottom:.0f}" width="12" height="46" rx="5"/>'
        f'<circle cx="{nose - 144:.0f}" cy="{bottom + 52:.0f}" r="18"/>',
        f'    <path d="M {nose - 150},{top + 6} L {nose - 60},{top + 10} L {nose - 48},{mid - 6} '
        f'L {nose - 150},{mid - 10} Z" fill="{DETAIL}" opacity="0.75"/>',
    ]
    return _frame("\n".join(parts), caption)


def helicopter(caption: str) -> str:
    parts = [
        # Kabine mit auslaufendem Heckausleger
        '    <path d="M 760,300 C 640,300 540,286 486,252 C 440,222 430,196 452,178 '
        'C 486,150 592,140 690,146 C 760,150 812,166 846,192 L 900,232 '
        'C 916,244 912,264 892,268 L 820,288 C 800,296 780,300 760,300 Z"/>',
        '    <path d="M 470,222 L 250,206 L 236,232 L 468,250 Z"/>',
        # Heckrotor und Finne
        '    <path d="M 262,214 L 214,142 L 186,146 L 232,222 Z"/>',
        '    <circle cx="200" cy="140" r="13"/>',
        '    <rect x="194" y="70" width="11" height="146" rx="5" opacity="0.5"/>',
        # Rotormast und Blaetter
        '    <rect x="654" y="104" width="18" height="52" rx="8"/>',
        '    <rect x="330" y="96" width="660" height="13" rx="6" opacity="0.85"/>',
        '    <rect x="470" y="112" width="420" height="8" rx="4" opacity="0.4"/>',
        # Kufen
        '    <rect x="470" y="332" width="380" height="13" rx="6"/>',
        '    <rect x="548" y="298" width="12" height="40" rx="5"/>',
        '    <rect x="760" y="298" width="12" height="40" rx="5"/>',
        f'    <path d="M 700,168 C 760,172 806,190 838,214 L 800,238 C 764,214 726,198 690,192 Z" fill="{DETAIL}" opacity="0.7"/>',
    ]
    return _frame("\n".join(parts), caption)


VARIANTS = {
    "fallback-narrowbody": lambda: airliner(engines=1, caption="Verkehrsflugzeug"),
    "fallback-widebody": lambda: airliner(nose=1120, tail=120, top=158, bottom=266,
                                          engines=1, caption="Grossraumflugzeug"),
    "fallback-turboprop": lambda: turboprop("Turboprop"),
    "fallback-bizjet": lambda: bizjet("Geschaeftsreiseflugzeug"),
    "fallback-ga": lambda: light_aircraft("Kleinflugzeug"),
    "fallback-heli": lambda: helicopter("Hubschrauber"),
    "fallback-unknown": lambda: airliner(engines=1, caption="Flugzeug"),
}


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    for name, build in VARIANTS.items():
        path = ART / f"{name}-01.svg"
        path.write_text(build(), encoding="utf-8")
        print(f"  {path.relative_to(ART.parent.parent)}  ({path.stat().st_size // 1024 or 1} KB)")
    print(f"\n{len(VARIANTS)} Platzhalter erzeugt.")


if __name__ == "__main__":
    main()
