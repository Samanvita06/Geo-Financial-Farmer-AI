"""
soil_agent.py — Rewritten with region/terrain-aware Indian soil profiles.

Root cause of original issues:
  - NPK values were plausible but not location-aware
  - Crop recommendations did not account for season
  - Same crops recommended regardless of climate zone

Data sources:
  - ICAR soil health card database averages by soil type
  - NBSS&LUP (National Bureau of Soil Survey and Land Use Planning)
  - State soil health card portal averages
"""

import math

# ─── Soil NPK profiles by terrain/land type ───────────────────────────────────
# Values in kg/ha (available N, P2O5, K2O)
# These are realistic averages; actual values require lab testing.

SOIL_PROFILES = {
    "alluvial plains": {
        "n_range": (65, 95),   # Indo-Gangetic alluvial: moderate-high N
        "p_range": (12, 25),   # kg/ha P2O5
        "k_range": (120, 200), # kg/ha K2O — alluvial soils are K-rich
        "ph_range": (7.0, 8.2),
        "texture": "loamy/silty",
        "oc_pct": 0.6,         # organic carbon %
        "description": "Indo-Gangetic alluvial — moderate fertility, good irrigation potential",
    },
    "lowland plains": {
        "n_range": (50, 80),
        "p_range": (10, 20),
        "k_range": (100, 180),
        "ph_range": (6.5, 7.8),
        "texture": "loamy",
        "oc_pct": 0.55,
        "description": "Lowland plains — moderate fertility",
    },
    "gentle hills": {
        "n_range": (55, 85),
        "p_range": (15, 35),
        "k_range": (80, 140),
        "ph_range": (5.8, 7.2),
        "texture": "sandy loam to clay loam",
        "oc_pct": 0.65,
        "description": "Gently sloping terrain — variable fertility, erosion risk moderate",
    },
    "plateau": {
        "n_range": (30, 65),
        "p_range": (8, 20),
        "k_range": (60, 120),
        "ph_range": (6.0, 7.5),
        "texture": "medium black / red laterite",
        "oc_pct": 0.45,
        "description": "Deccan/peninsular plateau — low-medium fertility, rainfed",
    },
    "hilly": {
        "n_range": (60, 100),
        "p_range": (20, 45),
        "k_range": (70, 120),
        "ph_range": (5.0, 6.8),
        "texture": "forest loam / laterite",
        "oc_pct": 1.2,
        "description": "Hilly terrain — high OM but steep slopes, limited cultivation",
    },
    "coastal": {
        "n_range": (40, 70),
        "p_range": (10, 22),
        "k_range": (80, 150),
        "ph_range": (5.5, 7.5),
        "texture": "sandy loam / coastal alluvial",
        "oc_pct": 0.50,
        "description": "Coastal — moderate fertility, salinity risk in some zones",
    },
}

DEFAULT_SOIL = SOIL_PROFILES["gentle hills"]

# ─── Crop-season-terrain suitability ─────────────────────────────────────────
# Returns recommended crops based on terrain + season + climate zone

CROP_RECOMMENDATIONS = {
    # (terrain_key, season_key) -> [crops in priority order]
    ("alluvial plains", "rabi"): ["wheat", "mustard", "chickpea", "potato", "lentil", "barley"],
    ("alluvial plains", "kharif"): ["rice", "corn", "soybean", "cotton", "groundnut", "sugarcane"],
    ("alluvial plains", "zaid"): ["moong", "sunflower", "corn", "vegetable crops"],

    ("lowland plains", "rabi"): ["wheat", "mustard", "chickpea", "lentil", "barley"],
    ("lowland plains", "kharif"): ["rice", "corn", "cotton", "soybean", "groundnut"],
    ("lowland plains", "zaid"): ["sunflower", "moong", "corn"],

    ("gentle hills", "rabi"): ["wheat", "mustard", "chickpea", "potato", "sunflower"],
    ("gentle hills", "kharif"): ["corn", "soybean", "cotton", "rice", "groundnut"],
    ("gentle hills", "zaid"): ["sunflower", "moong", "corn"],

    ("plateau", "rabi"): ["chickpea", "wheat", "lentil", "mustard", "sunflower"],
    ("plateau", "kharif"): ["jowar", "bajra", "soybean", "cotton", "groundnut"],
    ("plateau", "zaid"): ["sunflower", "moong", "groundnut"],

    ("hilly", "rabi"): ["wheat", "potato", "mustard", "lentil"],
    ("hilly", "kharif"): ["corn", "rice", "soybean", "ginger", "turmeric"],
    ("hilly", "zaid"): ["corn", "potato", "vegetables"],

    ("coastal", "rabi"): ["rice", "wheat", "mustard", "chickpea", "tomato", "onion"],
    ("coastal", "kharif"): ["rice", "cotton", "groundnut", "sugarcane", "banana"],
    ("coastal", "zaid"): ["rice", "moong", "vegetables"],
}


