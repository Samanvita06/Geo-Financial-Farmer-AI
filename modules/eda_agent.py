"""
modules/eda_agent.py
EDA (Exploratory Data Analysis) Agent — Agent 7

Consumes outputs from all 6 agents and returns structured analysis
data ready for rendering in Streamlit charts, tables, and summaries.

Sections:
  1. Geo & Climate  (Agent 1 + 2)
  2. Soil Profile   (Agent 3)
  3. Yield Analysis (Agent 4)
  4. Market / WPI   (Agent 5)
  5. Financial      (Agent 6)
  6. Cross-agent correlations & insights
"""

from __future__ import annotations
import os
import math
import statistics
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "markets.csv")


# ── Helpers ──────────────────────────────────────────────────────

def _safe_float(v, default=0.0):
    try:
        return float(str(v).replace(",", "").replace("₹", "").split()[0])
    except Exception:
        return default


def _pct_change(old, new):
    if old == 0:
        return 0.0
    return round((new - old) / old * 100, 2)


def _describe(values: list) -> dict:
    if not values:
        return {}
    return {
        "count":  len(values),
        "mean":   round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min":    round(min(values), 2),
        "max":    round(max(values), 2),
        "stdev":  round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
        "range":  round(max(values) - min(values), 2),
    }


# ── Section 1: Geo & Climate ──────────────────────────────────────

def _eda_geo(a1: dict, a2: dict) -> dict:
    weather  = a1.get("weather", {})
    current  = weather.get("current", {})
    forecast = weather.get("weekly_forecast", {})
    terrain  = a1.get("terrain", {})

    temp      = _safe_float(current.get("temperature_2m", 0))
    humidity  = _safe_float(current.get("relative_humidity_2m", 0))
    windspeed = _safe_float(current.get("windspeed_10m", 0))
    precip    = _safe_float(current.get("precipitation", 0))
    elevation = _safe_float(terrain.get("elevation_m", 0))

    tmax_list = [_safe_float(v) for v in forecast.get("temperature_2m_max", [])]
    tmin_list = [_safe_float(v) for v in forecast.get("temperature_2m_min", [])]
    rain_list = [_safe_float(v) for v in forecast.get("precipitation_sum", [])]
    days      = forecast.get("time", [])

    temp_spread = [round(mx - mn, 2) for mx, mn in zip(tmax_list, tmin_list)]

    T = temp; R = humidity
    heat_index = round(
        -8.78469 + 1.61139*T + 2.33855*R - 0.14611*T*R
        - 0.01230*T**2 - 0.01642*R**2 + 0.00221*T**2*R
        + 0.00073*T*R**2 - 0.000003*T**2*R**2, 1
    ) if temp > 27 else temp

    pet_approx = max(0.1,
        0.0023 * (temp + 17.8) *
        math.sqrt(max(0, tmax_list[0] - tmin_list[0] if tmax_list and tmin_list else 10)) * 30
    ) if tmax_list else 1
    aridity = round(sum(rain_list) / pet_approx, 3) if rain_list else 0

    forecast_chart = []
    for i, day in enumerate(days):
        forecast_chart.append({
            "day":    day[-5:] if len(day) >= 5 else day,
            "t_max":  tmax_list[i] if i < len(tmax_list) else None,
            "t_min":  tmin_list[i] if i < len(tmin_list) else None,
            "rain":   rain_list[i] if i < len(rain_list) else None,
            "spread": temp_spread[i] if i < len(temp_spread) else None,
        })

    return {
        "current": {
            "temperature":   temp,
            "humidity":      humidity,
            "windspeed":     windspeed,
            "precipitation": precip,
            "elevation":     elevation,
            "heat_index":    heat_index,
            "aridity_index": aridity,
        },
        "forecast_chart": forecast_chart,
        "forecast_stats": {
            "temperature_max": _describe(tmax_list),
            "temperature_min": _describe(tmin_list),
            "precipitation":   _describe(rain_list),
            "temp_spread":     _describe(temp_spread),
        },
        "geo_scores": {
            "farming_score":     a2.get("farming_score", 0),
            "soil_health_score": a2.get("soil_health_score", 0),
            "climate_zone":      a2.get("climate_zone", "—"),
            "land_type":         a2.get("land_type", "—"),
            "season":            a2.get("current_season", "—"),
        },
        "area_km2":     a2.get("area_km2", 0),
        "area_hectare": round(_safe_float(a2.get("area_km2", 0)) * 100, 2),
        "insights":     _geo_insights(temp, humidity, precip, elevation, a2.get("farming_score", 0)),
    }


