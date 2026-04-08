from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.collector import collect_data
from modules.analyzer import analyze

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
        print(f"\n[Agent 1] Collecting data for: {city}")
        agent1_output = collect_data(city, bounds)
        print(f"[Agent 1] Done.")

        print(f"[Agent 2] Running geo-spatial analysis...")
        agent2_output = analyze(agent1_output)
        print(f"[Agent 2] Done.")
        print(f"  Climate zone  : {agent2_output['climate_zone']}")
        print(f"  Land type     : {agent2_output['land_type']}")
        print(f"  Farming score : {agent2_output['farming_score']}/10")
        print(f"  Mineral score : {agent2_output['mineral_score']}/10")

        return jsonify({
            "status": "success",
            "city": city,
            "agent1": agent1_output,
            "agent2": agent2_output
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "agents_loaded": ["agent1_collection", "agent2_geospatial"]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)