def _terrain_key(land_type: str) -> str:
    lt = (land_type or "").lower()
    if "alluvial" in lt:
        return "alluvial plains"
    if "lowland" in lt or ("plain" in lt and "gentle" not in lt):
        return "lowland plains"
    if "gentle" in lt or ("hill" in lt and "hilly" not in lt):
        return "gentle hills"
    if "plateau" in lt or "deccan" in lt or "black" in lt:
        return "plateau"
    if "hilly" in lt or "mountain" in lt or "hill" in lt:
        return "hilly"
    if "coastal" in lt or "delta" in lt:
        return "coastal"
    return "gentle hills"


def _season_key(temp: float, humidity: float) -> str:
    """
    Infer season from temperature if not explicitly provided.
    Nov-Mar (cool): rabi
    Jun-Sep (hot+humid): kharif
    Apr-May: zaid
    Oct: rabi transitioning
    """
    # Simple heuristic: use temp as proxy
    if temp < 20:
        return "rabi"
    elif temp > 30 and humidity > 60:
        return "kharif"
    else:
        return "zaid"


def _midpoint(range_tuple: tuple) -> float:
    lo, hi = range_tuple
    return round((lo + hi) / 2.0, 1)


def soil_agent(land_type: str, temp: float = 25.0, humidity: float = 60.0,
               season: str = None) -> dict:
    """
    Returns soil NPK estimates, pH, and crop recommendations for given terrain/season.

    Args:
        land_type: terrain description
        temp: temperature °C (used to infer season if not provided)
        humidity: relative humidity %
        season: season string override (e.g. "rabi / winter crop season")

    Returns:
        dict with n, p, k, ph, soil_type, recommended_crops
    """
    tk = _terrain_key(land_type)
    profile = SOIL_PROFILES.get(tk, DEFAULT_SOIL)

    # Derive season key
    if season:
        s_lower = season.lower()
        if "rabi" in s_lower:
            sk = "rabi"
        elif "kharif" in s_lower:
            sk = "kharif"
        elif "zaid" in s_lower or "summer" in s_lower:
            sk = "zaid"
        else:
            sk = _season_key(temp, humidity)
    else:
        sk = _season_key(temp, humidity)

    n = _midpoint(profile["n_range"])
    p = _midpoint(profile["p_range"])
    k = _midpoint(profile["k_range"])
    ph_mid = _midpoint(profile["ph_range"])

    # Minor temperature adjustment to pH (high temp + high humidity slightly acidifies)
    if temp > 28 and humidity > 75:
        ph_mid = round(ph_mid - 0.1, 2)

    crops = CROP_RECOMMENDATIONS.get((tk, sk),
            CROP_RECOMMENDATIONS.get(("gentle hills", "rabi")))[:5]

    return {
        "n": n,
        "p": p,
        "k": k,
        "ph": ph_mid,
        "soil_type": tk,
        "soil_texture": profile["texture"],
        "soil_description": profile["description"],
        "organic_carbon_pct": profile["oc_pct"],
        "recommended_crops": crops,
        "season_detected": sk,
    }