def _geo_insights(temp, humidity, precip, elevation, farming_score):
    tips = []
    if temp > 35:
        tips.append("⚠️ High temperature (>35°C) — risk of heat stress for most crops.")
    elif temp < 15:
        tips.append("❄️ Cool temperature (<15°C) — suitable for Rabi crops (wheat, mustard).")
    else:
        tips.append("✅ Moderate temperature — favourable for most Kharif & Rabi crops.")
    if humidity > 80:
        tips.append("💧 High humidity — increased risk of fungal diseases. Monitor closely.")
    elif humidity < 40:
        tips.append("🌵 Low humidity — irrigation scheduling critical.")
    if precip > 10:
        tips.append("🌧️ Active precipitation — reduce irrigation; watch for waterlogging.")
    if elevation > 1000:
        tips.append("⛰️ High elevation — shorter growing season; cold-hardy crops preferred.")
    if farming_score >= 7:
        tips.append("🏆 Excellent farming suitability score — land is ready to cultivate.")
    elif farming_score >= 4:
        tips.append("🔧 Moderate suitability — soil amendment recommended before planting.")
    else:
        tips.append("🚫 Low suitability score — significant land preparation needed.")
    return tips


# ── Section 2: Soil ───────────────────────────────────────────────

def _eda_soil(a3: dict) -> dict:
    n  = _safe_float(a3.get("n", 0))
    p  = _safe_float(a3.get("p", 0))
    k  = _safe_float(a3.get("k", 0))
    ph = _safe_float(a3.get("ph", 7.0))
    crops = a3.get("recommended_crops", [])

    total_npk = n + p + k
    npk_balance = {
        "N": round(n / total_npk * 100, 1) if total_npk else 0,
        "P": round(p / total_npk * 100, 1) if total_npk else 0,
        "K": round(k / total_npk * 100, 1) if total_npk else 0,
    }

    if ph < 4.5:    ph_class = "Strongly Acidic"
    elif ph < 5.5:  ph_class = "Moderately Acidic"
    elif ph < 6.5:  ph_class = "Slightly Acidic"
    elif ph < 7.5:  ph_class = "Neutral"
    elif ph < 8.5:  ph_class = "Slightly Alkaline"
    else:           ph_class = "Strongly Alkaline"

    IDEAL = {"N": 120, "P": 60, "K": 60}
    gaps = {
        "N": round(max(0, IDEAL["N"] - n), 1),
        "P": round(max(0, IDEAL["P"] - p), 1),
        "K": round(max(0, IDEAL["K"] - k), 1),
    }

    nutrient_radar = [
        {"nutrient": "Nitrogen",   "value": n,  "ideal": IDEAL["N"]},
        {"nutrient": "Phosphorus", "value": p,  "ideal": IDEAL["P"]},
        {"nutrient": "Potassium",  "value": k,  "ideal": IDEAL["K"]},
    ]

    return {
        "npk":            {"N": n, "P": p, "K": k, "pH": ph},
        "npk_balance":    npk_balance,
        "ph_class":       ph_class,
        "nutrient_radar": nutrient_radar,
        "fertiliser_gaps": gaps,
        "recommended_crops": crops,
        "crop_count":     len(crops),
        "soil_type":      a3.get("soil_type", "—"),
        "insights":       _soil_insights(n, p, k, ph, gaps),
    }


def _soil_insights(n, p, k, ph, gaps):
    tips = []
    if gaps["N"] > 40:
        tips.append(f"🌿 Nitrogen deficient by {gaps['N']} kg/ha — apply urea or organic compost.")
    elif n > 150:
        tips.append("⚠️ Excess nitrogen — risk of lodging and leaf burn. Reduce N application.")
    else:
        tips.append("✅ Nitrogen within acceptable range.")
    if gaps["P"] > 20:
        tips.append(f"🔴 Phosphorus deficient by {gaps['P']} kg/ha — apply DAP or SSP.")
    if gaps["K"] > 20:
        tips.append(f"🟡 Potassium deficient by {gaps['K']} kg/ha — apply MOP or SOP.")
    if ph < 5.5:
        tips.append("🧪 Acidic soil — apply agricultural lime to raise pH before sowing.")
    elif ph > 8.0:
        tips.append("🧪 Alkaline soil — apply gypsum or sulphur to lower pH.")
    else:
        tips.append("✅ Soil pH is in optimal range (5.5–8.0) for most crops.")
    return tips


# ── Section 3: Yield ──────────────────────────────────────────────

