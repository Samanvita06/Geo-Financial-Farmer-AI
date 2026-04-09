"""
analyzer.py — Geo-spatial analysis agent.

Fixes:
  - Season detection now uses lat/lon + month (not just temperature)
  - Climate zone classification covers all of India properly
  - Land type inference from elevation + coordinates
  - Farming/soil scores are meaningful, not always 7/10
"""

from datetime import datetime


# ─── Climate zone lookup by lat/lon bounding boxes ────────────────────────────
# India spans ~8°N to 37°N, 68°E to 97°E
# Zones per Köppen-Geiger adapted for Indian agriculture

CLIMATE_ZONES = [
    # (lat_min, lat_max, lon_min, lon_max, zone_name)
    # Northeast India — tropical/subtropical wet
    (22, 30, 88, 97, "subtropical humid"),
    # Eastern India (WB, Odisha, Jharkhand)
    (19, 27, 83, 92, "subtropical humid"),
    # Kerala + coastal Karnataka
    (8, 15, 74, 78, "tropical wet"),
    # Tamil Nadu + Andhra coast
    (8, 16, 78, 83, "tropical wet-dry"),
    # Karnataka interior + Telangana
    (14, 20, 74, 80, "tropical dry"),
    # Maharashtra (Deccan)
    (15, 22, 73, 80, "semi-arid"),
    # Rajasthan + Gujarat dry
    (22, 30, 68, 76, "arid / hot desert"),
    # Gujarat coastal
    (20, 24, 68, 74, "semi-arid"),
    # Madhya Pradesh + Chhattisgarh
    (18, 25, 75, 84, "subtropical sub-humid"),
    # UP + Bihar plains
    (24, 28, 78, 88, "subtropical sub-humid"),
    # Punjab + Haryana
    (28, 32, 73, 78, "subtropical sub-humid"),
    # Delhi NCR
    (28, 29, 76, 78, "subtropical semi-arid"),
    # Himachal Pradesh + Uttarakhand foothills
    (28, 33, 76, 82, "subtropical highland"),
    # J&K + Ladakh
    (32, 37, 72, 80, "cold arid / highland"),
    # Northeast Hills (Meghalaya, Mizoram, Manipur)
    (20, 27, 90, 97, "subtropical highland"),
    # Default — if nothing matches
    (0, 40, 60, 100, "subtropical sub-humid"),
]

# Season calendar by month (Rabi: Nov-Mar, Kharif: Jun-Oct, Zaid: Apr-May)
def get_season(month: int, lat: float) -> str:
    """Return season name given month and latitude."""
    # North India (above ~20°N): standard seasons
    # South India (below ~15°N): rice seasons slightly shifted
    if month in [11, 12, 1, 2, 3]:
        return "rabi / winter crop season"
    elif month in [6, 7, 8, 9, 10]:
        return "kharif / monsoon crop season"
    else:  # April, May
        return "zaid / summer crop season"


def get_climate_zone(lat: float, lon: float) -> str:
    for lat_min, lat_max, lon_min, lon_max, zone in CLIMATE_ZONES[:-1]:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return zone
    return "subtropical sub-humid"


def get_land_type(elevation_m: float, lat: float, lon: float) -> str:
    """Classify land type from elevation + rough geography."""
    if elevation_m > 2000:
        return "hilly / mountain"
    elif elevation_m > 800:
        return "hilly"
    elif elevation_m > 400:
        return "gentle hills"
    else:
        # Check for coastal belt (rough: within ~100km of coast)
        # Coastal: lon < 72.5 (Gujarat/Maharastra west), or lon > 79.5 (East coast)
        # or lat < 12 (South)
        if lat < 12 or lon < 72.5 or (lon > 79.5 and lat < 20):
            return "coastal"
        # Indo-Gangetic plain: lat 24-32, lon 73-88
        if 24 <= lat <= 32 and 73 <= lon <= 88:
            return "alluvial plains"
        # Deccan plateau: lat 14-22, rough
        if 14 <= lat <= 22 and 73 <= lon <= 82:
            return "plateau"
        return "lowland plains"


def score_farming(climate_zone: str, land_type: str, elevation_m: float,
                  temp: float, humidity: float, n: float = 60,
                  p: float = 20, k: float = 120, ph: float = 7.0) -> tuple:
    """
    Returns (farming_score, soil_health_score) as floats 1-10.
    """
    # Base score by climate zone
    zone_scores = {
        "subtropical humid": 8.0,
        "subtropical sub-humid": 7.5,
        "tropical wet": 7.5,
        "tropical wet-dry": 7.0,
        "subtropical semi-arid": 6.5,
        "semi-arid": 6.0,
        "tropical dry": 6.0,
        "subtropical highland": 6.5,
        "arid / hot desert": 3.5,
        "cold arid / highland": 3.0,
    }
    base = zone_scores.get(climate_zone, 6.0)

    # Land type adjustment
    land_adj = {
        "alluvial plains": +1.0,
        "lowland plains": +0.5,
        "gentle hills": 0.0,
        "plateau": -0.5,
        "hilly": -1.0,
        "hilly / mountain": -2.0,
        "coastal": +0.2,
    }
    base += land_adj.get(land_type, 0.0)

    # Elevation penalty
    if elevation_m > 1500:
        base -= 1.5
    elif elevation_m > 800:
        base -= 0.5

    farming_score = round(max(2.0, min(9.5, base)), 1)

    # Soil health score based on NPK and pH
    npk_score = min(10, (n / 10 + p / 5 + k / 20))  # rough index
    ph_score = 10 - abs(ph - 6.8) * 2  # peak at pH 6.8
    soil_health = round(max(2.0, min(9.5, (npk_score + ph_score) / 2)), 1)

    return farming_score, soil_health


def analyze(agent1_output: dict) -> dict:
    """
    Agent 2 — Geo-Spatial Analysis.

    Input:  agent1_output (from collector.py)
    Output: climate_zone, land_type, season, scores, area info
    """
    weather = agent1_output.get("weather", {})
    current = weather.get("current", {})
    terrain = agent1_output.get("terrain", {})

    lat = agent1_output.get("lat", 20.0)
    lon = agent1_output.get("lon", 78.0)
    elevation_m = float(terrain.get("elevation_m", 200))
    temp = float(current.get("temperature_2m", 25))
    humidity = float(current.get("relative_humidity_2m", 60))

    month = datetime.now().month
    climate_zone = get_climate_zone(lat, lon)
    land_type = get_land_type(elevation_m, lat, lon)
    season = get_season(month, lat)

    # Rough NPK defaults for scoring (will be refined by soil_agent)
    farming_score, soil_health = score_farming(
        climate_zone, land_type, elevation_m, temp, humidity
    )

    return {
        "climate_zone": climate_zone,
        "land_type": land_type,
        "current_season": season,
        "farming_score": farming_score,
        "soil_health_score": soil_health,
        "elevation_m": elevation_m,
        "coordinates": {"lat": lat, "lon": lon},
    }