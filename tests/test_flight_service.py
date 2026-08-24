from __future__ import annotations

import time
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend import store
from backend.config import Config, Flights, Location
from backend.flights.adsb import AdsbClient
from backend.flights.artwork import ArtworkIndex
from backend.flights import geo
from backend.flights.service import FlightService
from backend.hub import Hub


class FakeClient:
    active_source = "test"

    def __init__(self, responses: dict[int, list[dict]]) -> None:
        self.responses = responses
        self.calls: list[int] = []

    async def aircraft_near(self, lat: float, lon: float, dist_nm: int):
        self.calls.append(dist_nm)
        return self.responses.get(dist_nm, [])

    async def aclose(self) -> None:
        pass


class FakeEnricher:
    async def aircraft(self, hex_code: str) -> dict:
        return {}

    async def route(self, callsign: str) -> dict:
        return {}


class FakeHttp:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def json(self, url: str):
        self.urls.append(url)
        return {"ac": []} if "adsb.fi" in url else None

    async def aclose(self) -> None:
        pass


class TestFlightService(FlightService):
    async def _join(self, aircraft: dict, now: float) -> dict:
        joined = dict(aircraft)
        joined.update({"last_seen": now, "is_stale": False})
        return joined


def raw_aircraft(hex_code: str, lat_offset: float) -> dict:
    return {
        "hex": hex_code,
        "lat": 52.0 + lat_offset,
        "lon": 10.0,
        "alt_baro": 10_000,
        "gs": 300,
        "track": 90,
        "baro_rate": 0,
        "category": "A3",
    }


def candidate(hex_code: str, distance: float) -> dict:
    return {
        "hex": hex_code,
        "callsign": hex_code.upper(),
        "registration": None,
        "type_code": "A320",
        "lat": 52.2,
        "lon": 10.5,
        "altitude_ft": 10_000,
        "ground_speed_kt": 300,
        "track_deg": 90,
        "vertical_rate_fpm": 0,
        "ground_distance_km": distance,
        "distance_km": distance,
        "bearing_deg": 90,
        "compass": "O",
        "elevation_deg": 10,
        "climb_state": "Reiseflug",
        "squawk": None,
        "emergency": None,
        "category": "A3",
    }


class FlightServiceTests(unittest.IsolatedAsyncioTestCase):
    def make_service(self, client: FakeClient) -> TestFlightService:
        config = Config(
            location=Location(lat=52.0, lon=10.0, radius_nm=50),
            flights=Flights(
                max_tracked=3,
                linger_seconds=90,
                max_radius_nm=100,
                radius_step_nm=25,
                radius_margin_nm=5,
            ),
        )
        return TestFlightService(config, Hub(), FakeEnricher(), client)

    async def test_radius_expands_until_three_candidates_are_available(self) -> None:
        near = [raw_aircraft("a", 0.01), raw_aircraft("b", 0.02)]
        expanded = [*near, raw_aircraft("c", 0.03)]
        client = FakeClient({50: near, 75: expanded})
        service = self.make_service(client)

        await service.tick()

        self.assertEqual(client.calls, [50, 75])
        self.assertEqual(len(service.fleet), 3)
        self.assertEqual(service.candidate_count, 3)
        self.assertFalse(service.radius_exhausted)

    async def test_full_live_result_is_always_the_exact_nearest_three(self) -> None:
        service = self.make_service(FakeClient({}))
        now = time.time()
        service.fleet = [
            {**candidate("a", 1.0), "last_seen": now},
            {**candidate("b", 2.0), "last_seen": now},
            {**candidate("old", 3.1), "last_seen": now},
        ]

        await service._update_fleet([
            candidate("a", 1.0),
            candidate("b", 2.0),
            candidate("new", 3.0),
            candidate("old", 3.1),
        ])

        self.assertEqual([item["hex"] for item in service.fleet], ["a", "b", "new"])

    async def test_linger_only_fills_a_live_data_gap(self) -> None:
        service = self.make_service(FakeClient({}))
        now = time.time()
        service.fleet = [
            {**candidate("a", 1.0), "last_seen": now},
            {**candidate("b", 2.0), "last_seen": now},
            {**candidate("c", 3.0), "last_seen": now},
        ]

        await service._update_fleet([candidate("a", 1.1), candidate("b", 2.1)])

        self.assertEqual(len(service.fleet), 3)
        self.assertTrue(next(item for item in service.fleet if item["hex"] == "c")["is_stale"])

    async def test_successful_fallback_is_tried_first_on_the_next_poll(self) -> None:
        client = AdsbClient()
        fake_http = FakeHttp()
        client._http = fake_http

        await client.aircraft_near(52.2, 10.5, 50)
        self.assertEqual(client.active_source, "adsb.fi")
        fake_http.urls.clear()

        await client.aircraft_near(52.2, 10.5, 50)

        self.assertEqual(len(fake_http.urls), 1)
        self.assertIn("adsb.fi", fake_http.urls[0])


