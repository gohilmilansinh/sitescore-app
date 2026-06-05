import osmnx as ox
import googlemaps
import json
import os
from census_data import score_population

SUPPORTED_CITIES = [
    "ahmedabad", "surat", "vadodara", "baroda",
    "rajkot", "gandhinagar", "anand", "mehsana",
    "bharuch", "bhavnagar", "jamnagar", "junagadh",
    "gujarat", "gj"
]

def validate_address(address):
    address_lower = address.strip().lower()

    if len(address.strip()) < 6:
        return False, (
            "Address too short. Please provide a specific area "
            "and city name — e.g. 'Bopal, Ahmedabad, Gujarat'."
        )

    is_gujarat = any(city in address_lower for city in SUPPORTED_CITIES)
    if not is_gujarat:
        return False, (
            "This address does not appear to be in Gujarat. "
            "SiteScore currently covers Ahmedabad, Surat, Vadodara, "
            "and Rajkot only. Please include your city name."
        )

    return True, "Valid"


def geocode(address):
    try:
        result = gmaps.geocode(address + ", Gujarat, India")
        if not result:
            return None, None

        # Check every address component for Gujarat
        found_gujarat = False
        components = result[0].get("address_components", [])
        for comp in components:
            types = comp.get("types", [])
            name  = comp.get("long_name", "").lower()
            if "administrative_area_level_1" in types:
                if "gujarat" in name:
                    found_gujarat = True
                else:
                    # Google returned a result outside Gujarat
                    return None, None

        # Also check formatted address as backup
        formatted = result[0].get("formatted_address", "").lower()
        if not found_gujarat and "gujarat" not in formatted:
            return None, None

        loc = result[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    except Exception as e:
        print(f"Geocode error: {e}")
        return None, None

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY","")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

WEIGHTS = {
    "demand":          0.20,  # reduced from 0.25
    "footfall":        0.20,  # reduced from 0.25
    "competition":     0.20,
    "accessibility":   0.15,  # reduced from 0.20
    "catchment":       0.10,
    "spending_power":  0.15,  # new variable
}


def score_demand(lat, lng):
    """
    Uses Census 2011 ward data to estimate population
    within 1km. More accurate than building count.
    """
    try:
        pop_score, pop_data = score_population(lat, lng)

        # Fallback to OSM buildings if population estimate is zero
        if pop_data["estimated_population"] == 0:
            tags  = {"building": ["residential", "apartments", "house"]}
            b     = ox.features_from_point((lat, lng), tags=tags, dist=1000)
            count = len(b)
            return round(min(count / 200 * 100, 100), 1), {
                "method":     "osm_buildings",
                "count":      count,
                "population": 0,
                "households": 0
            }

        return pop_score, {
            "method":      "census_2011",
            "population":  pop_data["estimated_population"],
            "households":  pop_data["estimated_households"],
            "wards":       pop_data["contributing_wards"]
        }
    except Exception as e:
        return 30, {
            "method":     "fallback",
            "population": 0,
            "households": 0
        }

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

def score_spending_power(lat, lng):
    """
    Uses average price level of nearby places as a spending
    power proxy. Google price_level: 0=free, 1=cheap,
    2=moderate, 3=expensive, 4=very expensive.
    Areas with avg price_level 3+ = high spending power.
    """
    try:
        result = gmaps.places_nearby(
            location=(lat, lng),
            radius=1000,
            keyword="restaurant cafe shop hotel"
        )
        places = result.get("results", [])

        if not places:
            return 50, {"avg_price_level": None, "sample_size": 0}

        price_levels = [
            p["price_level"]
            for p in places
            if "price_level" in p
        ]

        if not price_levels:
            return 50, {"avg_price_level": None, "sample_size": 0}

        avg = sum(price_levels) / len(price_levels)

        # Scale: 0→0, 1→25, 2→50, 3→75, 4→100
        score = round(min(avg / 4 * 100, 100), 1)

        return score, {
            "avg_price_level": round(avg, 2),
            "sample_size":     len(price_levels),
            "distribution": {
                "budget (0-1)":   sum(1 for p in price_levels if p <= 1),
                "moderate (2)":   sum(1 for p in price_levels if p == 2),
                "premium (3-4)":  sum(1 for p in price_levels if p >= 3),
            }
        }
    except:
        return 50, {"avg_price_level": None, "sample_size": 0}

def score_site(address, brand_type="restaurant"):
    # Validate address first
    is_valid, message = validate_address(address)
    if not is_valid:
        return {"error": message}

    lat, lng = geocode(address)
    if not lat:
        return {"error": (
            "Could not find this address in Gujarat. "
            "Make sure you include the area name and city — "
            "e.g. 'Bopal, Ahmedabad, Gujarat'. "
            "If the address is correct, try adding more detail."
        )}

    demand_score,      demand_data        = score_demand(lat, lng)
    footfall_score,    footfall_found     = score_footfall(lat, lng, brand_type)
    competition_score, competitor_details = score_competition(lat, lng, brand_type)
    access_score,      access_data        = score_accessibility(lat, lng)
    catchment_score,   catchment_count    = score_catchment(lat, lng)
    spending_score,    spending_data      = score_spending_power(lat, lng)

    scores = {
        "demand":         demand_score,
        "footfall":       footfall_score,
        "competition":    competition_score,
        "accessibility":  access_score,
        "catchment":      catchment_score,
        "spending_power": spending_score,
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
            "demand_buildings":  demand_data.get("count", 0),
            "demand_population": demand_data.get("population", 0),
            "demand_households": demand_data.get("households", 0),
            "demand_method":     demand_data.get("method", "unknown"),
            "demand_wards":      demand_data.get("wards", []),
            "footfall_anchors":  footfall_found,
            "intersections":     access_data["intersections"],
            "road_nodes":        access_data["total_nodes"],
            "catchment_places":  catchment_count,
            "competitor_count":  len(competitor_details),
            "spending_data":     spending_data,
        }
    }