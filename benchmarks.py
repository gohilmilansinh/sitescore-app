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

    # Surat QSR locations
    ("Domino's Pizza, Adajan, Surat",       "restaurant", 81.0, "residential"),
    ("KFC, VR Mall, Surat",                 "restaurant", 86.0, "mall"),
    ("McDonald's, Varachha, Surat",         "restaurant", 74.0, "commercial"),
    ("Pizza Hut, Vesu, Surat",              "restaurant", 78.0, "residential"),
    ("Wow Momo, Athwa, Surat",              "restaurant", 82.0, "high_street"),

    # Vadodara QSR locations
    ("Domino's Pizza, Alkapuri, Vadodara",  "restaurant", 83.0, "high_street"),
    ("KFC, Akota, Vadodara",                "restaurant", 79.0, "residential"),
    ("McDonald's, Manjalpur, Vadodara",     "restaurant", 76.0, "suburban"),

    # Rajkot QSR locations
    ("Domino's Pizza, Kalawad Road, Rajkot","restaurant", 77.0, "high_street"),
    ("KFC, 150 Feet Ring Road, Rajkot",     "restaurant", 81.0, "highway"),

    # Surat pharmacy
    ("Apollo Pharmacy, Adajan, Surat",      "pharmacy",   79.0, "residential"),
    ("MedPlus, Varachha, Surat",            "pharmacy",   72.0, "commercial"),

    # Vadodara pharmacy
    ("Apollo Pharmacy, Alkapuri, Vadodara", "pharmacy",   81.0, "high_street"),
]


def get_benchmark_stats(brand_type="restaurant"):
    relevant = [
        (score, addr) for addr, btype, score, cat
        in BENCHMARK_DATA if btype == brand_type
    ]

    if not relevant:
        relevant = [(score, addr) for _, _, score, _ in BENCHMARK_DATA]

    scores_only = [s for s, _ in relevant]
    avg         = round(sum(scores_only) / len(scores_only), 1)
    high        = max(scores_only)
    low         = min(scores_only)
    top25       = sorted(scores_only, reverse=True)
    top25_avg   = round(
        sum(top25[:max(1, len(top25)//4)]) /
        max(1, len(top25)//4), 1
    )

    # City breakdown
    city_counts = {}
    for score, addr in relevant:
        for city in ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]:
            if city.lower() in addr.lower():
                city_counts[city] = city_counts.get(city, 0) + 1

    return {
        "count":         len(scores_only),
        "average":       avg,
        "top_sites_avg": top25_avg,
        "highest":       high,
        "lowest":        low,
        "brand_type":    brand_type,
        "cities":        city_counts
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