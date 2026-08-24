"""Ordnet Typ und Airline einem vorbereiteten Poster zu.

Ablage: ``frontend/art/<familie>--<airline>-01.png``. Die optionale
``manifest.tsv`` im selben Ordner enthaelt die lesbaren Airline-Namen und
Aliases. Alte familienbasierte Dateinamen bleiben weiterhin kompatibel.
"""
from __future__ import annotations

import csv
import random
import re
import unicodedata
from pathlib import Path
from typing import Any

from ..config import ROOT

ART_DIR = ROOT / "frontend" / "art"
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".svg")

# slug -> (Anzeigename, Kategorie, [ICAO-Typcodes])
FAMILIES: dict[str, tuple[str, str, list[str]]] = {
    # --- Schmalrumpf ---------------------------------------------------
    "a319":  ("Airbus A319", "narrowbody", ["A318", "A319", "A19N"]),
    "a320":  ("Airbus A320", "narrowbody", ["A320", "A20N"]),
    "a321":  ("Airbus A321", "narrowbody", ["A321", "A21N"]),
    "a220":  ("Airbus A220", "narrowbody", ["BCS1", "BCS3", "A220"]),
    "b737c": ("Boeing 737 Classic", "narrowbody", ["B731", "B732", "B733", "B734", "B735"]),
    "b738":  ("Boeing 737NG", "narrowbody", ["B736", "B737", "B738", "B739", "B73H"]),
    "b38m":  ("Boeing 737 MAX", "narrowbody", ["B37M", "B38M", "B39M", "B3XM"]),
    "b757":  ("Boeing 757", "narrowbody", ["B752", "B753", "B757"]),
    # --- Regional ------------------------------------------------------
    "e190":  ("Embraer E-Jet E2", "regional", ["E190", "E195", "E290", "E295", "E90", "E95"]),
    "e175":  ("Embraer E175", "regional", ["E170", "E175", "E75L", "E75S", "E70"]),
    "crj":   ("Bombardier CRJ", "regional", ["CRJ1", "CRJ2", "CRJ7", "CRJ9", "CRJX", "CRJ"]),
    # --- Grossraum -----------------------------------------------------
    "a330":  ("Airbus A330", "widebody", ["A332", "A333", "A338", "A339", "A330", "A33X"]),
    "a340":  ("Airbus A340", "widebody", ["A342", "A343", "A345", "A346", "A340"]),
    "a350":  ("Airbus A350", "widebody", ["A359", "A35K", "A350"]),
    "a380":  ("Airbus A380", "widebody", ["A388", "A380"]),
    "b767":  ("Boeing 767", "widebody", ["B762", "B763", "B764", "B767"]),
    "b777":  ("Boeing 777", "widebody", ["B772", "B773", "B77L", "B77W", "B778", "B779", "B777"]),
    "b787":  ("Boeing 787", "widebody", ["B788", "B789", "B78X", "B787"]),
    "b747":  ("Boeing 747", "widebody", ["B741", "B742", "B743", "B744", "B748", "B74F", "B747"]),
    "md11":  ("McDonnell Douglas MD-11", "widebody", ["MD11", "MD1F", "DC10", "MD82", "MD83", "MD88"]),
    # --- Turboprop -----------------------------------------------------
    "at72":  ("ATR 72", "turboprop", ["AT43", "AT44", "AT45", "AT46", "AT72", "AT73", "AT75", "AT76", "ATR"]),
    "dh8d":  ("De Havilland Dash 8", "turboprop", ["DH8A", "DH8B", "DH8C", "DH8D", "DHC8"]),
    "b350":  ("Beechcraft King Air", "turboprop", ["BE20", "B350", "BE9L", "BE10", "C441"]),
    "c208":  ("Cessna Caravan", "turboprop", ["C208", "C20T", "PC12", "TBM7", "TBM8", "TBM9", "P180"]),
    # --- Geschaeftsreise ------------------------------------------------
    "cl35":  ("Bombardier Challenger", "bizjet", ["CL30", "CL35", "CL60", "CL64", "GLEX", "GL5T", "GL7T", "GLF4", "GLF5", "GLF6"]),
    "c56x":  ("Cessna Citation", "bizjet", ["C25A", "C25B", "C25C", "C500", "C510", "C525", "C550", "C560", "C56X", "C680", "C68A", "C700", "C750"]),
    "e55p":  ("Embraer Phenom / PC-24", "bizjet", ["E50P", "E55P", "PC24", "HDJT", "LJ35", "LJ45", "LJ60", "FA7X", "FA8X", "F2TH"]),
    # --- Kleinflugzeuge / Sonstiges -------------------------------------
    "c172":  ("Kleinflugzeug", "ga", ["C152", "C162", "C172", "C177", "C182", "C206", "PA28", "PA32", "PA34", "DA40", "DA42", "DA62", "SR20", "SR22", "AC11", "P28A", "BE33", "BE36", "M20P", "RV7", "RV8", "A210", "AT01", "P208", "P06T", "P46T"]),
    "heli":  ("Hubschrauber", "heli", ["EC20", "EC25", "EC30", "EC35", "EC45", "EC55", "H125", "H135", "H145", "H160", "H175", "AS32", "AS50", "AS55", "A109", "A139", "A169", "B06", "B407", "B412", "B429", "R22", "R44", "R66", "S76", "S92", "MD90"]),
    "mil":   ("Militaer", "military", ["A400", "C130", "C30J", "C17", "K35R", "KC30", "A332", "E3TF", "P8", "EUFI", "F16", "F15", "F18", "F35", "TOR", "GLF5", "RQ4", "H60", "CH47", "C295", "C160"]),
}

