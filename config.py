from __future__ import annotations

from typing import Dict, List

SUPPORTED_CITIES: List[str] = [
    "ahmedabad",
    "surat",
    "vadodara",
    "baroda",
    "rajkot",
    "gandhinagar",
    "anand",
    "mehsana",
    "bharuch",
    "bhavnagar",
    "jamnagar",
    "junagadh",
    "gujarat",
    "gj",
]

WEIGHTS: Dict[str, float] = {
    "demand": 0.20,
    "footfall": 0.20,
    "competition": 0.20,
    "accessibility": 0.15,
    "catchment": 0.10,
    "spending_power": 0.15,
}

FOOTFALL_ANCHORS: Dict[str, List[str]] = {
    "restaurant": [
        "supermarket",
        "hospital",
        "school",
        "bus_station",
        "bank",
        "subway_station",
    ],
    "pharmacy": [
        "hospital",
        "doctor",
        "clinic",
        "residential",
        "bus_station",
        "bank",
    ],
    "supermarket": [
        "residential_area",
        "bus_station",
        "school",
        "bank",
        "pharmacy",
    ],
    "bank": [
        "supermarket",
        "office",
        "hospital",
        "bus_station",
        "school",
    ],
    "school": [
        "residential_area",
        "bus_station",
        "park",
        "library",
        "supermarket",
    ],
}

BRAND_KEYWORDS: Dict[str, str] = {
    "restaurant": "fast food burger pizza QSR cafe restaurant",
    "pharmacy": "pharmacy chemist medical store drugstore",
    "supermarket": "supermarket grocery kirana departmental store",
    "bank": "bank ATM financial services",
    "school": "school coaching institute tuition academy",
}

VERDICT_THRESHOLDS: Dict[str, float] = {
    "strong": 65.0,
    "moderate": 45.0,
}
