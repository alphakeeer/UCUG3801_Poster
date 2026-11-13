"""Explicit coordinate conversion; GCJ-02 is not an EPSG projection.

The conventional GCJ displacement formula is inverted iteratively. Numerical
round-trip agreement checks the implementation, not real-world gate accuracy.
Original coordinates and transformation labels are always retained.
"""

import math

ALGORITHM = "gcj_iterative_inverse_v1"


def _offset(lon: float, lat: float) -> tuple[float, float]:
    x, y = lon - 105, lat - 35
    dy = -100 + 2*x + 3*y + .2*y*y + .1*x*y + .2*math.sqrt(abs(x))
    dx = 300 + x + 2*y + .1*x*x + .1*x*y + .1*math.sqrt(abs(x))
    wave = (20*math.sin(6*x*math.pi) + 20*math.sin(2*x*math.pi))*2/3
    dy += wave + (20*math.sin(y*math.pi) + 40*math.sin(y/3*math.pi))*2/3
    dy += (160*math.sin(y/12*math.pi) + 320*math.sin(y*math.pi/30))*2/3
    dx += wave + (20*math.sin(x*math.pi) + 40*math.sin(x/3*math.pi))*2/3
    dx += (150*math.sin(x/12*math.pi) + 300*math.sin(x/30*math.pi))*2/3
    radians = math.radians(lat)
    magic = 1 - .00669342162296594323 * math.sin(radians)**2
    dy = dy * 180 / ((6378245*(1-.00669342162296594323)/(magic**1.5))*math.pi)
    dx = dx * 180 / (6378245/math.sqrt(magic)*math.cos(radians)*math.pi)
    return dx, dy


def wgs84_to_gcj02(lon: float, lat: float) -> tuple[float, float]:
    if not (72.004 <= lon <= 137.8347 and .8293 <= lat <= 55.8271):
        raise ValueError("GCJ conversion is only supported inside the documented China extent")
    dx, dy = _offset(lon, lat)
    return lon + dx, lat + dy


def gcj02_to_wgs84(lon: float, lat: float) -> tuple[float, float]:
    guess_lon, guess_lat = lon, lat
    for _ in range(12):
        calc_lon, calc_lat = wgs84_to_gcj02(guess_lon, guess_lat)
        error_lon, error_lat = calc_lon-lon, calc_lat-lat
        guess_lon -= error_lon
        guess_lat -= error_lat
        if max(abs(error_lon), abs(error_lat)) < 1e-10:
            break
    return round(guess_lon, 8), round(guess_lat, 8)


def chord_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    return math.hypot((lon2-lon1)*math.cos(math.radians((lat1+lat2)/2)), lat2-lat1)*111195


def position(record_id: str, entity_id: str, role: str, lon: float, lat: float,
             crs: str, source_id: str, locator: str, status: str,
             note: str = "", candidate: str = "") -> dict:
    if crs not in {"WGS84", "GCJ-02"}:
        raise ValueError(f"Unsupported original CRS: {crs}")
    x, y = (lon, lat) if crs == "WGS84" else gcj02_to_wgs84(lon, lat)
    return dict(id=record_id, entity_id=entity_id, candidate_entity_id=candidate,
        position_role=role, original_longitude=lon, original_latitude=lat,
        original_crs=crs, longitude=x, latitude=y, crs="EPSG:4326",
        transform="identity" if crs=="WGS84" else ALGORITHM,
        verification_status=status, source_id=source_id, source_locator=locator,
        note=note, gate_verified=False)
