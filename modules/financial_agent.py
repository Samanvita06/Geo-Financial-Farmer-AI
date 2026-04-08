"""
Agent 6 — Financial Intelligence
Combines outputs from:
  - Agent 2 (geo-spatial): region, area_km2, land_type, climate_zone
  - Agent 3 (soil):        best crop, N/P/K, soil_type
  - Agent 4 (yield):       estimated_yield (tonnes/ha), best_crop
  - Agent 5 (marketing):   current_wpi, historical_avg, yoy_change_pct

Produces per-crop financial projection:
  {
    "crop":          str,
    "area_hectare":  float,
    "total_cost":    float,   # INR
    "revenue":       float,   # INR
    "profit":        float,   # INR
    "roi_pct":       float,
    "cost_breakdown": {...},
    "assumptions":   {...},
  }
"""

from __future__ import annotations
import math

# ---------------------------------------------------------------------------
# Static cost tables  (INR per hectare, 2024-25 estimates for India)
# These are defaults; WPI index is used to scale market price dynamically.
# ---------------------------------------------------------------------------

CROP_COST_TABLE: dict[str, dict] = {
    # Seeds, fertiliser, labour, irrigation, pesticide, misc (INR/ha)
    "rice":      {"seed": 2500,  "fertiliser": 6000,  "labour": 12000, "irrigation": 4000, "pesticide": 3000, "misc": 2000},
    "wheat":     {"seed": 3000,  "fertiliser": 5500,  "labour": 10000, "irrigation": 3500, "pesticide": 2000, "misc": 1500},
    "maize":     {"seed": 2000,  "fertiliser": 5000,  "labour": 9000,  "irrigation": 2500, "pesticide": 2500, "misc": 1500},
    "potato":    {"seed": 15000, "fertiliser": 8000,  "labour": 18000, "irrigation": 5000, "pesticide": 4000, "misc": 3000},
    "onion":     {"seed": 3000,  "fertiliser": 7000,  "labour": 20000, "irrigation": 6000, "pesticide": 3500, "misc": 2500},
    "tomato":    {"seed": 5000,  "fertiliser": 9000,  "labour": 25000, "irrigation": 8000, "pesticide": 5000, "misc": 3000},
    "cotton":    {"seed": 4000,  "fertiliser": 7500,  "labour": 14000, "irrigation": 5000, "pesticide": 6000, "misc": 2500},
    "sugarcane": {"seed": 8000,  "fertiliser": 10000, "labour": 20000, "irrigation": 9000, "pesticide": 3000, "misc": 3000},
    "soybean":   {"seed": 3500,  "fertiliser": 5000,  "labour": 8000,  "irrigation": 2000, "pesticide": 2500, "misc": 1500},
    "groundnut": {"seed": 5000,  "fertiliser": 5500,  "labour": 12000, "irrigation": 3000, "pesticide": 3000, "misc": 2000},
    "bajra":     {"seed": 1500,  "fertiliser": 4000,  "labour": 7000,  "irrigation": 1500, "pesticide": 1500, "misc": 1000},
    "jowar":     {"seed": 1500,  "fertiliser": 4000,  "labour": 7000,  "irrigation": 1500, "pesticide": 1500, "misc": 1000},
    "gram":      {"seed": 4000,  "fertiliser": 4500,  "labour": 8000,  "irrigation": 2000, "pesticide": 2000, "misc": 1500},
    "tur":       {"seed": 3500,  "fertiliser": 4500,  "labour": 8000,  "irrigation": 2000, "pesticide": 2000, "misc": 1500},
    "urad":      {"seed": 3500,  "fertiliser": 4000,  "labour": 7500,  "irrigation": 1500, "pesticide": 2000, "misc": 1500},
    "moong":     {"seed": 4000,  "fertiliser": 4000,  "labour": 7500,  "irrigation": 1500, "pesticide": 2000, "misc": 1500},
    "lentil":    {"seed": 3500,  "fertiliser": 4000,  "labour": 7000,  "irrigation": 1500, "pesticide": 1500, "misc": 1000},
    "barley":    {"seed": 2000,  "fertiliser": 4000,  "labour": 7000,  "irrigation": 1500, "pesticide": 1500, "misc": 1000},
    "sunflower": {"seed": 3000,  "fertiliser": 5000,  "labour": 9000,  "irrigation": 2500, "pesticide": 2000, "misc": 1500},
    "rapeseed & mustard": {"seed": 2500, "fertiliser": 5000, "labour": 8000, "irrigation": 2000, "pesticide": 2000, "misc": 1500},
    "sesamum":   {"seed": 2000,  "fertiliser": 4000,  "labour": 8000,  "irrigation": 1500, "pesticide": 2000, "misc": 1500},
    "linseed":   {"seed": 2000,  "fertiliser": 4000,  "labour": 7000,  "irrigation": 1500, "pesticide": 1500, "misc": 1000},
    "tobacco":   {"seed": 6000,  "fertiliser": 8000,  "labour": 22000, "irrigation": 6000, "pesticide": 5000, "misc": 3000},
    "jute":      {"seed": 2500,  "fertiliser": 5000,  "labour": 15000, "irrigation": 3000, "pesticide": 2000, "misc": 2000},
    "default":   {"seed": 3000,  "fertiliser": 5500,  "labour": 10000, "irrigation": 3000, "pesticide": 2500, "misc": 2000},
}

