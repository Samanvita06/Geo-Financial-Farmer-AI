from flask import Flask, request, jsonify
from flask_cors import CORS

from modules.collector import collect_data
from modules.analyzer import analyze

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze_route():
    data   = request.json
    city   = data.get("city")
    bounds = data.get("bounds")

    if not city:
        return jsonify({"error": "City name is required"}), 400

    try:
        # -------- AGENT 1: GEO DATA --------
        agent1_output = collect_data(city, bounds)

        # -------- AGENT 2: GEO-SPATIAL ANALYSIS --------
        agent2_output = analyze(agent1_output)

        return jsonify({
            "status": "success",
            "city":   city,
            "agent1": agent1_output,
            "agent2": agent2_output,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)