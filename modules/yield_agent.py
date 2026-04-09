"""
yield_agent.py — Fixed with real-world Indian agronomic yield benchmarks.

Root cause of original bug:
  The original agent returned raw ML scores (0–100 range) directly as t/ha yields.
  Real Indian yields are 0.4–5 t/ha depending on crop, NOT 40–50 t/ha.

Sources:
  - ICAR (Indian Council of Agricultural Research) crop yield averages
  - Directorate of Economics & Statistics, Dept. of Agriculture, GoI
  - State agriculture department averages (2022-24)
"""

import math

# ─── Real-world Indian average yield benchmarks (t/ha) ────────────────────────
# Format: crop -> { terrain_key: (base_yield_t_ha, std_dev) }
# These are conservative realistic averages; high-input modern farming can achieve
# ~1.3x-1.5x these figures.

INDIA_YIELD_BENCHMARKS = {
    "wheat": {
        "alluvial plains":   (4.2, 0.5),   # Punjab/Haryana top belt
        "lowland plains":    (3.5, 0.5),
        "gentle hills":      (3.2, 0.4),   # Delhi NCR, UP hills
        "plateau":           (2.8, 0.4),   # Deccan
        "hilly":             (2.5, 0.4),
        "coastal":           (2.0, 0.3),   # not ideal
        "default":           (3.2, 0.5),
    },
    "rice": {
        "alluvial plains":   (3.8, 0.5),
        "lowland plains":    (3.5, 0.5),
        "gentle hills":      (2.8, 0.4),
        "plateau":           (2.5, 0.4),
        "hilly":             (2.2, 0.4),
        "coastal":           (3.6, 0.5),
        "default":           (3.0, 0.5),
    },
    "corn": {
        "alluvial plains":   (4.5, 0.6),
        "lowland plains":    (3.8, 0.5),
        "gentle hills":      (3.2, 0.5),
        "plateau":           (3.0, 0.4),
        "hilly":             (2.8, 0.4),
        "coastal":           (3.0, 0.4),
        "default":           (3.2, 0.5),
    },
    "maize": {  # alias for corn
        "alluvial plains":   (4.5, 0.6),
        "lowland plains":    (3.8, 0.5),
        "gentle hills":      (3.2, 0.5),
        "plateau":           (3.0, 0.4),
        "hilly":             (2.8, 0.4),
        "coastal":           (3.0, 0.4),
        "default":           (3.2, 0.5),
    },
    "cotton": {
        # Cotton is kharif (Jun-Nov). In rabi/winter it is off-season in most of India.
        # Yields given as seed cotton (kapas), NOT lint.
        "alluvial plains":   (2.0, 0.3),   # Gujarat/Maharashtra irrigated
        "lowland plains":    (1.8, 0.3),
        "gentle hills":      (1.2, 0.3),   # Poor fit — Rabi season
        "plateau":           (1.5, 0.3),
        "hilly":             (0.8, 0.2),
        "coastal":           (1.0, 0.2),
        "default":           (1.5, 0.3),
    },
    "soybean": {
        # Kharif crop — peak in Maharashtra/MP
        "alluvial plains":   (1.8, 0.3),
        "lowland plains":    (1.5, 0.3),
        "gentle hills":      (1.2, 0.2),
        "plateau":           (1.4, 0.3),
        "hilly":             (1.0, 0.2),
        "coastal":           (1.0, 0.2),
        "default":           (1.3, 0.2),
    },
    "sunflower": {
        "alluvial plains":   (1.4, 0.2),
        "lowland plains":    (1.2, 0.2),
        "gentle hills":      (1.0, 0.2),
        "plateau":           (1.1, 0.2),
        "hilly":             (0.8, 0.2),
        "coastal":           (0.9, 0.2),
        "default":           (1.0, 0.2),
    },
    "groundnut": {
        "alluvial plains":   (2.2, 0.3),
        "lowland plains":    (1.8, 0.3),
        "gentle hills":      (1.5, 0.3),
        "plateau":           (1.6, 0.3),
        "hilly":             (1.2, 0.2),
        "coastal":           (1.7, 0.3),
        "default":           (1.6, 0.3),
    },
    "mustard": {
        "alluvial plains":   (1.8, 0.3),
        "lowland plains":    (1.6, 0.3),
        "gentle hills":      (1.4, 0.2),
        "plateau":           (1.2, 0.2),
        "hilly":             (1.0, 0.2),
        "coastal":           (1.0, 0.2),
        "default":           (1.4, 0.3),
    },
    "sugarcane": {
        # t/ha of cane (not sugar). Sugarcane is perennial; yields are annual.
        "alluvial plains":   (75.0, 10.0),
        "lowland plains":    (68.0, 10.0),
        "gentle hills":      (55.0, 8.0),
        "plateau":           (60.0, 8.0),
        "hilly":             (45.0, 8.0),
        "coastal":           (70.0, 10.0),
        "default":           (65.0, 10.0),
    },
    "potato": {
        "alluvial plains":   (22.0, 3.0),
        "lowland plains":    (19.0, 3.0),
        "gentle hills":      (17.0, 3.0),
        "plateau":           (15.0, 3.0),
        "hilly":             (14.0, 3.0),
        "coastal":           (14.0, 3.0),
        "default":           (18.0, 3.0),
    },
    "tomato": {
        "alluvial plains":   (28.0, 5.0),
        "lowland plains":    (24.0, 4.0),
        "gentle hills":      (20.0, 4.0),
        "plateau":           (18.0, 3.0),
        "hilly":             (15.0, 3.0),
        "coastal":           (22.0, 4.0),
        "default":           (22.0, 4.0),
    },
    "onion": {
        "alluvial plains":   (18.0, 3.0),
        "lowland plains":    (16.0, 3.0),
        "gentle hills":      (13.0, 2.0),
        "plateau":           (14.0, 2.0),
        "hilly":             (11.0, 2.0),
        "coastal":           (13.0, 2.0),
        "default":           (15.0, 3.0),
    },
    "jowar": {
        "alluvial plains":   (1.8, 0.3),
        "lowland plains":    (1.5, 0.3),
        "gentle hills":      (1.2, 0.2),
        "plateau":           (1.3, 0.2),
        "hilly":             (1.0, 0.2),
        "coastal":           (1.1, 0.2),
        "default":           (1.3, 0.2),
    },
    "bajra": {
        "alluvial plains":   (2.0, 0.3),
        "lowland plains":    (1.8, 0.3),
        "gentle hills":      (1.5, 0.3),
        "plateau":           (1.6, 0.3),
        "hilly":             (1.2, 0.2),
        "coastal":           (1.4, 0.2),
        "default":           (1.6, 0.3),
    },
    "chickpea": {
        "alluvial plains":   (1.6, 0.3),
        "lowland plains":    (1.4, 0.2),
        "gentle hills":      (1.2, 0.2),
        "plateau":           (1.3, 0.2),
        "hilly":             (1.0, 0.2),
        "coastal":           (0.9, 0.2),
        "default":           (1.2, 0.2),
    },
    "lentil": {
        "alluvial plains":   (1.2, 0.2),
        "lowland plains":    (1.0, 0.2),
        "gentle hills":      (0.9, 0.2),
        "plateau":           (0.8, 0.2),
        "hilly":             (0.7, 0.1),
        "coastal":           (0.7, 0.1),
        "default":           (0.9, 0.2),
    },
}