CATEGORY_FALLBACK = {
    "narrowbody": "fallback-narrowbody",
    "widebody": "fallback-widebody",
    "regional": "fallback-narrowbody",
    "turboprop": "fallback-turboprop",
    "bizjet": "fallback-bizjet",
    "ga": "fallback-ga",
    "heli": "fallback-heli",
    "military": "fallback-narrowbody",
    "unknown": "fallback-unknown",
}

# ADS-B "category" als letzte Rettung, wenn der Typcode voellig unbekannt ist
ADSB_CATEGORY = {
    "A1": ("ga", "Kleinflugzeug"),
    "A2": ("bizjet", "Geschaeftsreiseflugzeug"),
    "A3": ("narrowbody", "Verkehrsflugzeug"),
    "A4": ("narrowbody", "Verkehrsflugzeug"),
    "A5": ("widebody", "Grossraumflugzeug"),
    "A6": ("military", "Militaerflugzeug"),
    "A7": ("heli", "Hubschrauber"),
    "B2": ("unknown", "Ballon"),
    "B4": ("unknown", "Segelflugzeug"),
}

_TYPE_INDEX: dict[str, str] = {
    code: slug for slug, (_, _, codes) in FAMILIES.items() for code in codes
}


def family_for(type_code: str | None, category: str | None = None) -> tuple[str, str, str]:
    """(slug, Anzeigename, Kategorie) fuer einen Typcode."""
    code = (type_code or "").strip().upper()
    slug = _TYPE_INDEX.get(code)
    if slug:
        label, cat, _ = FAMILIES[slug]
        return slug, label, cat

    # Kein Treffer: die ADS-B-Kategorie ist verlaesslicher als jede
    # Praefix-Ratelei (die machte aus einer Aquila A210 einen "Airbus A321").
    cat, label = ADSB_CATEGORY.get((category or "").upper(), ("unknown", "Flugzeug"))
    return CATEGORY_FALLBACK[cat], label, cat


