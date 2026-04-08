from flask import Flask, request, jsonify
from flask_cors import CORS

from modules.collector import collect_data
from modules.analyzer import analyze
from modules.soil import soil_agent
# (later) from modules.yield_agent import yield_agent

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze_route():
    data = request.json
    city = data.get("city")
    bounds = data.get("bounds")

    if not city:
        return jsonify({"error": "City name is required"}), 400

    try:
        # ------------------ AGENT 1 ------------------
        print(f"\n[Agent 1] Collecting data for: {city}")
        agent1_output = collect_data(city, bounds)

        # ------------------ AGENT 2 ------------------
        print(f"[Agent 2] Running geo analysis...")
        agent2_output = analyze(agent1_output)

        # ------------------ AGENT 3 (SOIL) ------------------
        print(f"[Agent 3] Running soil agent...")

        # 🔥 extract values
        minerals = agent2_output["soil_minerals"]

        # handle both text OR numeric safely
        def map_value(val):
            if isinstance(val, str):
                mapping = {"low": 30, "medium": 60, "high": 90}
                return mapping.get(val.lower(), 50)
            return val

        n = map_value(minerals["nitrogen"])
        p = map_value(minerals["phosphorus"])
        k = map_value(minerals["potassium"])

        # extract pH
        ph_text = minerals["pH"]
        low, high = map(float, ph_text.split(" ")[0].split("-"))
        ph = (low + high) / 2

        soil_type = agent2_output["soil_type"]

        crops = soil_agent(n, p, k, ph, soil_type)

        print(f"[Agent 3] Crops: {crops}")

        # ------------------ AGENT 4 (YIELD - future) ------------------
        # Example structure (we will build next)
        # best_crop = yield_agent(crops, agent1_output, dataset)

        # ------------------ FINAL RESPONSE ------------------
        return jsonify({
            "status": "success",
            "city": city,

            "agent1": agent1_output,
            "agent2": agent2_output,

            "agent3": {
                "n": n,
                "p": p,
                "k": k,
                "ph": ph,
                "soil_type": soil_type,
                "recommended_crops": crops
            },

            # placeholder for next step
            "agent4": {
                "message": "Yield agent not connected yet",
                "input_crops": crops
            }
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "agents_loaded": [
            "agent1_collection",
            "agent2_geospatial",
            "agent3_soil"
        ]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)