"""
app.py — Flask backend for AgriMineral Land Analyzer.

Fix vs original:
  - season string is now passed from agent2 → soil_agent → yield_agent
    so crop recommendations and yield penalties are season-aware.
  - lat/lon from agent1 are passed into agent2 properly.
  - Error messages are more descriptive.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from modules.collector import collect_data
from modules.analyzer import analyze
from modules.soil import soil_agent
from modules.yield_agent import yield_agent
from modules.marketing_agent import marketing_agent
from modules.financial_agent import financial_agent
from modules.eda_agent import eda_agent

app = Flask(__name__)
CORS(app)


@app.route("/analyze", methods=["POST"])
def analyze_route():
    data = request.json
    city = data.get("city")
    bounds = data.get("bounds")

    if not city and not bounds:
        return jsonify({"error": "City name or bounds are required"}), 400

    # -------- AGENT 1: GEO DATA --------
    agent1_output = collect_data(city, bounds)

    # -------- AGENT 2: GEO-SPATIAL ANALYSIS --------
    # Pass lat/lon through for proper climate zone detection
    agent2_output = analyze(agent1_output)
    agent2_output["area_km2"] = bounds.get("area_km2", 1.0) if bounds else 1.0

    # -------- AGENT 3: SOIL (region + season aware) --------
    land_type = agent2_output.get("land_type", "lowland plains")
    season = agent2_output.get("current_season", "rabi / winter crop season")
    weather = agent1_output.get("weather", {}).get("current", {})
    temp = weather.get("temperature_2m", 25)
    humidity = weather.get("relative_humidity_2m", 60)

    try:
        soil_result = soil_agent(
            land_type=land_type,
            temp=temp,
            humidity=humidity,
            season=season,          # ← KEY FIX: season now passed in
        )
    except Exception as e:
        return jsonify({"error": f"soil_agent failed: {str(e)}"}), 500

    n = soil_result["n"]
    p = soil_result["p"]
    k = soil_result["k"]
    ph = soil_result["ph"]
    crops = soil_result["recommended_crops"]

    agent3_soil = {
        "n": n,
        "p": p,
        "k": k,
        "ph": ph,
        "soil_type": land_type,
        "recommended_crops": crops,
    }

    # -------- AGENT 4: YIELD (real-world benchmarks) --------
    try:
        yield_result = yield_agent(
            recommended_crops=crops,
            land_type=land_type,
            temp=temp,
            humidity=humidity,
            n=n, p=p, k=k, ph=ph,
            season=season,          # ← KEY FIX: season now passed in
        )
    except Exception as e:
        return jsonify({"error": f"yield_agent failed: {str(e)}"}), 500

    # -------- AGENT 5: MARKETING INTELLIGENCE --------
    try:
        marketing_result = marketing_agent(recommended_crops=crops)
    except Exception as e:
        return jsonify({"error": f"marketing_agent failed: {str(e)}"}), 500

    # -------- AGENT 6: FINANCIAL INTELLIGENCE --------
    try:
        financial_result = financial_agent(
            agent2_output=agent2_output,
            agent3_output=agent3_soil,
            agent4_output=yield_result,
            agent5_output=marketing_result,
        )
    except Exception as e:
        return jsonify({"error": f"financial_agent failed: {str(e)}"}), 500

    # -------- AGENT 7: EDA --------
    try:
        eda_result = eda_agent(
            agent1_output=agent1_output,
            agent2_output=agent2_output,
            agent3_output=agent3_soil,
            agent4_output=yield_result,
            agent5_output=marketing_result,
            agent6_output=financial_result,
        )
    except Exception as e:
        eda_result = {"status": "error", "error": str(e)}

    return jsonify({
        "status": "success",
        "city": city,
        "agent1": agent1_output,
        "agent2": agent2_output,
        "agent3_soil": agent3_soil,
        "agent4_yield": yield_result,
        "agent5_marketing": marketing_result,
        "agent6_financial": financial_result,
        "agent7_eda": eda_result,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
