from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

import googlemaps
import osmnx as ox
from config import (
    BRAND_KEYWORDS,
    FOOTFALL_ANCHORS,
    SUPPORTED_CITIES,
    VERDICT_THRESHOLDS,
    WEIGHTS,
)
from census_data import score_population

logger = logging.getLogger(__name__)


def cached_geocode(address: str) -> Tuple[Any, Any]:
    return geocode(address)


def cached_demand(lat: float, lng: float) -> Tuple[float, Dict[str, Any]]:
    return score_demand(lat, lng)


def cached_footfall(lat: float, lng: float, brand_type: str) -> Tuple[float, Dict[str, int]]:
    return score_footfall(lat, lng, brand_type)


def cached_competition(lat: float, lng: float, brand_type: str) -> Tuple[float, List[Dict[str, Any]]]:
    return score_competition(lat, lng, brand_type)


def cached_accessibility(lat: float, lng: float) -> Tuple[float, Dict[str, int]]:
    return score_accessibility(lat, lng)


def cached_catchment(lat: float, lng: float) -> Tuple[float, int]:
    return score_catchment(lat, lng)


def cached_spending(lat: float, lng: float) -> Tuple[float, Dict[str, Any]]:
    return score_spending_power(lat, lng)


def validate_address(address: str) -> Tuple[bool, str]:
    address_lower = address.strip().lower()
    if len(address_lower) < 6:
        return False, (
            "Address too short. Please provide a specific area "
            "and city name — e.g. 'Bopal, Ahmedabad, Gujarat'."
        )

    if not any(city in address_lower for city in SUPPORTED_CITIES):
        return False, (
            "This address does not appear to be in Gujarat. "
            "SiteScore currently covers Ahmedabad, Surat, Vadodara, "
            "and Rajkot only. Please include your city name."
        )

    return True, "Valid"


