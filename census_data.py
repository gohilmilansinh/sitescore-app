from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Any

WARDS_PATH = Path(__file__).resolve().parent / "data" / "wards.json"


def load_ward_data() -> list[Dict[str, Any]]:
    with WARDS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


WARD_DATA = load_ward_data()


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in km between two GPS points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_population(
    lat: float, lng: float, radius_km: float = 1.0
) -> Dict[str, Any]:
    """
    Estimates population within radius_km of a point
    by finding nearby Census wards and interpolating
    based on distance-weighted overlap.
    """
    total_population = 0.0
    total_households = 0.0
    contributing_wards = []

    for ward in WARD_DATA:
        dist = haversine_distance(lat, lng, ward["lat"], ward["lng"])
        if dist <= 3.0:
            overlap = max(0.0, 1.0 - (dist / 3.0))
            weight = overlap ** 2

            total_population += ward["population"] * weight
            total_households += ward["households"] * weight

            if weight > 0.1:
                contributing_wards.append(
                    {
                        "name": ward["name"],
                        "city": ward["city"],
                        "distance": round(dist, 2),
                        "population": ward["population"],
                        "weight": round(weight, 2),
                    }
                )

    return {
        "estimated_population": int(total_population),
        "estimated_households": int(total_households),
        "contributing_wards": sorted(
            contributing_wards,
            key=lambda x: x["weight"],
            reverse=True,
        )[:3],
    }


def score_population(lat: float, lng: float) -> tuple[float, Dict[str, Any]]:
    """
    Returns a 0-100 score based on estimated population
    within 1km. 200,000+ people = score 100.
    """
    data = estimate_population(lat, lng, radius_km=1.0)
    pop = data["estimated_population"]
    score = round(min(pop / 200000 * 100, 100), 1)
    return score, data
