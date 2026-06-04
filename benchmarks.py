# Pre-scored reference locations for Ahmedabad
# These were scored using the same engine and serve as benchmarks
# Format: (address, brand_type, total_score, category)

BENCHMARK_DATA = [
    # Strong QSR locations
    ("Alpha One Mall, Ahmedabad",           "restaurant", 84.0, "mall"),
    ("Domino's Pizza, CG Road, Ahmedabad",  "restaurant", 97.0, "high_street"),
    ("KFC, Prahlad Nagar, Ahmedabad",       "restaurant", 69.4, "residential"),
    ("Subway, SG Highway, Ahmedabad",       "restaurant", 97.0, "highway"),
    ("Pizza Hut, Vastrapur, Ahmedabad",     "restaurant", 84.0, "residential"),
    ("McDonald's, Iscon Mall, Ahmedabad",   "restaurant", 85.0, "mall"),
    ("Domino's, Bopal, Ahmedabad",          "restaurant", 79.0, "suburban"),
    ("KFC, Satellite Road, Ahmedabad",      "restaurant", 82.0, "high_street"),
    ("Pizza Hut, Navrangpura, Ahmedabad",   "restaurant", 88.0, "commercial"),
    ("Wow Momo, Thaltej, Ahmedabad",        "restaurant", 76.0, "suburban"),

    # Moderate QSR locations
    ("Naroda, Ahmedabad",                   "restaurant", 68.2, "industrial"),
    ("Nikol, Ahmedabad",                    "restaurant", 80.5, "residential"),
    ("Odhav, Ahmedabad",                    "restaurant", 79.0, "industrial"),
    ("Vastral, Ahmedabad",                  "restaurant", 65.0, "suburban"),
    ("Chandkheda, Ahmedabad",               "restaurant", 72.0, "suburban"),

    # Pharmacy locations
    ("Apollo Pharmacy, CG Road, Ahmedabad",     "pharmacy", 88.0, "high_street"),
    ("MedPlus, Satellite Road, Ahmedabad",      "pharmacy", 82.0, "high_street"),
    ("Apollo Pharmacy, Bopal, Ahmedabad",       "pharmacy", 74.0, "suburban"),
    ("Wellness Forever, Vastrapur, Ahmedabad",  "pharmacy", 79.0, "residential"),
    ("MedPlus, Nikol, Ahmedabad",               "pharmacy", 70.0, "residential"),

    # Supermarket locations
    ("D-Mart, Prahlad Nagar, Ahmedabad",    "supermarket", 86.0, "residential"),
    ("Big Bazaar, Iscon Mall, Ahmedabad",   "supermarket", 83.0, "mall"),
    ("D-Mart, Bopal, Ahmedabad",            "supermarket", 78.0, "suburban"),
    ("Reliance Fresh, Navrangpura",         "supermarket", 84.0, "commercial"),
    ("D-Mart, Vastral, Ahmedabad",          "supermarket", 69.0, "suburban"),
]


def get_benchmark_stats(brand_type="restaurant"):
    """Returns benchmark statistics for a given brand type."""
    relevant = [
        score for addr, btype, score, cat in BENCHMARK_DATA
        if btype == brand_type
    ]

    if not relevant:
        relevant = [score for _, _, score, _ in BENCHMARK_DATA]

    avg   = round(sum(relevant) / len(relevant), 1)
    high  = max(relevant)
    low   = min(relevant)
    top25 = sorted(relevant, reverse=True)[:max(1, len(relevant)//4)]
    top25_avg = round(sum(top25) / len(top25), 1)

    return {
        "count":        len(relevant),
        "average":      avg,
        "top_sites_avg": top25_avg,
        "highest":      high,
        "lowest":       low,
        "brand_type":   brand_type
    }


def get_percentile(score, brand_type="restaurant"):
    """Returns what percentile this score falls in vs benchmarks."""
    relevant = [
        s for _, btype, s, _ in BENCHMARK_DATA
        if btype == brand_type
    ]

    if not relevant:
        relevant = [s for _, _, s, _ in BENCHMARK_DATA]

    below = sum(1 for s in relevant if s < score)
    percentile = round((below / len(relevant)) * 100)
    return percentile


def get_category_context(score, brand_type="restaurant"):
    """Returns a human-readable benchmark context string."""
    stats      = get_benchmark_stats(brand_type)
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
        "percentile":   percentile,
        "tier":         tier,
        "stats":        stats,
        "context":      (
            f"This site scores {score} — placing it in the {tier} "
            f"benchmarked {brand_type} locations in Ahmedabad "
            f"(avg: {stats['average']}, top sites: {stats['top_sites_avg']})."
        )
    }