class ArtworkTests(unittest.TestCase):
    def test_airline_match_and_neutral_fallback(self) -> None:
        artwork = ArtworkIndex()

        cathay = artwork.match("b747", "widebody", ["Cathay Cargo"], "b747-test")
        unknown = artwork.match("b787", "widebody", ["Unknown Air"], "b787-test")

        self.assertEqual(cathay["file"], "display/b747--cathay-cargo-01.png")
        self.assertEqual(cathay["match"], "airline")
        self.assertEqual(unknown["match"], "fallback")
        self.assertEqual(unknown["file"], "fallback-widebody-01.svg")

    def test_display_cutout_works_without_unpublished_raw_master(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            art_dir = Path(temp_dir)
            display_dir = art_dir / "display"
            display_dir.mkdir()
            filename = "b747--cathay-cargo-01.png"
            (display_dir / filename).write_bytes(b"display-cutout")
            (art_dir / "manifest.tsv").write_text(
                "file\tfamily\toperator\toperator_aliases\n"
                f"{filename}\tb747\tCathay Pacific Cargo\tCathay Cargo\n",
                encoding="utf-8",
            )

            artwork = ArtworkIndex(art_dir)
            cathay = artwork.match("b747", "widebody", ["Cathay Cargo"], "clean-clone")

            self.assertEqual(cathay["file"], f"display/{filename}")
            self.assertEqual(cathay["match"], "airline")
            coverage = artwork.coverage()
            self.assertEqual(coverage["display_cutouts"], 1)
            self.assertEqual(coverage["families_with_art"], 1)
            self.assertEqual(coverage["files"], 1)

    def test_type_code_prevents_wrong_subtype_livery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            art_dir = Path(temp_dir)
            display_dir = art_dir / "display"
            display_dir.mkdir()
            for filename in ("a321--sample-ceo.png", "a321--sample-neo.png"):
                (display_dir / filename).write_bytes(b"display-cutout")
            (art_dir / "manifest.tsv").write_text(
                "file\tfamily\toperator\toperator_aliases\ttype_codes\n"
                "a321--sample-ceo.png\ta321\tSample Air\tSample\tA321\n"
                "a321--sample-neo.png\ta321\tSample Air\tSample\tA21N\n",
                encoding="utf-8",
            )

            artwork = ArtworkIndex(art_dir)

            ceo = artwork.match("a321", "narrowbody", ["Sample"], type_code="A321")
            neo = artwork.match("a321", "narrowbody", ["Sample"], type_code="A21N")
            unknown = artwork.match("a321", "narrowbody", ["Sample"], type_code="A320")

            self.assertEqual(ceo["file"], "display/a321--sample-ceo.png")
            self.assertEqual(neo["file"], "display/a321--sample-neo.png")
            self.assertEqual(unknown["match"], "none")


class RoutePlausibilityTests(unittest.TestCase):
    def test_stale_milan_munich_route_is_rejected_over_braunschweig(self) -> None:
        self.assertFalse(geo.route_position_plausible(
            52.2044, 10.5241, 45.6306, 8.7281, 48.3538, 11.7861
        ))

    def test_gothenburg_frankfurt_route_is_plausible_over_braunschweig(self) -> None:
        self.assertTrue(geo.route_position_plausible(
            52.2044, 10.5241, 57.6628, 12.2798, 50.0379, 8.5622
        ))

    def test_route_filter_keeps_airline_but_hides_bad_airports(self) -> None:
        ac = {"callsign": "DLH8VY", "lat": 52.2044, "lon": 10.5241}
        route = {
            "airline": {"name": "Lufthansa"},
            "callsign_iata": "LH1857",
            "origin": {"iata": "MXP", "lat": 45.6306, "lon": 8.7281},
            "destination": {"iata": "MUC", "lat": 48.3538, "lon": 11.7861},
        }

        cleaned = FlightService._validated_route(ac, route)

        self.assertEqual(cleaned["route_status"], "unverified")
        self.assertEqual(cleaned["airline"]["name"], "Lufthansa")
        self.assertNotIn("origin", cleaned)
        self.assertNotIn("destination", cleaned)


class AircraftCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_connection = store._conn
        self.memory_connection = sqlite3.connect(":memory:")
        self.memory_connection.row_factory = sqlite3.Row
        self.original_connection.backup(self.memory_connection)
        store._conn = self.memory_connection

    def tearDown(self) -> None:
        store._conn = self.original_connection
        self.memory_connection.close()

    def test_model_airline_pair_is_upserted_without_false_refresh_sighting(self) -> None:
        flight = {
            "type_code": "B744",
            "art_family": "b747",
            "type_name": "Boeing 747-400F",
            "manufacturer": "Boeing",
            "display_operator": "Cathay Pacific Cargo",
            "art_file": "b747--cathay-cargo-01.png",
            "art_match": "airline",
        }

        store.record_aircraft_model(flight)
        store.record_aircraft_model(flight, count_sighting=False)
        rows = store.aircraft_model_catalog()

        row = next(item for item in rows if item["model_key"] == "B744")
        self.assertEqual(row["airline"], "Cathay Pacific Cargo")
        self.assertEqual(row["sightings"], 1)
        self.assertEqual(row["needs_artwork"], 0)


if __name__ == "__main__":
    unittest.main()