# Base yield (tonnes/ha) if yield agent gives no numeric value
BASE_YIELD_TABLE: dict[str, float] = {
    "rice": 3.5, "wheat": 3.2, "maize": 4.0, "potato": 20.0, "onion": 18.0,
    "tomato": 25.0, "cotton": 1.5, "sugarcane": 65.0, "soybean": 1.8,
    "groundnut": 2.0, "bajra": 1.8, "jowar": 1.5, "gram": 1.2, "tur": 1.0,
    "urad": 0.9, "moong": 0.9, "lentil": 1.0, "barley": 2.5, "sunflower": 1.2,
    "rapeseed & mustard": 1.4, "sesamum": 0.6, "linseed": 0.8, "tobacco": 1.5,
    "jute": 2.5, "default": 2.0,
}

# WPI base (2011-12 = 100), used to convert WPI index → approximate market price (INR/quintal)
# MSP 2024-25 at approx WPI index 200 for calibration
WPI_TO_PRICE_BASE: dict[str, float] = {
    # INR per quintal at WPI index 100
    "rice": 900, "wheat": 850, "maize": 700, "potato": 500, "onion": 600,
    "tomato": 800, "cotton": 4000, "sugarcane": 350, "soybean": 1800,
    "groundnut": 2500, "bajra": 700, "jowar": 900, "gram": 2500, "tur": 3000,
    "urad": 3000, "moong": 3000, "lentil": 2800, "barley": 700, "sunflower": 2000,
    "rapeseed & mustard": 2200, "sesamum": 5000, "linseed": 2500, "tobacco": 8000,
    "jute": 1800, "default": 1500,
}


def _km2_to_hectare(km2: float) -> float:
    return round(km2 * 100, 4)   # 1 km² = 100 ha


def _get_cost_per_ha(crop: str) -> dict:
    key = crop.lower()
    return CROP_COST_TABLE.get(key, CROP_COST_TABLE["default"])


def _get_base_yield(crop: str, yield_str: str | None) -> float:
    """Parse yield from Agent 4 string like '3.2 t/ha' or fall back to table."""
    if yield_str:
        # Try to extract first float from the string
        import re
        nums = re.findall(r"[\d.]+", str(yield_str))
        if nums:
            val = float(nums[0])
            # Sugarcane yields are in tonnes and typically 40-80 t/ha
            # Potato/onion/tomato also high; most others 1-5 t/ha
            if val > 0:
                return val
    key = crop.lower()
    return BASE_YIELD_TABLE.get(key, BASE_YIELD_TABLE["default"])


def _wpi_to_market_price(crop: str, current_wpi: float) -> float:
    """Convert WPI index value to INR/quintal market price."""
    key = crop.lower()
    base = WPI_TO_PRICE_BASE.get(key, WPI_TO_PRICE_BASE["default"])
    # price scales linearly with WPI (base=100)
    price = base * (current_wpi / 100.0)
    return round(price, 2)


def _project_single_crop(
    crop: str,
    area_ha: float,
    yield_str: str | None,
    current_wpi: float,
    historical_avg_wpi: float,
    yoy_change_pct: float,
) -> dict:
    cost_table  = _get_cost_per_ha(crop)
    cost_per_ha = sum(cost_table.values())
    total_cost  = round(cost_per_ha * area_ha, 2)

    yield_per_ha = _get_base_yield(crop, yield_str)          # tonnes/ha
    total_yield  = round(yield_per_ha * area_ha, 4)          # tonnes

    price_per_quintal = _wpi_to_market_price(crop, current_wpi)   # INR/quintal
    # 1 tonne = 10 quintals
    revenue = round(total_yield * 10 * price_per_quintal, 2)

    profit  = round(revenue - total_cost, 2)
    roi_pct = round((profit / total_cost * 100), 2) if total_cost > 0 else 0.0

    # Break-even yield (quintals/ha needed to cover cost)
    break_even_q = round(cost_per_ha / price_per_quintal, 2) if price_per_quintal > 0 else 0.0

    return {
        "crop":            crop.capitalize(),
        "area_hectare":    round(area_ha, 2),
        "yield_per_ha":    f"{yield_per_ha} t/ha",
        "total_yield":     f"{total_yield} tonnes",
        "price_per_quintal": round(price_per_quintal, 2),
        "total_cost":      total_cost,
        "revenue":         revenue,
        "profit":          profit,
        "roi_pct":         roi_pct,
        "break_even_yield": f"{break_even_q} q/ha",
        "cost_breakdown": {
            k: round(v * area_ha, 2) for k, v in cost_table.items()
        },
        "assumptions": {
            "wpi_used":          current_wpi,
            "historical_avg_wpi": historical_avg_wpi,
            "yoy_price_change":  f"{yoy_change_pct:+.1f}%",
            "yield_source":      "yield_agent" if yield_str else "default_table",
            "price_basis":       "WPI-scaled INR/quintal",
        },
    }


