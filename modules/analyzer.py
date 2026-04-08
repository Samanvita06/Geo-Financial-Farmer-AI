# Agent 2 — Geo-Spatial Analyzer
# Input:  Agent 1 output dict
# Output: climate zone, land type, soil suitability hint, season info

def analyze(agent1_output: dict) -> dict:
    terrain  = agent1_output.get("terrain", {})
    weather  = agent1_output.get("weather", {}).get("current", {})
    forecast = agent1_output.get("weather", {}).get("weekly_forecast", {})
    location = agent1_output.get("location", {})
    region   = agent1_output.get("selected_region", {})

    elevation   = terrain.get("elevation_m", 0) or 0
    temp        = weather.get("temperature_2m", 25) or 25
    humidity    = weather.get("relative_humidity_2m", 50) or 50
    precip      = weather.get("precipitation", 0) or 0
    weekly_rain = sum(forecast.get("precipitation_sum", [0])) or 0

    climate_zone  = classify_climate(temp, humidity, weekly_rain)
    land_type     = classify_land(elevation)
    soil_hint     = classify_soil(climate_zone, land_type, elevation)
    season        = classify_season(temp, weekly_rain)
    mineral_hint  = classify_mineral(elevation, land_type)
    farming_score = calc_farming_score(temp, humidity, weekly_rain, elevation)
    mineral_score = calc_mineral_score(elevation, land_type)

    return {
        "climate_zone":    climate_zone,
        "land_type":       land_type,
        "soil_hint":       soil_hint,
        "current_season":  season,
        "mineral_hint":    mineral_hint,
        "farming_score":   farming_score,   # out of 10
        "mineral_score":   mineral_score,   # out of 10
        "raw": {
            "elevation_m":   elevation,
            "temperature_c": temp,
            "humidity_pct":  humidity,
            "weekly_rain_mm": weekly_rain
        }
    }


# ── Classifiers ──────────────────────────────────────────────────

def classify_climate(temp, humidity, weekly_rain):
    if temp > 25 and humidity > 70 and weekly_rain > 20:
        return "tropical wet"
    elif temp > 25 and humidity < 50 and weekly_rain < 5:
        return "arid / semi-arid"
    elif temp > 20 and humidity > 50:
        return "tropical dry"
    elif 10 < temp <= 20 and humidity > 60:
        return "subtropical humid"
    elif 10 < temp <= 20:
        return "subtropical dry"
    elif temp <= 10 and temp > 0:
        return "temperate / cool"
    else:
        return "alpine / cold"


def classify_land(elevation):
    if elevation < 200:
        return "lowland plains"
    elif elevation < 500:
        return "gentle hills"
    elif elevation < 1000:
        return "upland plateau"
    elif elevation < 2000:
        return "highland"
    else:
        return "mountainous"


def classify_soil(climate_zone, land_type, elevation):
    if "tropical wet" in climate_zone and "lowland" in land_type:
        return "laterite / alluvial — high organic matter, good for rice, sugarcane"
    elif "arid" in climate_zone:
        return "sandy / loamy — low moisture retention, needs irrigation"
    elif "subtropical" in climate_zone and "plains" in land_type:
        return "black cotton soil / regur — excellent for cotton, soybean"
    elif "highland" in land_type or "plateau" in land_type:
        return "red loamy soil — moderate fertility, good for millets, pulses"
    elif "mountainous" in land_type:
        return "rocky / thin topsoil — limited farming, mineral-rich"
    else:
        return "mixed loamy soil — moderate fertility, versatile"


def classify_season(temp, weekly_rain):
    if temp > 28 and weekly_rain > 15:
        return "kharif / monsoon season"
    elif temp > 25 and weekly_rain < 5:
        return "summer / pre-monsoon"
    elif 15 < temp <= 25 and weekly_rain < 10:
        return "rabi / winter crop season"
    elif temp <= 15:
        return "winter / cold season"
    else:
        return "transition / inter-season"


def classify_mineral(elevation, land_type):
    if "mountainous" in land_type or elevation > 1500:
        return "high — likely iron ore, bauxite, granite deposits"
    elif "highland" in land_type or elevation > 800:
        return "moderate — possible limestone, manganese, mica"
    elif "plateau" in land_type:
        return "moderate — possible coal, iron ore, chromite"
    elif "lowland" in land_type:
        return "low — mostly sedimentary, possible sand/gravel"
    else:
        return "low to moderate — survey recommended"


def calc_farming_score(temp, humidity, weekly_rain, elevation):
    score = 5.0
    if 20 <= temp <= 30:   score += 2
    elif 15 <= temp < 20:  score += 1
    elif temp > 35:        score -= 1
    if humidity > 60:      score += 1
    if weekly_rain > 10:   score += 1
    elif weekly_rain < 2:  score -= 1
    if elevation < 500:    score += 1
    elif elevation > 1500: score -= 1
    return round(min(max(score, 0), 10), 1)


def calc_mineral_score(elevation, land_type):
    score = 3.0
    if elevation > 1500:              score += 4
    elif elevation > 800:             score += 3
    elif elevation > 400:             score += 2
    if "mountainous" in land_type:    score += 2
    elif "highland" in land_type:     score += 1
    elif "plateau" in land_type:      score += 1
    return round(min(max(score, 0), 10), 1)


if __name__ == "__main__":
    # Quick test with dummy Agent 1 output
    dummy = {
        "terrain": {"elevation_m": 920, "terrain_note": "upland / plateau"},
        "weather": {
            "current": {
                "temperature_2m": 27,
                "relative_humidity_2m": 65,
                "precipitation": 2.0,
                "windspeed_10m": 10
            },
            "weekly_forecast": {
                "precipitation_sum": [1, 3, 0, 5, 2, 0, 4]
            }
        },
        "location": {"name": "Bangalore"},
        "selected_region": {"area_km2": 12.5}
    }

    import json
    result = analyze(dummy)
    print(json.dumps(result, indent=2))