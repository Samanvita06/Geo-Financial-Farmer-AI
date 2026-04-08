import pandas as pd

# load dataset once
df = pd.read_csv("data/soil_yield.csv")

def soil_agent(n, p, k, ph, soil_type):
    
    # 🔥 tolerance (important)
    n_range = 25
    p_range = 25
    k_range = 25
    ph_range = 1

    # 📊 filter dataset using geo values
    filtered = df[
        (df['N'].between(n - n_range, n + n_range)) &
        (df['P'].between(p - p_range, p + p_range)) &
        (df['K'].between(k - k_range, k + k_range)) &
        (df['ph'].between(ph - ph_range, ph + ph_range))
    ]

    # 🎯 get crops
    crops = filtered['crop'].str.lower().unique().tolist()

    # 🌍 ADD GEO INTELLIGENCE (very important)
    if "sandy" in soil_type.lower():
        crops.append("groundnut")

    if "clay" in soil_type.lower():
        crops.append("rice")

    if ph > 7.5:
        crops.append("barley")

    if ph < 6:
        crops.append("potato")

    # ❗ remove duplicates
    crops = list(set(crops))

    # ⚠️ fallback (super important)
    if not crops:
        crops = ["millets", "pulses"]

    return crops[:5]