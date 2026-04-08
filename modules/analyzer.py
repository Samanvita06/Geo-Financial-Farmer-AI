# Agent 2 — Geo-Spatial Analyzer
# Input:  Agent 1 output dict
# Output: climate zone, land type, soil suitability, NPK estimate, pH estimate, season

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

    climate_zone   = classify_climate(temp, humidity, weekly_rain)
    land_type      = classify_land(elevation)
    soil_type      = classify_soil(climate_zone, land_type, elevation)
    season         = classify_season(temp, weekly_rain)
    npk            = estimate_npk(climate_zone, land_type, elevation, weekly_rain)
    ph             = estimate_ph(climate_zone, land_type, elevation)
    micronutrients = estimate_micronutrients(climate_zone, land_type)
    farming_score  = calc_farming_score(temp, humidity, weekly_rain, elevation)
    soil_health    = calc_soil_health(npk, ph)
    print("DEBUG NPK:", npk)

    return {
        "climate_zone":    climate_zone,
        "land_type":       land_type,
        "soil_type":       soil_type,
        "current_season":  season,
        "farming_score":   farming_score,
        "soil_health_score": soil_health,
        "soil_minerals": {
            "nitrogen":    npk["N"],
            "phosphorus":  npk["P"],
            "potassium":   npk["K"],
            "pH":          ph,
            "micronutrients": micronutrients
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
        return "black cotton soil — excellent for cotton, soybean"
    elif "highland" in land_type or "plateau" in land_type:
        return "red loamy soil — moderate fertility, good for millets, pulses"
    elif "mountainous" in land_type:
        return "rocky / thin topsoil — limited farming, needs heavy composting"
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


# ── Soil Mineral Estimators ──────────────────────────────────────

def estimate_npk(climate_zone, land_type, elevation, weekly_rain):
    """
    Return numeric NPK values (kg/ha)
    """

    # Nitrogen (N)
    if "tropical wet" in climate_zone and weekly_rain > 20:
        N = 50   # leached by rain
    elif "arid" in climate_zone:
        N = 30
    elif "subtropical" in climate_zone and "plains" in land_type:
        N = 80
    elif "mountainous" in land_type:
        N = 25
    else:
        N = 60

    # Phosphorus (P)
    if "lowland" in land_type and "tropical" in climate_zone:
        P = 60
    elif "arid" in climate_zone:
        P = 40
    elif "mountainous" in land_type or elevation > 1500:
        P = 20
    else:
        P = 45

    # Potassium (K)
    if "black cotton" in classify_soil(climate_zone, land_type, elevation):
        K = 80
    elif "arid" in climate_zone:
        K = 70
    elif weekly_rain > 30:
        K = 30
    else:
        K = 50

    return {"N": N, "P": P, "K": K}


def estimate_ph(climate_zone, land_type, elevation):
    """
    Estimate soil pH range based on climate and land type
    Most crops prefer 6.0 - 7.5
    """
    if "tropical wet" in climate_zone:
        return "5.0 - 6.0 (acidic)"       # heavy rain makes soil acidic
    elif "arid" in climate_zone:
        return "7.5 - 8.5 (alkaline)"     # dry soils accumulate salts
    elif "subtropical" in climate_zone and "plains" in land_type:
        return "6.5 - 8.0 (neutral to alkaline)"
    elif "mountainous" in land_type or elevation > 1500:
        return "4.5 - 6.0 (acidic)"       # high elevation = acidic
    elif "highland" in land_type:
        return "5.5 - 6.5 (slightly acidic)"
    else:
        return "6.0 - 7.5 (neutral)"      # ideal for most crops


def estimate_micronutrients(climate_zone, land_type):
    """
    Estimate micronutrient availability
    """
    nutrients = []

    if "tropical" in climate_zone:
        nutrients.append("Iron: high")
        nutrients.append("Manganese: medium")
        nutrients.append("Zinc: low (leached by rain)")
    elif "arid" in climate_zone:
        nutrients.append("Iron: low")
        nutrients.append("Zinc: medium")
        nutrients.append("Boron: high")
    elif "subtropical" in climate_zone:
        nutrients.append("Iron: medium")
        nutrients.append("Zinc: medium")
        nutrients.append("Copper: medium")
    else:
        nutrients.append("Iron: medium")
        nutrients.append("Zinc: medium")
        nutrients.append("Manganese: medium")

    if "lowland" in land_type:
        nutrients.append("Calcium: high")
        nutrients.append("Magnesium: medium")
    elif "mountainous" in land_type:
        nutrients.append("Calcium: low")
        nutrients.append("Magnesium: low")
    else:
        nutrients.append("Calcium: medium")
        nutrients.append("Magnesium: medium")

    return nutrients


# ── Score Calculators ────────────────────────────────────────────

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


def calc_soil_health(npk, ph):
    score = 5.0

    # SAFE extraction
    N = npk.get("N") or npk.get("nitrogen") or 50
    P = npk.get("P") or npk.get("phosphorus") or 50
    K = npk.get("K") or npk.get("potassium") or 50

    # numeric scoring
    score += (N / 100) * 2
    score += (P / 100) * 1.5
    score += (K / 100) * 1.2

    if isinstance(ph, str):
        if "neutral" in ph:
            score += 1.5
        elif "slightly acidic" in ph:
            score += 1.0
        elif "acidic" in ph:
            score += 0.3
        elif "alkaline" in ph:
            score += 0.5

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