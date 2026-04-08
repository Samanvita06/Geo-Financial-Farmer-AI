import pandas as pd

# Load dataset once
df = pd.read_csv("data/data/soil_yield.csv")

def yield_agent(recommended_crops, land_type, temp=25, humidity=50, n=60, p=45, k=50, ph=6.5):
    """
    recommended_crops — list from soil_agent
    land_type         — from analyzer (agent2)
    temp, humidity    — from agent1 weather
    n, p, k, ph       — from agent3 soil (dataset averages)

    Returns best crop, estimated yield, confidence, and all predictions.
    """

    results = {}

    for crop in recommended_crops:
        # ── Filter dataset rows matching this crop ────────────────
        crop_df = df[df['Crop_Type'].str.lower() == crop.lower()]

        if crop_df.empty:
            continue

        # ── Filter by current conditions ──────────────────────────
        filtered = crop_df[
            crop_df['Temperature'].between(temp - 6, temp + 6) &
            crop_df['Humidity'].between(humidity - 15, humidity + 15) &
            crop_df['N'].between(n - 25, n + 25) &
            crop_df['P'].between(p - 25, p + 25) &
            crop_df['K'].between(k - 25, k + 25) &
            crop_df['Soil_pH'].between(ph - 1.0, ph + 1.0)
        ]

        # fallback: just use temp+humidity match if NPK filter too strict
        if filtered.empty:
            filtered = crop_df[
                crop_df['Temperature'].between(temp - 6, temp + 6) &
                crop_df['Humidity'].between(humidity - 15, humidity + 15)
            ]

        # fallback: use full crop rows
        if filtered.empty:
            filtered = crop_df

        avg_yield    = round(filtered['Crop_Yield'].mean(), 2)
        avg_quality  = round(filtered['Soil_Quality'].mean(), 2) if 'Soil_Quality' in filtered.columns else 0

        results[crop] = {
            "estimated_yield_t_ha": avg_yield,
            "soil_quality":         avg_quality,
            "data_points":          len(filtered)
        }

    if not results:
        return {
            "best_crop":      "—",
            "estimated_yield": "—",
            "confidence":      0,
            "all_predictions": {}
        }

    # ── Pick best crop by yield ───────────────────────────────────
    best_crop = max(results, key=lambda c: results[c]["estimated_yield_t_ha"])
    best_yield = results[best_crop]["estimated_yield_t_ha"]

    # ── Confidence: based on data points + yield strength ─────────
    data_pts   = results[best_crop]["data_points"]
    confidence = min(95, round((min(data_pts, 200) / 200) * 70 + (best_yield / 140) * 30))

    return {
        "best_crop":       best_crop.capitalize(),
        "estimated_yield": f"{best_yield} t/ha",
        "confidence":      confidence,
        "all_predictions": {
            crop: f"{v['estimated_yield_t_ha']} t/ha"
            for crop, v in results.items()
        }
    }