def _eda_yield(a4: dict, area_ha: float) -> dict:
    best_crop  = a4.get("best_crop", "—")
    est_yield  = a4.get("estimated_yield", "0 t/ha")
    confidence = _safe_float(a4.get("confidence", 0))
    all_preds  = a4.get("all_predictions", {})

    parsed = {}
    for crop, val in all_preds.items():
        y = _safe_float(val, 0)
        parsed[crop] = {"yield_per_ha": y, "total_yield": round(y * area_ha, 2)}

    values  = [v["yield_per_ha"] for v in parsed.values() if v["yield_per_ha"] > 0]
    stats   = _describe(values)
    best_y  = max(values) if values else 0
    gaps    = {c: round(best_y - v["yield_per_ha"], 2) for c, v in parsed.items()}
    ranking = sorted(parsed.items(), key=lambda x: x[1]["yield_per_ha"], reverse=True)

    yield_chart = [
        {"crop": c, "yield_per_ha": v["yield_per_ha"], "total_yield": v["total_yield"]}
        for c, v in ranking
    ]

    return {
        "best_crop":   best_crop,
        "best_yield":  _safe_float(est_yield),
        "confidence":  confidence,
        "all_yields":  parsed,
        "yield_chart": yield_chart,
        "stats":       stats,
        "yield_gaps":  gaps,
        "ranking":     [(c, v["yield_per_ha"]) for c, v in ranking],
        "insights":    _yield_insights(best_crop, _safe_float(est_yield), confidence, stats),
    }


def _yield_insights(best_crop, best_yield, confidence, stats):
    tips = []
    if confidence >= 80:
        tips.append(f"✅ High confidence ({confidence:.0f}%) — yield prediction is reliable.")
    elif confidence >= 60:
        tips.append(f"⚠️ Moderate confidence ({confidence:.0f}%) — external factors may affect actual yield.")
    else:
        tips.append(f"⚠️ Low confidence ({confidence:.0f}%) — treat as indicative estimate only.")
    if best_yield > 0:
        tips.append(f"🏆 Best predicted crop: {best_crop} at {best_yield} t/ha.")
    if stats.get("stdev", 0) > stats.get("mean", 1) * 0.3:
        tips.append("📊 High yield variance across crops — diversification risk is elevated.")
    return tips


# ── Section 4: Market ─────────────────────────────────────────────

def _eda_market(a5: dict, recommended_crops: list) -> dict:
    crops_data = a5.get("crops", {})

    summary = []
    for cn, ci in crops_data.items():
        if ci.get("status") == "no_data":
            continue
        summary.append({
            "crop":           cn,
            "current_wpi":    ci.get("current_wpi", 0),
            "historical_avg": ci.get("historical_avg", 0),
            "yoy_pct":        ci.get("yoy_change_pct", 0),
            "volatility":     ci.get("volatility_score", 0),
            "best_month":     ci.get("best_selling_month", "—"),
            "action":         ci.get("market_action", "—"),
            "action_color":   ci.get("action_color", "warning"),
        })

    trend_data = {cn: ci["trend_12m"] for cn, ci in crops_data.items() if "trend_12m" in ci}

    # Deep WPI stats from CSV if available
    wpi_deep = {}
    if HAS_PANDAS and os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH).set_index("Crop")
            for crop in recommended_crops:
                match = next((idx for idx in df.index if idx.lower() == crop.lower()), None)
                if not match:
                    continue
                series = df.loc[match].dropna()
                vals = pd.to_numeric(series, errors="coerce").dropna()
                if vals.empty:
                    continue
                month_avgs = []
                for col in series.index:
                    try:
                        d = datetime.strptime(col, "%B-%Y")
                        month_avgs.append((d.month, float(vals[col])))
                    except Exception:
                        pass
                if HAS_PANDAS and month_avgs:
                    monthly_df = pd.DataFrame(month_avgs, columns=["month", "wpi"])
                    seasonality = (
                        monthly_df.groupby("month")["wpi"].mean().round(2)
                        .reset_index().rename(columns={"month": "month_num"})
                    )
                    seasonality["month_name"] = seasonality["month_num"].apply(
                        lambda m: datetime(2000, m, 1).strftime("%b")
                    )
                    yearly_dict = {}
                    for col in series.index:
                        try:
                            d = datetime.strptime(col, "%B-%Y")
                            yearly_dict.setdefault(d.year, []).append(float(vals[col]))
                        except Exception:
                            pass
                    yearly = [
                        {"year": yr, "avg_wpi": round(sum(vs) / len(vs), 2)}
                        for yr, vs in sorted(yearly_dict.items())
                    ]
                    wpi_deep[crop] = {
                        "seasonality": seasonality.to_dict("records"),
                        "yearly_trend": yearly,
                        "all_time_stats": {
                            "mean":   round(float(vals.mean()), 2),
                            "min":    round(float(vals.min()), 2),
                            "max":    round(float(vals.max()), 2),
                            "stdev":  round(float(vals.std()), 2),
                            "cv_pct": round(float(vals.std() / vals.mean() * 100), 1),
                        },
                    }
        except Exception as e:
            wpi_deep["_error"] = str(e)

    wpi_vals = {cn: ci.get("current_wpi", 0) for cn, ci in crops_data.items()
                if ci.get("status") != "no_data"}

    action_dist = {"SELL NOW 🟢": 0, "HOLD & WATCH 🟡": 0, "STORE & WAIT 🔴": 0}
    for row in summary:
        for key in action_dist:
            if key.split()[0] in row["action"]:
                action_dist[key] += 1

    return {
        "summary":          summary,
        "trend_data":       trend_data,
        "wpi_deep":         wpi_deep,
        "action_dist":      action_dist,
        "wpi_snapshot":     wpi_vals,
        "best_market_crop": a5.get("best_market_crop", "—"),
        "insights":         _market_insights(summary),
    }