# Season-suitability penalty multipliers
# If crop is off-season for the given season, yield is penalized
SEASON_SUITABILITY = {
    # (crop, season) -> multiplier
    # season strings from analyzer.py: "rabi / winter crop season", "kharif / monsoon crop season", "zaid / summer crop season"
    ("wheat",     "rabi"):   1.0,
    ("wheat",     "kharif"): 0.3,   # wheat in summer is very poor
    ("wheat",     "zaid"):   0.4,
    ("rice",      "kharif"): 1.0,
    ("rice",      "rabi"):   0.7,   # rabi rice possible in south
    ("rice",      "zaid"):   0.8,
    ("corn",      "kharif"): 1.0,
    ("corn",      "rabi"):   0.85,  # corn possible in rabi
    ("corn",      "zaid"):   0.9,
    ("maize",     "kharif"): 1.0,
    ("maize",     "rabi"):   0.85,
    ("maize",     "zaid"):   0.9,
    ("cotton",    "kharif"): 1.0,
    ("cotton",    "rabi"):   0.5,   # cotton off-season in rabi
    ("cotton",    "zaid"):   0.6,
    ("soybean",   "kharif"): 1.0,
    ("soybean",   "rabi"):   0.55,
    ("soybean",   "zaid"):   0.65,
    ("sunflower", "rabi"):   0.95,  # sunflower suits rabi/zaid
    ("sunflower", "kharif"): 0.9,
    ("sunflower", "zaid"):   1.0,
    ("groundnut", "kharif"): 1.0,
    ("groundnut", "rabi"):   0.75,
    ("groundnut", "zaid"):   0.8,
    ("mustard",   "rabi"):   1.0,
    ("mustard",   "kharif"): 0.4,
    ("mustard",   "zaid"):   0.5,
    ("sugarcane", "kharif"): 1.0,
    ("sugarcane", "rabi"):   0.9,
    ("sugarcane", "zaid"):   0.95,
    ("potato",    "rabi"):   1.0,
    ("potato",    "kharif"): 0.6,
    ("potato",    "zaid"):   0.7,
    ("tomato",    "rabi"):   1.0,
    ("tomato",    "kharif"): 0.8,
    ("tomato",    "zaid"):   0.9,
    ("onion",     "rabi"):   1.0,
    ("onion",     "kharif"): 0.75,
    ("onion",     "zaid"):   0.85,
    ("jowar",     "kharif"): 1.0,
    ("jowar",     "rabi"):   0.9,
    ("bajra",     "kharif"): 1.0,
    ("bajra",     "rabi"):   0.7,
    ("chickpea",  "rabi"):   1.0,
    ("chickpea",  "kharif"): 0.5,
    ("lentil",    "rabi"):   1.0,
    ("lentil",    "kharif"): 0.4,
}