def financial_agent(
    agent2_output: dict,
    agent3_output: dict,
    agent4_output: dict,
    agent5_output: dict,
) -> dict:
    """
    Parameters
    ----------
    agent2_output : dict   from /analyze → agent2
    agent3_output : dict   from /analyze → agent3_soil
    agent4_output : dict   from /analyze → agent4_yield
    agent5_output : dict   from /analyze → agent5_marketing

    Returns
    -------
    dict  with projections for best crop + all recommended crops
    """
    # ── Area ────────────────────────────────────────────────────
    area_km2 = agent2_output.get("area_km2", 0)
    if not area_km2:
        # fallback: try bounds centroid area embedded in agent2
        area_km2 = agent2_output.get("selected_area_km2", 1.0)
    area_ha = _km2_to_hectare(float(area_km2)) if area_km2 else 1.0

    region       = agent2_output.get("climate_zone", "Unknown region")
    land_type    = agent2_output.get("land_type", "Unknown")
    season       = agent2_output.get("current_season", "Unknown")

    # ── Crops & Yields ──────────────────────────────────────────
    best_crop        = agent4_output.get("best_crop", "")
    estimated_yield  = agent4_output.get("estimated_yield", "")   # "3.2 t/ha"
    all_predictions  = agent4_output.get("all_predictions", {})   # {crop: "X t/ha"}
    recommended_crops = agent3_output.get("recommended_crops", [])

    if not recommended_crops and best_crop:
        recommended_crops = [best_crop]

    # ── Marketing prices ────────────────────────────────────────
    marketing_crops = agent5_output.get("crops", {})

    results = {}

    for crop in recommended_crops:
        # Find matching marketing data (case-insensitive)
        mkt = next(
            (v for k, v in marketing_crops.items() if k.lower() == crop.lower()),
            {}
        )
        current_wpi      = mkt.get("current_wpi", 150.0)
        hist_avg         = mkt.get("historical_avg", 130.0)
        yoy              = mkt.get("yoy_change_pct", 0.0)

        # Yield for this specific crop
        yield_str = (
            estimated_yield if crop.lower() == (best_crop or "").lower()
            else all_predictions.get(crop, all_predictions.get(crop.lower(), ""))
        )

        results[crop] = _project_single_crop(
            crop=crop,
            area_ha=area_ha,
            yield_str=yield_str,
            current_wpi=current_wpi,
            historical_avg_wpi=hist_avg,
            yoy_change_pct=yoy,
        )

    # ── Best financial pick ──────────────────────────────────────
    best_financial_crop = max(results, key=lambda c: results[c]["profit"]) if results else None

    # ── Portfolio summary (if you grow all crops equally split) ──
    if results:
        per_crop_ha = round(area_ha / len(results), 2)
        portfolio_revenue = sum(
            _project_single_crop(
                crop=c,
                area_ha=per_crop_ha,
                yield_str=all_predictions.get(c, ""),
                current_wpi=marketing_crops.get(c, {}).get("current_wpi", 150.0),
                historical_avg_wpi=marketing_crops.get(c, {}).get("historical_avg", 130.0),
                yoy_change_pct=marketing_crops.get(c, {}).get("yoy_change_pct", 0.0),
            )["revenue"]
            for c in results
        )
        portfolio_cost = sum(
            _project_single_crop(
                crop=c,
                area_ha=per_crop_ha,
                yield_str=all_predictions.get(c, ""),
                current_wpi=marketing_crops.get(c, {}).get("current_wpi", 150.0),
                historical_avg_wpi=marketing_crops.get(c, {}).get("historical_avg", 130.0),
                yoy_change_pct=marketing_crops.get(c, {}).get("yoy_change_pct", 0.0),
            )["total_cost"]
            for c in results
        )
        portfolio_profit = round(portfolio_revenue - portfolio_cost, 2)
    else:
        portfolio_revenue = portfolio_cost = portfolio_profit = 0.0
        per_crop_ha = area_ha

    return {
        "status": "success",
        "region":             region,
        "land_type":          land_type,
        "season":             season,
        "total_area_hectare": round(area_ha, 2),
        "best_financial_crop": best_financial_crop,
        "portfolio_summary": {
            "total_revenue": round(portfolio_revenue, 2),
            "total_cost":    round(portfolio_cost, 2),
            "total_profit":  round(portfolio_profit, 2),
            "per_crop_ha":   per_crop_ha,
            "num_crops":     len(results),
        },
        "crops": results,
    }