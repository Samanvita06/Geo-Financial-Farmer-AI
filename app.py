from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.collector import collect_data

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    city = data.get("city")
    bounds = data.get("bounds")

    if not city:
        return jsonify({"error": "City name is required"}), 400

    try:
        result = collect_data(city, bounds)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)