def geocode(address: str) -> Tuple[Any, Any]:
    if gmaps is None:
        logger.warning("No Google Maps client available for geocoding.")
        return None, None

    try:
        result = gmaps.geocode(address + ", Gujarat, India")
        if not result:
            return None, None

        found_gujarat = False
        components = result[0].get("address_components", [])
        for comp in components:
            types = comp.get("types", [])
            name = comp.get("long_name", "").lower()
            if "administrative_area_level_1" in types:
                if "gujarat" in name:
                    found_gujarat = True
                else:
                    return None, None

        formatted = result[0].get("formatted_address", "").lower()
        if not found_gujarat and "gujarat" not in formatted:
            return None, None

        loc = result[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    except Exception as exc:
        logger.warning("Geocode error for %s: %s", address, exc)
        return None, None


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
else:
    gmaps = None


def score_demand(lat: float, lng: float) -> Tuple[float, Dict[str, Any]]:
    try:
        pop_score, pop_data = score_population(lat, lng)

        if pop_data["estimated_population"] == 0:
            tags = {"building": ["residential", "apartments", "house"]}
            b = ox.features_from_point((lat, lng), tags=tags, dist=1000)
            count = len(b)
            return round(min(count / 200 * 100, 100), 1), {
                "method": "osm_buildings",
                "count": count,
                "population": 0,
                "households": 0,
            }

        return pop_score, {
            "method": "census_2011",
            "population": pop_data["estimated_population"],
            "households": pop_data["estimated_households"],
            "wards": pop_data["contributing_wards"],
        }
    except Exception as exc:
        logger.warning("Demand scoring failed: %s", exc)
        return 30.0, {"method": "fallback", "population": 0, "households": 0}


def score_footfall(lat: float, lng: float, brand_type: str = "restaurant") -> Tuple[float, Dict[str, int]]:
    if gmaps is None:
        logger.warning("No Google Maps client available for footfall scoring.")
        return 50.0, {}

    anchors = FOOTFALL_ANCHORS.get(brand_type, FOOTFALL_ANCHORS["restaurant"])
    total = 0
    found: Dict[str, int] = {}
    for anchor in anchors:
        try:
            res = gmaps.places_nearby(location=(lat, lng), radius=500, type=anchor)
            count = len(res.get("results", []))
            if count > 0:
                found[anchor] = count
            total += count
        except Exception as exc:
            logger.warning("Footfall query failed for %s: %s", anchor, exc)
    return round(min(total / 10 * 100, 100), 1), found


def score_competition(lat: float, lng: float, brand_type: str = "restaurant") -> Tuple[float, List[Dict[str, Any]]]:
    keyword = BRAND_KEYWORDS.get(brand_type, BRAND_KEYWORDS["restaurant"])

    if gmaps is None:
        logger.warning("No Google Maps client available for competition scoring.")
        return 50.0, []

    try:
        result = gmaps.places_nearby(
            location=(lat, lng),
            radius=500,
            keyword=keyword,
            type=brand_type if brand_type != "school" else "school",
        )
        places = result.get("results", [])
    except Exception as exc:
        logger.warning("Competition scoring failed: %s", exc)
        return 50.0, []

    if not places:
        return 100.0, []

    import math

    weighted_pressure = 0.0
    competitor_details: List[Dict[str, Any]] = []

    for place in places:
        review_count = place.get("user_ratings_total", 0)
        rating = place.get("rating", 3.0)
        name = place.get("name", "Unknown")

        review_weight = min(math.log10(review_count) / 3.0, 1.0) if review_count > 0 else 0.05
        rating_weight = rating / 5.0
        strength = review_weight * 0.7 + rating_weight * 0.3

        weighted_pressure += strength
        competitor_details.append(
            {
                "name": name,
                "reviews": review_count,
                "rating": rating,
                "strength": round(strength, 2),
            }
        )

    score = max(100.0 - (weighted_pressure / 10 * 100), 0.0)
    return round(score, 1), competitor_details


def score_accessibility(lat: float, lng: float) -> Tuple[float, Dict[str, int]]:
    try:
        G = ox.graph_from_point((lat, lng), dist=300, network_type="drive")
        intersections = len([n for n, d in G.degree() if d > 2])
        total_nodes = len(G.nodes)
        return round(min(intersections / 15 * 100, 100), 1), {
            "intersections": intersections,
            "total_nodes": total_nodes,
        }
    except Exception as exc:
        logger.warning("Accessibility scoring failed: %s", exc)
        return 40.0, {"intersections": 0, "total_nodes": 0}


def score_catchment(lat: float, lng: float) -> Tuple[float, int]:
    if gmaps is None:
        logger.warning("No Google Maps client available for catchment scoring.")
        return 30.0, 0
    try:
        result = gmaps.places_nearby(
            location=(lat, lng), radius=1000, keyword="cafe restaurant shop"
        )
        count = len(result.get("results", []))
        return round(min(count / 20 * 100, 100), 1), count
    except Exception as exc:
        logger.warning("Catchment scoring failed: %s", exc)
        return 30.0, 0


def score_spending_power(lat: float, lng: float) -> Tuple[float, Dict[str, Any]]:
    if gmaps is None:
        logger.warning("No Google Maps client available for spending power scoring.")
        return 50.0, {"avg_price_level": None, "sample_size": 0}

    try:
        result = gmaps.places_nearby(
            location=(lat, lng), radius=1000, keyword="restaurant cafe shop hotel"
        )
        places = result.get("results", [])

        if not places:
            return 50.0, {"avg_price_level": None, "sample_size": 0}

        price_levels = [p["price_level"] for p in places if "price_level" in p]
        if not price_levels:
            return 50.0, {"avg_price_level": None, "sample_size": 0}

        avg = sum(price_levels) / len(price_levels)
        score = round(min(avg / 4 * 100, 100), 1)

        return score, {
            "avg_price_level": round(avg, 2),
            "sample_size": len(price_levels),
            "distribution": {
                "budget (0-1)": sum(1 for p in price_levels if p <= 1),
                "moderate (2)": sum(1 for p in price_levels if p == 2),
                "premium (3-4)": sum(1 for p in price_levels if p >= 3),
            },
        }
    except Exception as exc:
        logger.warning("Spending power scoring failed: %s", exc)
        return 50.0, {"avg_price_level": None, "sample_size": 0}


def score_site(address: str, brand_type: str = "restaurant") -> Dict[str, Any]:
    is_valid, message = validate_address(address)
    if not is_valid:
        return {"error": message}

    lat, lng = cached_geocode(address)
    if not lat:
        return {
            "error": (
                "Could not find this address in Gujarat. "
                "Try adding area name and city — "
                "e.g. 'Bopal, Ahmedabad, Gujarat'."
            )
        }

    demand_score, demand_data = cached_demand(lat, lng)
    footfall_score, footfall_found = cached_footfall(lat, lng, brand_type)
    competition_score, competitor_details = cached_competition(lat, lng, brand_type)
    access_score, access_data = cached_accessibility(lat, lng)
    catchment_score, catchment_count = cached_catchment(lat, lng)
    spending_score, spending_data = cached_spending(lat, lng)

    scores = {
        "demand": demand_score,
        "footfall": footfall_score,
        "competition": competition_score,
        "accessibility": access_score,
        "catchment": catchment_score,
        "spending_power": spending_score,
    }

    total = sum(scores[k] * WEIGHTS[k] for k in scores)
    verdict_thresholds = VERDICT_THRESHOLDS
    verdict = (
        "Strong"
        if total >= verdict_thresholds["strong"]
        else "Moderate"
        if total >= verdict_thresholds["moderate"]
        else "Weak"
    )

    return {
        "address": address,
        "lat": lat,
        "lng": lng,
        "brand_type": brand_type,
        "scores": scores,
        "total_score": round(total, 1),
        "verdict": verdict,
        "competitor_details": competitor_details,
        "raw": {
            "demand_buildings": demand_data.get("count", 0),
            "demand_population": demand_data.get("population", 0),
            "demand_households": demand_data.get("households", 0),
            "demand_method": demand_data.get("method", "unknown"),
            "demand_wards": demand_data.get("wards", []),
            "footfall_anchors": footfall_found,
            "intersections": access_data["intersections"],
            "road_nodes": access_data["total_nodes"],
            "catchment_places": catchment_count,
            "competitor_count": len(competitor_details),
            "spending_data": spending_data,
        },
    }
