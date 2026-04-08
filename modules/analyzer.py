
# Agent 2 — Geo-Spatial Analyzer
# Input:  Agent 1 output dict
# Output: climate zone, land type, season, farming score, soil health score, soil NPK+pH

import re

def analyze(agent1_output: dict) -> dict:
    terrain  = agent1_output.get("terrain", {})
    weather  = agent1_output.get("weather", {}).get("current", {})
    forecast = agent1_output.get("weather", {}).get("weekly_forecast", {})

    elevation   = terrain.get("elevation_m", 0) or 0
    temp        = weather.get("temperature_2m", 25) or 25
    humidity    = weather.get("relative_humidity_2m", 50) or 50
    weekly_rain = sum(forecast.get("precipitation_sum", [0])) or 0

    climate_zone  = classify_climate(temp, humidity, weekly_rain)
    land_type     = classify_land(elevation)
    season        = classify_season(temp, weekly_rain)
    npk           = estimate_npk(climate_zone, land_type, elevation, weekly_rain)
    ph            = estimate_ph(climate_zone, land_type, elevation)
    farming_score = calc_farming_score(temp, humidity, weekly_rain, elevation)
    soil_health   = calc_soil_health_score(temp, humidity, weekly_rain, elevation)

    return {
        "climate_zone":      climate_zone,
        "land_type":         land_type,
        "current_season":    season,
        "farming_score":     farming_score,
        "soil_health_score": soil_health,
        "soil": {
            "n":  npk["N"],
            "p":  npk["P"],
            "k":  npk["K"],
            "ph": ph,
        },
        "raw": {
            "elevation_m":    elevation,
            "temperature_c":  temp,
            "humidity_pct":   humidity,
            "weekly_rain_mm": weekly_rain
        }
    }


# ── Classifiers ──────────────────────────────────────────────────

def classify_climate(temp, humidity, weekly_rain):
    if temp > 25 and humidity > 70 and weekly_rain > 20:
        return "tropical wet"
    elif temp > 25 and humidity < 50 and weekly_rain < 5:
        return "arid / semi-arid"
    elif temp > 25 and humidity > 50:
        return "tropical dry"
    elif 10 < temp <= 20 and humidity > 60:
        return "subtropical humid"
    elif 10 < temp <= 20:
        return "subtropical dry"
    elif 0 < temp <= 10:
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


# ── Soil Estimators ───────────────────────────────────────────────

def estimate_npk(climate_zone, land_type, elevation, weekly_rain):
    if "tropical wet" in climate_zone and weekly_rain > 20:
        N = 50
    elif "arid" in climate_zone:
        N = 30
    elif "subtropical" in climate_zone and "plains" in land_type:
        N = 80
    elif "mountainous" in land_type:
        N = 25
    else:
        N = 60

    if "lowland" in land_type and "tropical" in climate_zone:
        P = 60
    elif "arid" in climate_zone:
        P = 40
    elif "mountainous" in land_type or elevation > 1500:
        P = 20
    else:
        P = 45

    if "arid" in climate_zone:
        K = 70
    elif weekly_rain > 30:
        K = 30
    else:
        K = 50

    return {"N": N, "P": P, "K": K}


def estimate_ph(climate_zone, land_type, elevation):
    if "tropical wet" in climate_zone:
        ph = 5.5
    elif "arid" in climate_zone:
        ph = 8.0
    elif "subtropical" in climate_zone and "plains" in land_type:
        ph = 7.2
    elif "mountainous" in land_type or elevation > 1500:
        ph = 5.2
    elif "highland" in land_type:
        ph = 6.0
    else:
        ph = 6.5
    return ph


# ── Score Calculators ─────────────────────────────────────────────

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


def calc_soil_health_score(temp, humidity, weekly_rain, elevation):
    score = 5.0
    if 20 <= temp <= 30:        score += 1.5
    elif 15 <= temp < 20:       score += 0.8
    elif temp > 35:             score -= 1.0
    if humidity >= 70:          score += 1.2
    elif humidity >= 50:        score += 0.6
    else:                       score -= 0.5
    if 10 <= weekly_rain <= 30: score += 1.0
    elif weekly_rain > 30:      score -= 0.5
    elif weekly_rain < 3:       score -= 0.8
    if elevation < 300:         score += 0.8
    elif elevation < 800:       score += 0.3
    elif elevation > 1500:      score -= 0.8
    return round(min(max(score, 0), 10), 1)


if __name__ == "__main__":
    import json
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
    result = analyze(dummy)
    print(json.dumps(result, indent=2))