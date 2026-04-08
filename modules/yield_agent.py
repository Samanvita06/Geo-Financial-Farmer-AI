# modules/yield_agent.py

def yield_agent(crops, geo_data):
    """
    crops: list from soil_agent (recommended crops)
    geo_data: output from agent1 (weather + terrain)

    Returns:
        best crop + estimated yield + confidence
    """

    weather = geo_data.get("weather", {}).get("current", {})
    
    temp = weather.get("temperature_2m", 25)
    humidity = weather.get("relative_humidity_2m", 50)
    rainfall = weather.get("precipitation", 0)

    results = {}

    # 🌾 Simple scoring logic (can upgrade later with ML)
    for crop in crops:
        score = 0

        # Temperature suitability
        if crop.lower() in ["rice", "sugarcane"]:
            if 25 <= temp <= 35:
                score += 3
        elif crop.lower() in ["wheat", "barley"]:
            if 15 <= temp <= 25:
                score += 3
        else:
            if 20 <= temp <= 30:
                score += 2

        # Rainfall suitability
        if crop.lower() == "rice":
            if rainfall > 5:
                score += 3
        elif crop.lower() in ["millet", "maize"]:
            if rainfall < 5:
                score += 2
        else:
            score += 1

        # Humidity suitability
        if humidity > 60:
            score += 2
        else:
            score += 1

        # Convert score → yield estimate (ton/hectare approx)
        estimated_yield = round(1 + (score * 0.8), 2)

        results[crop] = estimated_yield

    # 🏆 Best crop selection
    best_crop = max(results, key=results.get) if results else None
    best_yield = results.get(best_crop, 0) if best_crop else 0

    # 📊 Confidence (based on score strength)
    confidence = min(95, int((best_yield / 5) * 100)) if best_yield else 0

    return {
        "best_crop": best_crop,
        "estimated_yield": f"{best_yield} ton/hectare",
        "confidence": confidence,
        "all_predictions": results
    }