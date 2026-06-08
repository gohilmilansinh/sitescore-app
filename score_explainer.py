from __future__ import annotations
from typing import Any, Dict, List
from benchmarks import get_benchmark_stats

# Benchmark averages per variable per brand type
# Used to calculate "above/below average" context
VARIABLE_AVERAGES = {
    "restaurant": {
        "demand":        72.0,
        "footfall":      78.0,
        "competition":   45.0,
        "accessibility": 82.0,
        "catchment":     75.0,
        "spending_power": 52.0,
    },
    "pharmacy": {
        "demand":        68.0,
        "footfall":      72.0,
        "competition":   50.0,
        "accessibility": 78.0,
        "catchment":     70.0,
        "spending_power": 50.0,
    },
    "supermarket": {
        "demand":        75.0,
        "footfall":      74.0,
        "competition":   48.0,
        "accessibility": 80.0,
        "catchment":     72.0,
        "spending_power": 51.0,
    },
    "bank": {
        "demand":        70.0,
        "footfall":      76.0,
        "competition":   52.0,
        "accessibility": 83.0,
        "catchment":     74.0,
        "spending_power": 53.0,
    },
    "school": {
        "demand":        74.0,
        "footfall":      70.0,
        "competition":   55.0,
        "accessibility": 76.0,
        "catchment":     68.0,
        "spending_power": 49.0,
    },
}

WEIGHTS = {
    "demand":         0.20,
    "footfall":       0.20,
    "competition":    0.20,
    "accessibility":  0.15,
    "catchment":      0.10,
    "spending_power": 0.15,
}

VARIABLE_LABELS = {
    "demand":         "Demand Potential",
    "footfall":       "Footfall Proxy",
    "competition":    "Competition",
    "accessibility":  "Accessibility",
    "catchment":      "Catchment Quality",
    "spending_power": "Spending Power",
}

VARIABLE_DESCRIPTIONS = {
    "demand": (
        "high",
        "Low residential density nearby — walk-in base limited",
        "Strong residential catchment within 1km"
    ),
    "footfall": (
        "high",
        "Few anchor stores nearby — footfall will be low",
        "Strong anchor stores driving consistent footfall"
    ),
    "competition": (
        "high",
        "High competitor density — saturated market",
        "Low competition — genuine white space available"
    ),
    "accessibility": (
        "high",
        "Limited road connectivity — hard to reach",
        "Excellent road network — easy access for customers"
    ),
    "catchment": (
        "high",
        "Low commercial activity nearby — weak catchment",
        "High commercial density — strong catchment area"
    ),
    "spending_power": (
        "high",
        "Low spending power area — value pricing needed",
        "High spending power — premium pricing viable"
    ),
}


def explain_scores(
    scores: Dict[str, float],
    brand_type: str = "restaurant",
    total_score: float = 0,
) -> Dict[str, Any]:
    """
    Returns a full contribution analysis for all score variables.
    Shows what each variable contributed and how it compares
    to the benchmark average.
    """
    averages = VARIABLE_AVERAGES.get(
        brand_type, VARIABLE_AVERAGES["restaurant"])

    contributions = []
    max_contribution = 0.0
    biggest_drag = None
    biggest_boost = None

    for key, weight in WEIGHTS.items():
        score      = scores.get(key, 0)
        avg        = averages.get(key, 50)
        contrib    = round(score * weight, 2)
        vs_avg     = round(score - avg, 1)
        avg_contrib = round(avg * weight, 2)
        delta      = round(contrib - avg_contrib, 2)

        # Direction: is higher always better?
        # Competition is inverted — high score = less competition = good
        is_positive = vs_avg >= 0

        _, low_msg, high_msg = VARIABLE_DESCRIPTIONS.get(
            key, ("high", "Below average", "Above average"))

        insight = high_msg if is_positive else low_msg

        entry = {
            "key":          key,
            "label":        VARIABLE_LABELS[key],
            "score":        score,
            "weight":       weight,
            "weight_pct":   int(weight * 100),
            "contribution": contrib,
            "avg_score":    avg,
            "vs_avg":       vs_avg,
            "delta":        delta,
            "is_positive":  is_positive,
            "insight":      insight,
        }
        contributions.append(entry)

        if delta < 0 and (
            biggest_drag is None or
            delta < biggest_drag["delta"]
        ):
            biggest_drag = entry

        if delta > 0 and (
            biggest_boost is None or
            delta > biggest_boost["delta"]
        ):
            biggest_boost = entry

    # Sort by absolute contribution descending
    contributions.sort(
        key=lambda x: abs(x["delta"]), reverse=True)

    # Build narrative
    narrative_parts = []
    if biggest_boost:
        narrative_parts.append(
            f"{biggest_boost['label']} is your strongest asset "
            f"(score {biggest_boost['score']}, "
            f"{abs(biggest_boost['vs_avg']):.0f} points above average)."
        )
    if biggest_drag:
        narrative_parts.append(
            f"{biggest_drag['label']} is the main drag "
            f"(score {biggest_drag['score']}, "
            f"{abs(biggest_drag['vs_avg']):.0f} points below average)."
        )

    return {
        "contributions":  contributions,
        "biggest_boost":  biggest_boost,
        "biggest_drag":   biggest_drag,
        "narrative":      " ".join(narrative_parts),
        "total_score":    total_score,
        "brand_type":     brand_type,
    }