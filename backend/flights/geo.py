"""Geometrie: Entfernung, Peilung und Elevationswinkel zum Flugzeug."""
from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088
FEET_TO_KM = 0.0003048
NM_TO_KM = 1.852


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Grosskreis-Entfernung zwischen zwei Punkten in Kilometern."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Peilung von Punkt 1 nach Punkt 2 in Grad (0 = Norden)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def elevation_deg(ground_distance_km: float, altitude_ft: float | None) -> float:
    """Wie hoch ueber dem Horizont steht das Flugzeug? 90 = direkt im Zenit."""
    if not altitude_ft or altitude_ft <= 0:
        return 0.0
    alt_km = altitude_ft * FEET_TO_KM
    if ground_distance_km <= 0.01:
        return 90.0
    return math.degrees(math.atan2(alt_km, ground_distance_km))


def compass_point(bearing: float) -> str:
    """Peilung als Himmelsrichtung (deutsch)."""
    points = ["N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return points[int((bearing + 11.25) % 360 // 22.5)]


def route_position_plausible(
    aircraft_lat: float,
    aircraft_lon: float,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
) -> bool:
    """Ob die aktuelle Position glaubhaft zwischen Start und Ziel liegt.

    Externe Callsign-Datenbanken koennen eine alte Route fuer ein inzwischen
    neu vergebenes Callsign liefern. Wir akzeptieren deshalb einen grosszuegigen
    350-km-Korridor um die Grosskreisroute, verhindern mit dem Umweg-Test aber
    auch Treffer weit vor dem Start oder hinter dem Ziel.
    """
    direct_km = haversine_km(origin_lat, origin_lon, destination_lat, destination_lon)
    origin_to_aircraft = haversine_km(origin_lat, origin_lon, aircraft_lat, aircraft_lon)
    aircraft_to_destination = haversine_km(
        aircraft_lat, aircraft_lon, destination_lat, destination_lon
    )

    if direct_km < 10:
        return min(origin_to_aircraft, aircraft_to_destination) <= 100

    angular_distance = origin_to_aircraft / EARTH_RADIUS_KM
    route_bearing = math.radians(
        bearing_deg(origin_lat, origin_lon, destination_lat, destination_lon)
    )
    aircraft_bearing = math.radians(
        bearing_deg(origin_lat, origin_lon, aircraft_lat, aircraft_lon)
    )
    cross_track = abs(
        math.asin(
            max(-1.0, min(1.0, math.sin(angular_distance) * math.sin(aircraft_bearing - route_bearing)))
        )
        * EARTH_RADIUS_KM
    )
    extra_km = origin_to_aircraft + aircraft_to_destination - direct_km
    allowed_extra = min(500.0, max(200.0, direct_km * 0.25))
    return cross_track <= 350.0 and extra_km <= allowed_extra
