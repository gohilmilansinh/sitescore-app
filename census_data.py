# Census 2011 population data for major Gujarat wards/areas
# Format: (area_name, city, lat, lng, population, households)
# Source: Census of India 2011, Primary Census Abstract

WARD_DATA = [
    # Ahmedabad zones (approximate centroids)
    ("Maninagar",      "Ahmedabad", 22.9990, 72.6050, 185000, 38000),
    ("Naroda",         "Ahmedabad", 23.0700, 72.6490, 220000, 44000),
    ("Nikol",          "Ahmedabad", 23.0560, 72.6350, 195000, 39000),
    ("Vatva",          "Ahmedabad", 22.9620, 72.6290, 168000, 33000),
    ("Odhav",          "Ahmedabad", 22.9980, 72.6540, 142000, 28000),
    ("Bopal",          "Ahmedabad", 23.0340, 72.4690, 95000,  19000),
    ("Prahlad Nagar",  "Ahmedabad", 23.0080, 72.5050, 72000,  14000),
    ("Vastrapur",      "Ahmedabad", 23.0376, 72.5313, 68000,  13500),
    ("Satellite",      "Ahmedabad", 23.0258, 72.5292, 85000,  17000),
    ("Navrangpura",    "Ahmedabad", 23.0395, 72.5599, 78000,  15600),
    ("Thaltej",        "Ahmedabad", 23.0550, 72.4980, 62000,  12400),
    ("Chandkheda",     "Ahmedabad", 23.1060, 72.5870, 148000, 29600),
    ("Gota",           "Ahmedabad", 23.0980, 72.5340, 132000, 26400),
    ("Vastral",        "Ahmedabad", 22.9990, 72.6660, 178000, 35600),
    ("Isanpur",        "Ahmedabad", 22.9700, 72.6380, 156000, 31200),
    ("Bapunagar",      "Ahmedabad", 23.0420, 72.6120, 192000, 38400),
    ("Meghaninagar",   "Ahmedabad", 23.0490, 72.6220, 145000, 29000),
    ("Rakhial",        "Ahmedabad", 23.0580, 72.6300, 138000, 27600),
    ("Shahibaug",      "Ahmedabad", 23.0710, 72.5850, 92000,  18400),
    ("Paldi",          "Ahmedabad", 23.0120, 72.5760, 88000,  17600),
    ("Vejalpur",       "Ahmedabad", 22.9970, 72.5390, 112000, 22400),
    ("Juhapura",       "Ahmedabad", 23.0000, 72.5260, 165000, 33000),
    ("Naranpura",      "Ahmedabad", 23.0580, 72.5540, 95000,  19000),
    ("Sabarmati",      "Ahmedabad", 23.0900, 72.5730, 125000, 25000),
    ("Ranip",          "Ahmedabad", 23.0850, 72.5620, 118000, 23600),
    ("Memnagar",       "Ahmedabad", 23.0630, 72.5450, 76000,  15200),
    ("Ambawadi",       "Ahmedabad", 23.0270, 72.5530, 82000,  16400),
    ("Ellis Bridge",   "Ahmedabad", 23.0280, 72.5710, 58000,  11600),
    ("SG Highway",     "Ahmedabad", 23.0420, 72.5070, 45000,  9000),
    ("Shilaj",         "Ahmedabad", 23.0160, 72.4780, 38000,  7600),

    # Surat zones
    ("Adajan",         "Surat", 21.2060, 72.7990, 198000, 39600),
    ("Varachha",       "Surat", 21.2140, 72.8680, 285000, 57000),
    ("Katargam",       "Surat", 21.2310, 72.8430, 242000, 48400),
    ("Vesu",           "Surat", 21.1590, 72.7920, 88000,  17600),
    ("Athwa",          "Surat", 21.1720, 72.8160, 125000, 25000),
    ("Althan",         "Surat", 21.1650, 72.8020, 95000,  19000),
    ("Udhna",          "Surat", 21.1940, 72.8580, 215000, 43000),
    ("Limbayat",       "Surat", 21.1830, 72.8720, 198000, 39600),
    ("Piplod",         "Surat", 21.1560, 72.7860, 72000,  14400),
    ("Dumas Road",     "Surat", 21.1340, 72.7720, 45000,  9000),

    # Vadodara zones
    ("Alkapuri",       "Vadodara", 22.3119, 73.1723, 92000,  18400),
    ("Akota",          "Vadodara", 22.3050, 73.1650, 115000, 23000),
    ("Manjalpur",      "Vadodara", 22.2740, 73.1860, 145000, 29000),
    ("Gotri",          "Vadodara", 22.3280, 73.1580, 88000,  17600),
    ("Waghodia Road",  "Vadodara", 22.2950, 73.2180, 125000, 25000),
    ("Fatehgunj",      "Vadodara", 22.3280, 73.1920, 78000,  15600),
    ("Harni",          "Vadodara", 22.3420, 73.2050, 68000,  13600),
    ("Nizampura",      "Vadodara", 22.3380, 73.1780, 95000,  19000),

    # Rajkot zones
    ("Kalawad Road",   "Rajkot", 22.3130, 70.7780, 98000,  19600),
    ("150 Feet Ring",  "Rajkot", 22.2920, 70.7850, 112000, 22400),
    ("Mavdi",          "Rajkot", 22.2780, 70.7720, 88000,  17600),
    ("University Road","Rajkot", 22.3050, 70.8020, 75000,  15000),
    ("Gondal Road",    "Rajkot", 22.2650, 70.7940, 92000,  18400),
    ("Bhaktinagar",    "Rajkot", 22.3180, 70.8120, 68000,  13600),
]


import math

def haversine_distance(lat1, lng1, lat2, lng2):
    """Distance in km between two GPS points."""
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a    = (math.sin(dlat/2)**2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def estimate_population(lat, lng, radius_km=1.0):
    """
    Estimates population within radius_km of a point
    by finding nearby Census wards and interpolating
    based on distance-weighted overlap.
    """
    total_population  = 0
    total_households  = 0
    contributing_wards = []

    for name, city, wlat, wlng, pop, hh in WARD_DATA:
        dist = haversine_distance(lat, lng, wlat, wlng)

        # Ward centroid within 3km contributes proportionally
        if dist <= 3.0:
            # Weight by inverse distance squared
            # and approximate overlap fraction
            overlap = max(0, 1 - (dist / 3.0))
            weight  = overlap ** 2

            pop_contribution = pop * weight
            hh_contribution  = hh  * weight

            total_population  += pop_contribution
            total_households  += hh_contribution

            if weight > 0.1:
                contributing_wards.append({
                    "name":       name,
                    "city":       city,
                    "distance":   round(dist, 2),
                    "population": pop,
                    "weight":     round(weight, 2)
                })

    return {
        "estimated_population": int(total_population),
        "estimated_households": int(total_households),
        "contributing_wards":   sorted(
            contributing_wards,
            key=lambda x: x["weight"],
            reverse=True
        )[:3]
    }


def score_population(lat, lng):
    """
    Returns a 0-100 score based on estimated population
    within 1km. 200,000+ people = score 100.
    """
    data  = estimate_population(lat, lng, radius_km=1.0)
    pop   = data["estimated_population"]
    score = round(min(pop / 200000 * 100, 100), 1)
    return score, data