def _market_insights(summary):
    tips = []
    if not summary:
        return tips
    volatile = [s["crop"] for s in summary if s["volatility"] > 6]
    stable   = [s["crop"] for s in summary if s["volatility"] < 3]
    sell_now = [s["crop"] for s in summary if "SELL" in s["action"]]
    rising   = [s["crop"] for s in summary if s["yoy_pct"] > 5]
    falling  = [s["crop"] for s in summary if s["yoy_pct"] < -5]
    if sell_now:
        tips.append(f"🟢 Sell signal active for: {', '.join(sell_now)} — WPI above historical avg.")
    if rising:
        tips.append(f"📈 Price momentum (YoY >5%): {', '.join(rising)}")
    if falling:
        tips.append(f"📉 Declining prices: {', '.join(falling)} — hold or store inventory.")
    if volatile:
        tips.append(f"⚡ High price volatility: {', '.join(volatile)} — hedge risk carefully.")
    if stable:
        tips.append(f"🎯 Stable price crops: {', '.join(stable)} — low-risk market options.")
    return tips


# ── Section 5: Financial ──────────────────────────────────────────

def _eda_financial(a6: dict) -> dict:
    crops_fin = a6.get("crops", {})
    portfolio = a6.get("portfolio_summary", {})

    rows = []
    for cn, ci in crops_fin.items():
        rows.append({
            "crop":     cn,
            "cost":     ci.get("total_cost", 0),
            "revenue":  ci.get("revenue", 0),
            "profit":   ci.get("profit", 0),
            "roi":      ci.get("roi_pct", 0),
            "area":     ci.get("area_hectare", 0),
            "yield_ha": _safe_float(ci.get("yield_per_ha", "0")),
            "price_q":  ci.get("price_per_quintal", 0),
        })

    profits  = [r["profit"]  for r in rows]
    revenues = [r["revenue"] for r in rows]
    costs    = [r["cost"]    for r in rows]
    rois     = [r["roi"]     for r in rows]

    cost_components = {}
    for cn, ci in crops_fin.items():
        for comp, val in ci.get("cost_breakdown", {}).items():
            cost_components.setdefault(comp, []).append(val)
    avg_cost_split = {k: round(sum(v) / len(v), 2) for k, v in cost_components.items()}

    ranking     = sorted(rows, key=lambda x: x["profit"], reverse=True)
    margin_data = [
        {
            "crop":         r["crop"],
            "gross_margin": round((r["revenue"] - r["cost"]) / r["revenue"] * 100, 1)
                            if r["revenue"] > 0 else 0,
            "cost_pct":     round(r["cost"] / r["revenue"] * 100, 1)
                            if r["revenue"] > 0 else 0,
        }
        for r in rows
    ]

    return {
        "rows":           rows,
        "ranking":        ranking,
        "margin_data":    margin_data,
        "avg_cost_split": avg_cost_split,
        "portfolio":      portfolio,
        "stats": {
            "profit":  _describe(profits),
            "revenue": _describe(revenues),
            "cost":    _describe(costs),
            "roi":     _describe(rois),
        },
        "best_crop":  a6.get("best_financial_crop", "—"),
        "region":     a6.get("region", "—"),
        "total_area": a6.get("total_area_hectare", 0),
        "insights":   _fin_insights(rows, portfolio),
    }


