"""
collector.py — Agent 1: Raw data collection.

Fixes:
  - lat/lon are now passed through in the output dict (needed by analyzer.py)
  - Terrain classification improved
  - Forecast data structure consistent
"""

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _get_coordinates(city: str) -> tuple:
    """Geocode city name to (lat, lon, display_name)."""
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city + ", India", "format": "json", "limit": 1},
            headers={"User-Agent": "AgriMineralPipeline/2.0"},
            timeout=10,
        )
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        pass
    return 20.5937, 78.9629, "India (default)"


def _get_terrain(lat: float, lon: float, elevation_m: float) -> dict:
    """Classify terrain from elevation + coordinates."""
    if elevation_m > 2000:
        terrain_note = "mountain"
    elif elevation_m > 800:
        terrain_note = "hilly"
    elif elevation_m > 300:
        terrain_note = "gentle hills"
    else:
        terrain_note = "plains"

    return {
        "elevation_m": round(elevation_m, 1),
        "terrain_note": terrain_note,
    }


def collect_data(city: str, bounds: dict = None) -> dict:
    """
    Agent 1 — collect weather, terrain, forecast data.

    Returns dict with lat, lon, weather (current + forecast), terrain, maps.
    """
    # Use bounds center if provided, else geocode city
    if bounds and bounds.get("center"):
        lat = bounds["center"].get("lat", 20.5937)
        lon = bounds["center"].get("lon", 78.9629)
        display_name = city or "Selected region"
    else:
        lat, lon, display_name = _get_coordinates(city)

    # Fetch weather from Open-Meteo (free, no API key)
    weather_data = {}
    elevation_m = 200.0
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "windspeed_10m",
                "precipitation",
            ],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
            ],
            "forecast_days": 7,
            "timezone": "Asia/Kolkata",
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        wd = resp.json()

        elevation_m = float(wd.get("elevation", 200))

        weather_data = {
            "current": {
                "temperature_2m": wd.get("current", {}).get("temperature_2m", 25),
                "relative_humidity_2m": wd.get("current", {}).get("relative_humidity_2m", 60),
                "windspeed_10m": wd.get("current", {}).get("windspeed_10m", 10),
                "precipitation": wd.get("current", {}).get("precipitation", 0),
            },
            "weekly_forecast": wd.get("daily", {}),
            "timezone": wd.get("timezone", "Asia/Kolkata"),
        }
    except Exception as e:
        weather_data = {
            "current": {
                "temperature_2m": 25,
                "relative_humidity_2m": 60,
                "windspeed_10m": 10,
                "precipitation": 0,
            },
            "weekly_forecast": {},
            "timezone": "Asia/Kolkata",
            "error": str(e),
        }

    terrain = _get_terrain(lat, lon, elevation_m)

    maps = {
        "openstreetmap": f"https://www.openstreetmap.org/#map=13/{lat}/{lon}",
        "google_maps": f"https://maps.google.com/?q={lat},{lon}&z=13",
        "satellite_view": f"https://maps.google.com/?q={lat},{lon}&z=13&t=k",
    }

    return {
        "city": display_name,
        "lat": lat,
        "lon": lon,
        "weather": weather_data,
        "terrain": terrain,
        "maps": maps,
    }
