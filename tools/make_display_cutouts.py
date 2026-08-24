#!/usr/bin/env python3
"""Erzeugt echte RGBA-Freisteller aus den roten FlightWall-Artwork-Mastern.

Die Flugzeuge werden nicht neu gerendert. Stattdessen wird nur die vom Bildrand
aus zusammenhaengende rote/orange Druckflaeche entfernt. So bleiben Lackierung,
Logos, Schrift und Retro-Raster pixelgenau erhalten.

Beispiele:
  python tools/make_display_cutouts.py --input frontend/art/b747--cathay-cargo-01.png
  python tools/make_display_cutouts.py --all
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent.parent
ART_DIR = ROOT / "frontend" / "art"
DISPLAY_DIR = ART_DIR / "display"


def looks_like_backdrop(pixel: tuple[int, ...]) -> bool:
    """Die Masters haben einen gesaettigten rot-orangen Hintergrund."""
    red, green, blue = pixel[:3]
    return red >= 105 and red - green >= 45 and red - blue >= 65


def edge_seeds(width: int, height: int, spacing: int = 72):
    for x in range(0, width, spacing):
        yield x, 0
        yield x, height - 1
    for y in range(0, height, spacing):
        yield 0, y
        yield width - 1, y
    yield width - 1, height - 1


def aircraft_seed(mask: Image.Image) -> tuple[int, int]:
    """Findet die dichteste Flugzeugzeile statt eines zufaelligen Korns."""
    width, height = mask.size
    row_density = list(mask.resize((1, height), Image.Resampling.BOX).tobytes())
    y = max(range(height), key=row_density.__getitem__)
    foreground_x = [x for x, value in enumerate(mask.crop((0, y, width, y + 1)).tobytes()) if value]
    if not foreground_x:
        raise ValueError("Kein Flugzeug-Vordergrund gefunden")
    return foreground_x[len(foreground_x) // 2], y


def keep_aircraft_component(alpha: Image.Image) -> Image.Image:
    """Entfernt isolierte Papierkoernungs-Pixel ausserhalb des Flugzeugs."""
    binary = alpha.point(lambda value: 255 if value > 4 else 0)
    seed = aircraft_seed(binary)
    component = binary.copy()
    ImageDraw.floodfill(component, seed, 128, thresh=0)
    component = component.point(lambda value: 255 if value == 128 else 0)

    # Kleine getrennte Antennen/Details direkt am Rumpf wieder aufnehmen,
    # weit entfernte Hintergrundsprenkel aber verwerfen.
    for _ in range(2):
        nearby = component.filter(ImageFilter.MaxFilter(9))
        component = Image.new("L", alpha.size, 0)
        component.paste(255, mask=Image.composite(binary, Image.new("L", alpha.size), nearby))

    return Image.composite(alpha, Image.new("L", alpha.size), component)


def make_cutout(
    source: Path,
    destination: Path,
    threshold: int = 72,
    preserve_alpha: bool = False,
) -> None:
    original = Image.open(source).convert("RGBA")
    work = original.copy()

    if preserve_alpha:
        # ImageGen kann bereits echte Transparenz liefern. Dann nur lose
        # Extraktionspixel entfernen und eng zuschneiden, ohne rote/orange
        # Lackierungen erneut gegen den roten Master-Hintergrund zu testen.
        alpha = keep_aircraft_component(work.getchannel("A"))
    else:
        draw = ImageDraw.Draw(work)

        # Mehrere Randpunkte fangen auch leichte Farbverlaeufe und Papierkoernung
        # ein. Floodfill entfernt nur zusammenhaengende Flaechen und greift daher
        # keine roten Details an, die innerhalb des Flugzeugs liegen.
        for seed in edge_seeds(*work.size):
            pixel = work.getpixel(seed)
            if pixel[3] and looks_like_backdrop(pixel):
                ImageDraw.floodfill(work, seed, (0, 0, 0, 0), thresh=threshold)

        alpha = keep_aircraft_component(work.getchannel("A"))
    # Ein sehr kleiner weicher Rand verhindert gezackte Kanten im Passepartout,
    # ohne feine Antennen oder Leitwerkskanten sichtbar zu verbreitern.
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.35))
    work.putalpha(alpha)

    # Transparente Leerflaeche wegschneiden, damit das Flugzeug im festen
    # Dashboard-Raster gross statt als kleine 16:9-Karte erscheint.
    bbox = alpha.getbbox()
    if bbox:
        padding = max(12, round(max(work.size) * 0.012))
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(work.width, bbox[2] + padding)
        bottom = min(work.height, bbox[3] + padding)
        work = work.crop((left, top, right, bottom))

    destination.parent.mkdir(parents=True, exist_ok=True)
    work.save(destination, "PNG", optimize=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="ein einzelner PNG-Master")
    group.add_argument("--all", action="store_true", help="alle Airline-PNGs verarbeiten")
    parser.add_argument("--output", type=Path, help="Ausgabedatei bei --input")
    parser.add_argument("--threshold", type=int, default=72, help="Farbtoleranz fuer den Hintergrund")
    parser.add_argument(
        "--preserve-alpha",
        action="store_true",
        help="vorhandene Transparenz bereinigen und zuschneiden, Hintergrund nicht neu entfernen",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.all:
        sources = sorted(path for path in ART_DIR.glob("*.png") if "--" in path.name)
        for source in sources:
            destination = DISPLAY_DIR / source.name
            make_cutout(source, destination, args.threshold)
            print(destination.relative_to(ROOT))
        return

    source = args.input.resolve()
    destination = args.output or (DISPLAY_DIR / source.name)
    make_cutout(source, destination.resolve(), args.threshold, args.preserve_alpha)
    print(destination)


if __name__ == "__main__":
    main()
