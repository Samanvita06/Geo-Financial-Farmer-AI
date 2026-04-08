"""
Agent 5 — Marketing Intelligence
Reads WPI (Wholesale Price Index) data from 2012–2026 and generates:
  - Price trend analysis for the recommended crops
  - Best selling window (month with historically highest WPI)
  - YoY price change
  - Price volatility score
  - Market recommendation (sell now / wait / store)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime




def _load_wpi() -> pd.DataFrame:
    df = pd.read_csv(r"C:\Users\himap\TerraYield_AI\Geo-Financial-Farmer-AI\data\data\market.csv")
    df.set_index("Crop", inplace=True)
    return df


def _parse_columns(df: pd.DataFrame):
    """Return list of (month_name, year, column_label) sorted chronologically."""
    entries = []
    for col in df.columns:
        try:
            dt = datetime.strptime(col, "%B-%Y")
            entries.append((dt, col))
        except ValueError:
            continue
    return sorted(entries, key=lambda x: x[0])


def _crop_series(df: pd.DataFrame, crop: str) -> pd.Series | None:
    """Return a time-indexed Series for a crop (case-insensitive fuzzy match)."""
    crop_lower = crop.lower()
    for idx in df.index:
        if idx.lower() == crop_lower:
            s = df.loc[idx].dropna()
            # reindex to datetime
            dates = []
            vals = []
            for col, v in s.items():
                try:
                    dt = datetime.strptime(col, "%B-%Y")
                    dates.append(dt)
                    vals.append(float(v))
                except (ValueError, TypeError):
                    continue
            if not dates:
                return None
            return pd.Series(vals, index=pd.DatetimeIndex(dates)).sort_index()
    return None


def _best_selling_month(series: pd.Series) -> str:
    """Month name that historically has the highest average WPI."""
    monthly_avg = series.groupby(series.index.month).mean()
    best_month_num = int(monthly_avg.idxmax())
    return datetime(2000, best_month_num, 1).strftime("%B")


def _worst_selling_month(series: pd.Series) -> str:
    monthly_avg = series.groupby(series.index.month).mean()
    worst_month_num = int(monthly_avg.idxmin())
    return datetime(2000, worst_month_num, 1).strftime("%B")


def _yoy_change(series: pd.Series) -> float:
    """Year-over-year % change based on last 12 months vs prior 12 months."""
    if len(series) < 24:
        return 0.0
    recent = series.iloc[-12:].mean()
    prior  = series.iloc[-24:-12].mean()
    if prior == 0:
        return 0.0
    return round((recent - prior) / prior * 100, 2)


def _volatility_score(series: pd.Series) -> float:
    """Coefficient of variation (0–10 scaled), higher = more volatile."""
    if series.mean() == 0:
        return 0.0
    cv = series.std() / series.mean()
    return round(min(cv * 20, 10), 1)   # scale so CV≈0.5 → score 10


def _market_recommendation(yoy: float, current_wpi: float, historical_avg: float,
                            best_month: str, today_month: str) -> dict:
    score = 0
    reasons = []

    if yoy > 5:
        score += 2
        reasons.append(f"Prices up {yoy}% YoY — upward momentum")
    elif yoy < -5:
        score -= 2
        reasons.append(f"Prices down {abs(yoy)}% YoY — bearish trend")
    else:
        reasons.append(f"Prices relatively stable YoY ({yoy:+.1f}%)")

    if current_wpi > historical_avg * 1.05:
        score += 2
        reasons.append("Current WPI above historical average — good time to sell")
    elif current_wpi < historical_avg * 0.95:
        score -= 1
        reasons.append("Current WPI below historical average — consider waiting")

    if today_month == best_month:
        score += 3
        reasons.append(f"{best_month} is historically the best selling month")
    else:
        reasons.append(f"Best historical month to sell is {best_month}")

    if score >= 4:
        action = "SELL NOW 🟢"
        color  = "success"
    elif score >= 1:
        action = "HOLD & WATCH 🟡"
        color  = "warning"
    else:
        action = "STORE & WAIT 🔴"
        color  = "error"

    return {"action": action, "color": color, "reasons": reasons, "score": score}


def marketing_agent(recommended_crops: list, current_month: str | None = None) -> dict:
    """
    Parameters
    ----------
    recommended_crops : list[str]
        Crop names from Agent 3.
    current_month : str | None
        Override today's month name for testing (e.g. "April").

    Returns
    -------
    dict with per-crop intelligence + summary
    """
    try:
        df = _load_wpi()
    except FileNotFoundError:
        return {"error": "WPI dataset not found. Place wpi.csv in the data/ folder."}

    today = datetime.now()
    today_month = current_month or today.strftime("%B")
    today_year  = today.year

    results = {}
    all_actions = []

    for crop in recommended_crops:
        series = _crop_series(df, crop)
        if series is None or series.empty:
            results[crop] = {"status": "no_data",
                             "message": f"No WPI data found for '{crop}'"}
            continue

        current_wpi     = round(float(series.iloc[-1]), 2)
        historical_avg  = round(float(series.mean()), 2)
        best_month      = _best_selling_month(series)
        worst_month     = _worst_selling_month(series)
        yoy             = _yoy_change(series)
        volatility      = _volatility_score(series)
        rec             = _market_recommendation(yoy, current_wpi, historical_avg,
                                                  best_month, today_month)

        # Last 12 months trend for chart
        trend_12m = []
        for dt, v in zip(series.index[-12:], series.values[-12:]):
            trend_12m.append({"month": dt.strftime("%b %Y"), "wpi": round(float(v), 2)})

        results[crop] = {
            "crop":            crop,
            "current_wpi":     current_wpi,
            "historical_avg":  historical_avg,
            "yoy_change_pct":  yoy,
            "volatility_score": volatility,
            "best_selling_month":  best_month,
            "worst_selling_month": worst_month,
            "market_action":   rec["action"],
            "action_color":    rec["color"],
            "action_reasons":  rec["reasons"],
            "trend_12m":       trend_12m,
            "data_range": {
                "from": series.index[0].strftime("%B %Y"),
                "to":   series.index[-1].strftime("%B %Y"),
            }
        }
        all_actions.append(rec["score"])

    # Summary pick: crop with highest score
    best_crop = None
    best_score = -999
    for crop, info in results.items():
        if "market_action" in info:
            s = next((a for c, a in zip(recommended_crops,
                       [r.get("score", 0) for r in
                        [_market_recommendation(
                            results[c]["yoy_change_pct"],
                            results[c]["current_wpi"],
                            results[c]["historical_avg"],
                            results[c]["best_selling_month"],
                            today_month
                        ) for c in results if "market_action" in results[c]]
                       ]) if c == crop), 0)
            if s > best_score:
                best_score = s
                best_crop = crop

    # Simpler best-crop: highest current_wpi relative to hist avg
    top = None
    top_ratio = -1
    for crop, info in results.items():
        if "current_wpi" in info and info["historical_avg"] > 0:
            ratio = info["current_wpi"] / info["historical_avg"]
            if ratio > top_ratio:
                top_ratio = ratio
                top = crop

    return {
        "status": "success",
        "analysis_month": today_month,
        "analysis_year":  today_year,
        "best_market_crop": top,
        "crops": results,
    }