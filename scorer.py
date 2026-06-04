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
        b     = ox.features_from_point((lat, lng), tags=tags, dist=1000)
        count = len(b)
        return round(min(count / 200 * 100, 100), 1), count
    except:
        return 30, 0

FOOTFALL_ANCHORS = {
    "restaurant":  ["supermarket", "hospital", "school",
                    "bus_station", "bank", "subway_station"],
    "pharmacy":    ["hospital", "doctor", "clinic",
                    "residential", "bus_station", "bank"],
    "supermarket": ["residential_area", "bus_station",
                    "school", "bank", "pharmacy"],
    "bank":        ["supermarket", "office", "hospital",
                    "bus_station", "school"],
    "school":      ["residential_area", "bus_station",
                    "park", "library", "supermarket"],
}

def score_footfall(lat, lng, brand_type="restaurant"):
    anchors = FOOTFALL_ANCHORS.get(brand_type, FOOTFALL_ANCHORS["restaurant"])
    total   = 0
    found   = {}
    for anchor in anchors:
        try:
            res   = gmaps.places_nearby(location=(lat, lng),
                                        radius=500, type=anchor)
            count = len(res.get("results", []))
            if count > 0:
                found[anchor] = count
            total += count
        except:
            pass
    return round(min(total / 10 * 100, 100), 1), found

# Brand-specific competitor keywords
BRAND_KEYWORDS = {
    "restaurant":   "fast food burger pizza QSR cafe restaurant",
    "pharmacy":     "pharmacy chemist medical store drugstore",
    "supermarket":  "supermarket grocery kirana departmental store",
    "bank":         "bank ATM financial services",
    "school":       "school coaching institute tuition academy",
}

def score_competition(lat, lng, brand_type="restaurant"):
    keyword = BRAND_KEYWORDS.get(brand_type, BRAND_KEYWORDS["restaurant"])

    try:
        result = gmaps.places_nearby(
            location=(lat, lng),
            radius=500,
            keyword=keyword,
            type=brand_type if brand_type != "school" else "school"
        )
        places = result.get("results", [])
    except:
        return 50.0, []  # safe fallback

    if not places:
        return 100.0, []  # always return tuple, even when empty

    import math
    weighted_pressure  = 0
    competitor_details = []

    for place in places:
        review_count = place.get("user_ratings_total", 0)
        rating       = place.get("rating", 3.0)
        name         = place.get("name", "Unknown")

        if review_count > 0:
            review_weight = min(math.log10(review_count) / 3.0, 1.0)
        else:
            review_weight = 0.05

        rating_weight = rating / 5.0
        strength      = review_weight * 0.7 + rating_weight * 0.3

        weighted_pressure += strength
        competitor_details.append({
            "name":     name,
            "reviews":  review_count,
            "rating":   rating,
            "strength": round(strength, 2)
        })

    score = max(100 - (weighted_pressure / 10 * 100), 0)
    return round(score, 1), competitor_details  # always a tuple

def score_accessibility(lat, lng):
    try:
        G             = ox.graph_from_point((lat, lng), dist=300,
                                            network_type="drive")
        intersections = len([n for n, d in G.degree() if d > 2])
        total_nodes   = len(G.nodes)
        return round(min(intersections / 15 * 100, 100), 1), {
            "intersections": intersections,
            "total_nodes":   total_nodes
        }
    except:
        return 40, {"intersections": 0, "total_nodes": 0}

def score_catchment(lat, lng):
    try:
        result = gmaps.places_nearby(
            location=(lat, lng),
            radius=1000,
            keyword="cafe restaurant shop"
        )
        count = len(result.get("results", []))
        return round(min(count / 20 * 100, 100), 1), count
    except:
        return 30, 0

def score_site(address, brand_type="restaurant"):
    lat, lng = geocode(address)
    if not lat:
        return None

    demand_score,      demand_count       = score_demand(lat, lng)
    footfall_score,    footfall_found     = score_footfall(lat, lng, brand_type)
    competition_score, competitor_details = score_competition(lat, lng, brand_type)
    access_score,      access_data        = score_accessibility(lat, lng)
    catchment_score,   catchment_count    = score_catchment(lat, lng)

    scores = {
        "demand":        demand_score,
        "footfall":      footfall_score,
        "competition":   competition_score,
        "accessibility": access_score,
        "catchment":     catchment_score
    }

    total = sum(scores[k] * WEIGHTS[k] for k in scores)

    return {
        "address":            address,
        "lat":                lat,
        "lng":                lng,
        "brand_type":         brand_type,
        "scores":             scores,
        "total_score":        round(total, 1),
        "verdict":            "Strong" if total >= 65 else
                              "Moderate" if total >= 45 else "Weak",
        "competitor_details": competitor_details,
        "raw": {
            "demand_buildings":    demand_count,
            "footfall_anchors":    footfall_found,
            "intersections":       access_data["intersections"],
            "road_nodes":          access_data["total_nodes"],
            "catchment_places":    catchment_count,
            "competitor_count":    len(competitor_details),
        }
    }