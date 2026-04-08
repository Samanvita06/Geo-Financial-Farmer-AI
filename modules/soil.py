import pandas as pd

# Load dataset once
df = pd.read_csv("data/data/soil_yield.csv")

def soil_agent(land_type, temp=25, humidity=50):
    """
    land_type — from analyzer.py (classify_land output)
    temp      — from agent1 weather
    humidity  — from agent1 weather

    NPK and pH come purely from the dataset filtering.
    """

    # ── Filter by temperature ─────────────────────────────────────
    filtered = df[df['Temperature'].between(temp - 6, temp + 6)]
    if filtered.empty:
        filtered = df  # fallback: use full dataset

    # ── Filter by humidity ────────────────────────────────────────
    hum_filtered = filtered[filtered['Humidity'].between(humidity - 15, humidity + 15)]
    if not hum_filtered.empty:
        filtered = hum_filtered

    # ── Map land_type → Soil_Type in dataset ─────────────────────
    soil_map = {
        "lowland plains":  ["Loamy", "Clay"],
        "gentle hills":    ["Loamy", "Sandy"],
        "upland plateau":  ["Sandy", "Peaty"],
        "highland":        ["Peaty", "Sandy"],
        "mountainous":     ["Peaty", "Sandy"],
    }
    matched_soils = soil_map.get(land_type, [])
    if matched_soils:
        soil_filtered = filtered[filtered['Soil_Type'].isin(matched_soils)]
        if not soil_filtered.empty:
            filtered = soil_filtered

    # ── Pick top crops by average yield ──────────────────────────
    if not filtered.empty and 'Crop_Yield' in filtered.columns:
        top = (
            filtered.groupby('Crop_Type')['Crop_Yield']
            .mean()
            .sort_values(ascending=False)
        )
        crops = top.index.str.lower().tolist()
    else:
        crops = filtered['Crop_Type'].str.lower().unique().tolist()

    # ── Get NPK + pH averages from filtered rows ──────────────────
    n  = round(filtered['N'].mean(), 1)  if not filtered.empty else 60
    p  = round(filtered['P'].mean(), 1)  if not filtered.empty else 45
    k  = round(filtered['K'].mean(), 1)  if not filtered.empty else 50
    ph = round(filtered['Soil_pH'].mean(), 2) if not filtered.empty else 6.5

    # ── Geo intelligence from land_type ───────────────────────────
    if "lowland" in land_type:
        crops.append("rice")
    if "plains" in land_type or "hills" in land_type:
        crops.append("wheat")
    if "plateau" in land_type or "upland" in land_type:
        crops.append("millets")
    if ph > 7.5:
        crops.append("barley")
    if ph < 6.0:
        crops.append("potato")
    if temp > 28:
        crops.append("sugarcane")
    if temp < 20:
        crops.append("wheat")

    # ── Deduplicate + fallback ────────────────────────────────────
    crops = list(dict.fromkeys(crops))
    if not crops:
        crops = ["millets", "pulses"]

    print("NPK from dataset — N:", n, "P:", p, "K:", k, "pH:", ph)
    print("Recommended crops:", crops[:5])

    return {
        "n":                 n,
        "p":                 p,
        "k":                 k,
        "ph":                ph,
        "recommended_crops": crops[:5]
    }