def _fin_insights(rows, portfolio):
    tips = []
    if not rows:
        return tips
    best  = max(rows, key=lambda x: x["profit"])
    worst = min(rows, key=lambda x: x["profit"])
    total_profit = portfolio.get("total_profit", 0)
    tips.append(f"🏆 Most profitable crop: {best['crop']} — ₹{best['profit']:,.0f} profit, ROI {best['roi']:.1f}%.")
    if worst["profit"] < 0:
        tips.append(f"❌ {worst['crop']} projects a loss (₹{worst['profit']:,.0f}) — consider replacing.")
    if total_profit > 0:
        tips.append(f"📊 Portfolio generates positive returns — ₹{total_profit:,.0f} net profit.")
    high_roi = [r for r in rows if r["roi"] > 100]
    if high_roi:
        tips.append(f"💎 High ROI crops (>100%): {', '.join(r['crop'] for r in high_roi)}")
    return tips


# ── Section 6: Cross-agent Insights ──────────────────────────────

def _cross_insights(geo: dict, soil: dict, yield_: dict, market: dict, fin: dict) -> dict:
    notes = []
    climate   = geo["geo_scores"].get("climate_zone", "")
    season    = geo["geo_scores"].get("season", "")
    best_crop = yield_.get("best_crop", "")

    if "Tropical" in climate and best_crop.lower() in ["rice", "sugarcane", "cotton"]:
        notes.append(f"✅ {best_crop} is well-matched to the {climate} climate zone.")
    if "Kharif" in season and best_crop.lower() in ["rice", "maize", "cotton", "soybean"]:
        notes.append(f"🌱 {best_crop} aligns with the current {season} season.")

    ph = soil["npk"]["pH"]
    if 6.0 <= ph <= 7.5 and yield_["best_yield"] > 2:
        notes.append("✅ Optimal soil pH supports the predicted high yield.")
    elif ph < 5.5:
        notes.append("⚠️ Acidic soil may be suppressing yield potential — liming recommended.")

    best_fin = fin.get("best_crop", "")
    best_mkt = market.get("best_market_crop", "")
    if best_fin and best_mkt and best_fin.lower() == best_mkt.lower():
        notes.append(f"🎯 Perfect alignment: {best_fin} is both the most profitable AND best market opportunity.")
    elif best_fin and best_mkt:
        notes.append(f"⚡ Split signal: Best financial crop ({best_fin}) ≠ Best market crop ({best_mkt}) — consider timing.")

    temp     = geo["current"]["temperature"]
    humidity = geo["current"]["humidity"]
    if temp > 38:
        notes.append("🌡️ Extreme heat may reduce actual yields below predictions.")
    if humidity > 85:
        notes.append("💧 High humidity elevates disease pressure — factor into cost estimates.")

    n = soil["npk"]["N"]
    if n < 60 and yield_.get("best_yield", 0) > 3:
        notes.append("⚠️ Low nitrogen relative to predicted yield — fertiliser investment needed.")

    fin_rows = fin.get("rows", [])
    if fin_rows:
        rev_ha = [(r["crop"], round(r["revenue"] / r["area"], 0)) for r in fin_rows if r["area"] > 0]
        best_rev_ha = max(rev_ha, key=lambda x: x[1]) if rev_ha else None
        if best_rev_ha:
            notes.append(f"💰 Highest revenue/ha: {best_rev_ha[0]} at ₹{best_rev_ha[1]:,.0f}/ha.")

    return {
        "notes":           notes,
        "alignment_score": len([n for n in notes if "✅" in n or "🎯" in n]),
        "risk_flags":      len([n for n in notes if "⚠️" in n or "❌" in n or "🌡️" in n]),
    }


# ── Main entry point ──────────────────────────────────────────────

def eda_agent(
    agent1_output: dict,
    agent2_output: dict,
    agent3_output: dict,
    agent4_output: dict,
    agent5_output: dict,
    agent6_output: dict,
) -> dict:
    try:
        geo    = _eda_geo(agent1_output, agent2_output)
        soil   = _eda_soil(agent3_output)
        area_ha = geo.get("area_hectare", 1.0)
        yield_ = _eda_yield(agent4_output, area_ha)
        market = _eda_market(agent5_output, agent3_output.get("recommended_crops", []))
        fin    = _eda_financial(agent6_output)
        cross  = _cross_insights(geo, soil, yield_, market, fin)

        return {
            "status":    "success",
            "generated": datetime.now().strftime("%d %b %Y, %H:%M"),
            "geo":       geo,
            "soil":      soil,
            "yield":     yield_,
            "market":    market,
            "financial": fin,
            "cross":     cross,
        }
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}
