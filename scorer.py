import osmnx as ox
import googlemaps
import json
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY","")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

WEIGHTS = {
    "demand":        0.25,
    "footfall":      0.25,
    "competition":   0.20,
    "accessibility": 0.20,
    "catchment":     0.10
}

def geocode(address):
    result = gmaps.geocode(address)
    if not result:
        return None, None
    loc = result[0]["geometry"]["location"]
    return loc["lat"], loc["lng"]

def score_demand(lat, lng):
    tags = {"building": ["residential", "apartments", "house"]}
    try:
        b = ox.features_from_point((lat, lng), tags=tags, dist=1000)
        return round(min(len(b) / 200 * 100, 100), 1)
    except:
        return 30

def score_footfall(lat, lng):
    anchor_types = ["supermarket", "hospital", "school",
                    "bus_station", "subway_station", "bank"]
    total = 0
    for anchor in anchor_types:
        result = gmaps.places_nearby(
            location=(lat, lng), radius=500, type=anchor)
        total += len(result.get("results", []))
    return round(min(total / 10 * 100, 100), 1)

def score_competition(lat, lng, brand_type="restaurant"):
    result = gmaps.places_nearby(
        location=(lat, lng),
        radius=500,
        keyword="fast food burger pizza QSR",
        type=brand_type
    )
    count = len(result.get("results", []))
    return round(max(100 - (count / 20 * 100), 0), 1)

def score_accessibility(lat, lng):
    try:
        G = ox.graph_from_point((lat, lng), dist=300, network_type="drive")
        intersections = len([n for n, d in G.degree() if d > 2])
        return round(min(intersections / 15 * 100, 100), 1)
    except:
        return 40

def score_catchment(lat, lng):
    result = gmaps.places_nearby(
        location=(lat, lng),
        radius=1000,
        keyword="cafe restaurant shop"
    )
    count = len(result.get("results", []))
    return round(min(count / 20 * 100, 100), 1)

def score_site(address, brand_type="restaurant"):
    lat, lng = geocode(address)
    if not lat:
        return None

    scores = {
        "demand":        score_demand(lat, lng),
        "footfall":      score_footfall(lat, lng),
        "competition":   score_competition(lat, lng, brand_type),
        "accessibility": score_accessibility(lat, lng),
        "catchment":     score_catchment(lat, lng)
    }

    total = sum(scores[k] * WEIGHTS[k] for k in scores)

    return {
        "address": address,
        "lat": lat,
        "lng": lng,
        "scores": scores,
        "total_score": round(total, 1),
        "verdict": "Strong" if total >= 65 else "Moderate" if total >= 45 else "Weak"
    }