def _get_season_key(season_str: str) -> str:
    """Extract season key (rabi/kharif/zaid) from full season string."""
    s = (season_str or "").lower()
    if "rabi" in s:
        return "rabi"
    elif "kharif" in s:
        return "kharif"
    elif "zaid" in s or "summer" in s:
        return "zaid"
    return "rabi"  # default


def _terrain_key(land_type: str) -> str:
    """Normalise land_type string to a benchmark key."""
    lt = (land_type or "").lower()
    if "alluvial" in lt:
        return "alluvial plains"
    if "lowland" in lt or "plain" in lt:
        return "lowland plains"
    if "gentle" in lt or "hill" in lt:
        return "gentle hills"
    if "plateau" in lt or "deccan" in lt:
        return "plateau"
    if "hilly" in lt or "mountain" in lt:
        return "hilly"
    if "coastal" in lt or "delta" in lt:
        return "coastal"
    return "default"


def _compute_yield(crop: str, land_type: str, temp: float, humidity: float,
                   n: float, p: float, k: float, ph: float,
                   season_str: str) -> float:
    """
    Return realistic yield in t/ha.

    Adjustments applied on top of benchmark:
    - Season suitability: ±0–50% depending on crop/season fit
    - Temperature stress: slight penalty if outside 15-35°C sweet spot
    - NPK adequacy: slight penalty if nutrients are very low
    - pH adequacy: slight penalty if pH < 5.5 or > 8.0
    All adjustments are capped so output never exceeds 1.5× benchmark or falls below 0.3× benchmark.
    """
    crop_l = crop.lower().strip()
    benchmarks = INDIA_YIELD_BENCHMARKS.get(crop_l, INDIA_YIELD_BENCHMARKS.get("wheat"))
    terrain = _terrain_key(land_type)
    base, std = benchmarks.get(terrain, benchmarks["default"])

    # Season suitability multiplier
    season_key = _get_season_key(season_str)
    season_mult = SEASON_SUITABILITY.get((crop_l, season_key), 0.85)

    # Temperature multiplier (optimal range varies but 18-32°C suits most crops)
    if 18 <= temp <= 32:
        temp_mult = 1.0
    elif 10 <= temp < 18 or 32 < temp <= 38:
        temp_mult = 0.92
    else:
        temp_mult = 0.80

    # NPK adequacy multiplier (low NPK = lower yields)
    npk_avg = (n + p + k) / 3.0
    if npk_avg >= 60:
        npk_mult = 1.0
    elif npk_avg >= 40:
        npk_mult = 0.95
    elif npk_avg >= 25:
        npk_mult = 0.88
    else:
        npk_mult = 0.80

    # pH multiplier (ideal 6.0-7.5)
    if 6.0 <= ph <= 7.5:
        ph_mult = 1.0
    elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
        ph_mult = 0.95
    else:
        ph_mult = 0.85

    final_yield = base * season_mult * temp_mult * npk_mult * ph_mult

    # Clamp: must be between 0.3× and 1.5× base
    final_yield = max(base * 0.3, min(base * 1.5, final_yield))

    return round(final_yield, 2)


def yield_agent(recommended_crops: list, land_type: str,
                temp: float = 25.0, humidity: float = 60.0,
                n: float = 50.0, p: float = 40.0, k: float = 40.0,
                ph: float = 6.5, season: str = "rabi") -> dict:
    """
    Returns realistic yield predictions for a list of recommended crops.

    Args:
        recommended_crops: list of crop name strings
        land_type: terrain description (e.g. "gentle hills", "alluvial plains")
        temp: current temperature in °C
        humidity: relative humidity %
        n, p, k: soil NPK in kg/ha
        ph: soil pH
        season: season string e.g. "rabi / winter crop season"

    Returns:
        dict with best_crop, estimated_yield, confidence, all_predictions
    """
    if not recommended_crops:
        return {
            "best_crop": "—",
            "estimated_yield": "0 t/ha",
            "confidence": 0,
            "all_predictions": {},
        }

    predictions = {}
    for crop in recommended_crops:
        y = _compute_yield(crop, land_type, temp, humidity, n, p, k, ph, season)
        predictions[crop.lower()] = y

    # Best crop = highest yield
    best_crop = max(predictions, key=predictions.get)
    best_yield = predictions[best_crop]

    # Confidence: higher when season suitability is good and NPK is adequate
    season_key = _get_season_key(season)
    best_season_mult = SEASON_SUITABILITY.get((best_crop, season_key), 0.85)
    confidence = int(min(92, max(55, 75 * best_season_mult + 10)))

    return {
        "best_crop": best_crop,
        "estimated_yield": f"{best_yield} t/ha",
        "confidence": confidence,
        "all_predictions": {c: f"{v} t/ha" for c, v in predictions.items()},
        "_raw_yields_t_ha": predictions,  # numeric version for financial_agent
    }