class ArtworkIndex:
    """Findet Poster nach Flugzeugfamilie und, wenn moeglich, Airline."""

    def __init__(self, art_dir: Path | None = None) -> None:
        self.art_dir = art_dir or ART_DIR
        self._index: dict[str, list[str]] = {}
        self._generic_index: dict[str, list[str]] = {}
        self._airline_index: dict[tuple[str, str], list[str]] = {}
        self._file_operators: dict[str, str] = {}
        self._file_type_codes: dict[str, set[str]] = {}
        self._manifest: list[dict[str, str]] = []
        self.refresh()

    def refresh(self) -> None:
        index: dict[str, list[str]] = {}
        airline_index: dict[tuple[str, str], list[str]] = {}
        file_operators: dict[str, str] = {}
        file_type_codes: dict[str, set[str]] = {}
        manifest: list[dict[str, str]] = []
        if self.art_dir.is_dir():
            for path in sorted(self.art_dir.iterdir()):
                if path.suffix.lower() not in EXTENSIONS or path.name.startswith("."):
                    continue
                if "--" in path.stem:
                    slug = path.stem.split("--", 1)[0]
                else:
                    slug = re.sub(r"-\d+$", "", path.stem)
                index.setdefault(slug.lower(), []).append(path.name)
            manifest_path = self.art_dir / "manifest.tsv"
            if manifest_path.is_file():
                with manifest_path.open(encoding="utf-8", newline="") as handle:
                    for row in csv.DictReader(handle, delimiter="\t"):
                        filename = (row.get("file") or "").strip()
                        family = (row.get("family") or "").strip().lower()
                        source_path = self.art_dir / filename
                        display_path = self.art_dir / "display" / filename
                        # Im oeffentlichen Repository liegen nur die fertig
                        # freigestellten Display-Dateien. Die grossen Rohmaster
                        # bleiben lokal und duerfen fuer einen Treffer daher
                        # nicht zwingend erforderlich sein.
                        has_artwork = source_path.is_file() or display_path.is_file()
                        if not filename or not family or not has_artwork:
                            continue
                        served_filename = f"display/{filename}" if display_path.is_file() else filename
                        operator = (row.get("operator") or "").strip()
                        type_codes = {
                            code.strip().upper()
                            for code in (row.get("type_codes") or "").split("|")
                            if code.strip()
                        }
                        aliases = [operator, *((row.get("operator_aliases") or "").split("|"))]
                        for alias in aliases:
                            key = normalise_airline(alias)
                            if key:
                                airline_index.setdefault((family, key), []).append(served_filename)
                        file_operators[served_filename] = operator
                        file_type_codes[served_filename] = type_codes
                        manifest.append({k: (v or "") for k, v in row.items()})
        self._index = index
        manifest_files = {row.get("file", "") for row in manifest}
        self._generic_index = {
            slug: [filename for filename in files if filename not in manifest_files]
            for slug, files in index.items()
        }
        self._airline_index = airline_index
        self._file_operators = file_operators
        self._file_type_codes = file_type_codes
        self._manifest = manifest

    @property
    def available(self) -> dict[str, list[str]]:
        return dict(self._index)

    def match(
        self,
        slug: str,
        category: str,
        airlines: list[str | None] | None = None,
        seed: str | None = None,
        type_code: str | None = None,
    ) -> dict[str, str | None]:
        """Poster-Treffer samt Qualitaet (Airline, Familie oder Platzhalter)."""
        rng = random.Random(seed) if seed else random
        for airline in airlines or []:
            airline_key = normalise_airline(airline)
            files = self._airline_index.get((slug, airline_key)) if airline_key else None
            if files and type_code:
                code = type_code.strip().upper()
                files = [
                    filename for filename in files
                    if not self._file_type_codes.get(filename)
                    or code in self._file_type_codes[filename]
                ]
            if files:
                filename = rng.choice(files)
                return {
                    "url": f"/art/{filename}",
                    "file": filename,
                    "match": "airline",
                    "operator": self._file_operators.get(filename),
                }

        for candidate in (slug, CATEGORY_FALLBACK.get(category), CATEGORY_FALLBACK["unknown"]):
            if not candidate:
                continue
            # Airline-spezifische Manifest-Dateien duerfen nicht als falsche
            # Lackierung fuer eine andere Airline herhalten. Nur alte/generische
            # Familienbilder und die neutralen SVG-Fallbacks landen hier.
            files = self._generic_index.get(candidate)
            if files:
                # gleiche Registrierung -> gleiches Bild, damit es nicht flackert
                filename = rng.choice(files)
                return {
                    "url": f"/art/{filename}",
                    "file": filename,
                    "match": "family" if candidate == slug else "fallback",
                    "operator": self._file_operators.get(filename),
                }
        return {"url": None, "file": None, "match": "none", "operator": None}

    def pick(
        self,
        slug: str,
        category: str,
        seed: str | None = None,
        airlines: list[str | None] | None = None,
        type_code: str | None = None,
    ) -> str | None:
        """Kompatible Kurzform, wenn nur die URL benoetigt wird."""
        return self.match(
            slug,
            category,
            airlines=airlines,
            seed=seed,
            type_code=type_code,
        )["url"]

    def coverage(self) -> dict[str, Any]:
        """Welche Familien haben schon ein Bild, welche fehlen noch?"""
        manifest_families = {row.get("family", "") for row in self._manifest}
        have = [
            slug for slug in FAMILIES
            if self._index.get(slug) or slug in manifest_families
        ]
        missing = [slug for slug in FAMILIES if not self._index.get(slug)]
        missing = [slug for slug in missing if slug not in manifest_families]
        fallbacks = [f for f in set(CATEGORY_FALLBACK.values()) if self._index.get(f)]
        return {
            "families_total": len(FAMILIES),
            "families_with_art": len(have),
            "missing": missing,
            "fallbacks_present": sorted(fallbacks),
            # Manifest-Dateien koennen als Rohmaster plus Display-Freisteller
            # vorliegen oder, wie im oeffentlichen Clone, nur als Freisteller.
            "files": sum(len(v) for v in self._generic_index.values()) + len(self._manifest),
            "airline_pairs": len(self._airline_index),
            "manifest_entries": len(self._manifest),
            "display_cutouts": sum(1 for row in self._manifest if (self.art_dir / "display" / row.get("file", "")).is_file()),
            "operators": sorted({row.get("operator", "") for row in self._manifest if row.get("operator")}),
        }


def normalise_airline(value: str | None) -> str:
    """Airline-Namen stabil vergleichen, unabhaengig von Satzzeichen/Umlauten."""
    text = unicodedata.normalize("NFKD", value or "")
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", ascii_text.casefold())
