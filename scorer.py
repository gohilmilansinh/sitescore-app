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
    anchors = FOOTFALL_ANCHORS.get(brand_type,
              FOOTFALL_ANCHORS["restaurant"])
    total = 0
    for anchor in anchors:
        try:
            res = gmaps.places_nearby(
                location=(lat, lng),
                radius=500,
                type=anchor
            )
            total += len(res.get("results", []))
        except:
            pass
    return round(min(total / 10 * 100, 100), 1)

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
    
    result = gmaps.places_nearby(
        location=(lat, lng),
        radius=500,
        keyword=keyword,
        type=brand_type if brand_type != "school" else "school"
    )
    
    places = result.get("results", [])
    
    if not places:
        return 100.0  # no competitors = perfect score
    
    # Calculate weighted competitor pressure
    # A place with 1000+ reviews = 1.0 (strong competitor)
    # A place with 100 reviews  = 0.3 (moderate competitor)
    # A place with 10 reviews   = 0.1 (weak competitor)
    weighted_pressure = 0
    competitor_details = []

    for place in places:
        review_count  = place.get("user_ratings_total", 0)
        rating        = place.get("rating", 3.0)
        name          = place.get("name", "Unknown")

        # Review count weight: logarithmic scale
        # log10(1000) = 3.0 → weight 1.0 (capped)
        # log10(100)  = 2.0 → weight 0.67
        # log10(10)   = 1.0 → weight 0.33
        # log10(1)    = 0   → weight 0.0
        import math
        if review_count > 0:
            review_weight = min(math.log10(review_count) / 3.0, 1.0)
        else:
            review_weight = 0.05  # exists but unreviewed

        # Rating weight: higher rated = stronger competitor
        # Scale 1–5 → 0.2–1.0
        rating_weight = rating / 5.0

        # Combined competitor strength
        strength = review_weight * 0.7 + rating_weight * 0.3

        weighted_pressure += strength
        competitor_details.append({
            "name":    name,
            "reviews": review_count,
            "rating":  rating,
            "strength": round(strength, 2)
        })

    # Normalize: 10 full-strength competitors = score 0
    # Score = how much white space remains
    score = max(100 - (weighted_pressure / 10 * 100), 0)

    return round(score, 1), competitor_details

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

    competition_score, competitor_details = score_competition(
        lat, lng, brand_type)

    scores = {
        "demand":        score_demand(lat, lng),
        "footfall":      score_footfall(lat, lng, brand_type),
        "competition":   competition_score,
        "accessibility": score_accessibility(lat, lng),
        "catchment":     score_catchment(lat, lng)
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
        "competitor_details": competitor_details
    }