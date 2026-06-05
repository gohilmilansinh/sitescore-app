from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

BENCHMARKS_PATH = Path(__file__).resolve().parent / "data" / "benchmarks.json"


def load_benchmark_data() -> List[Dict[str, Any]]:
    with BENCHMARKS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


BENCHMARK_DATA = load_benchmark_data()


def get_benchmark_stats(brand_type: str = "restaurant") -> Dict[str, Any]:
    relevant = [
        (entry["score"], entry["address"])
        for entry in BENCHMARK_DATA
        if entry.get("brand_type") == brand_type
    ]

    if not relevant:
        relevant = [
            (entry["score"], entry["address"])
            for entry in BENCHMARK_DATA
        ]

    scores_only = [score for score, _ in relevant]
    avg = round(sum(scores_only) / len(scores_only), 1)
    top25 = sorted(scores_only, reverse=True)
    top25_avg = round(
        sum(top25[: max(1, len(top25) // 4)]) /
        max(1, len(top25) // 4),
        1,
    )

    city_counts: Dict[str, int] = {}
    for _, addr in relevant:
        lower_addr = addr.lower()
        for city in ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]:
            if city.lower() in lower_addr:
                city_counts[city] = city_counts.get(city, 0) + 1

    return {
        "count": len(scores_only),
        "average": avg,
        "top_sites_avg": top25_avg,
        "highest": max(scores_only),
        "lowest": min(scores_only),
        "brand_type": brand_type,
        "cities": city_counts,
    }


def get_percentile(score: float, brand_type: str = "restaurant") -> int:
    """Returns what percentile this score falls in vs benchmarks."""
    relevant = [
        entry["score"]
        for entry in BENCHMARK_DATA
        if entry.get("brand_type") == brand_type
    ]

    if not relevant:
        relevant = [entry["score"] for entry in BENCHMARK_DATA]

    below = sum(1 for value in relevant if value < score)
    return round((below / len(relevant)) * 100)


def get_category_context(score: float, brand_type: str = "restaurant") -> Dict[str, Any]:
    """Returns a human-readable benchmark context string."""
    stats = get_benchmark_stats(brand_type)
    percentile = get_percentile(score, brand_type)

    if percentile >= 75:
        tier = "top 25% of"
    elif percentile >= 50:
        tier = "above average among"
    elif percentile >= 25:
        tier = "below average among"
    else:
        tier = "bottom 25% of"

    return {
        "percentile": percentile,
        "tier": tier,
        "stats": stats,
        "context": (
            f"This site scores {score} — placing it in the {tier} "
            f"benchmarked {brand_type} locations in Ahmedabad "
            f"(avg: {stats['average']}, top sites: {stats['top_sites_avg']})."
        ),
    }

