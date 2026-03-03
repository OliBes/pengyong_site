import json
import math
import os

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "eye_care_units.json")


def load_units():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_postcode_coords(postcode: str):
    """Resolve a UK postcode to (lat, lng) using the postcodes.io API."""
    clean = postcode.strip().replace(" ", "").upper()
    try:
        resp = requests.get(
            f"https://api.postcodes.io/postcodes/{clean}", timeout=8
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("status") == 200:
            result = data["result"]
            return result["latitude"], result["longitude"]
    except requests.RequestException:
        pass
    return None, None


def haversine_miles(lat1, lng1, lat2, lng2):
    """Return the great-circle distance in miles between two lat/lng points."""
    R = 3_958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/units")
def api_units():
    """Return all units (no distance calculation)."""
    return jsonify(load_units())


@app.route("/api/search")
def api_search():
    postcode = request.args.get("postcode", "").strip()
    if not postcode:
        return jsonify({"error": "Please enter a postcode."}), 400

    lat, lng = get_postcode_coords(postcode)
    if lat is None:
        return jsonify({"error": "Postcode not found. Please check and try again."}), 404

    units = load_units()
    for unit in units:
        unit["distance_miles"] = round(
            haversine_miles(lat, lng, unit["lat"], unit["lng"]), 1
        )

    units.sort(key=lambda u: u["distance_miles"])

    return jsonify({
        "postcode": postcode.upper(),
        "search_lat": lat,
        "search_lng": lng,
        "units": units,
    })


if __name__ == "__main__":
    app.run(debug=True)
