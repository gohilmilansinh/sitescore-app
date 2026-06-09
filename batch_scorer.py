from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
import pandas as pd
from scorer import score_site
from roi_calculator import calculate_roi


REQUIRED_COLUMNS = ["address"]

OPTIONAL_COLUMNS = {
    "brand_type":    "restaurant",
    "monthly_rent":  0,
    "notes":         "",
}


def validate_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate uploaded CSV has required columns."""
    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]
    if missing:
        return False, (
            f"Missing required column: {', '.join(missing)}. "
            f"CSV must have an 'address' column."
        )
    if len(df) == 0:
        return False, "CSV file is empty."
    if len(df) > 20:
        return False, (
            f"Too many rows ({len(df)}). "
            f"Maximum 20 sites per batch."
        )
    return True, "Valid"


def score_batch(
    df: pd.DataFrame,
    progress_callback: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    Score all addresses in a dataframe.
    Returns list of result dicts with original CSV data merged in.
    """
    results = []

    for i, row in df.iterrows():
        address    = str(row.get("address", "")).strip()
        brand_type = str(
            row.get("brand_type",
                    OPTIONAL_COLUMNS["brand_type"])
        ).strip().lower()
        monthly_rent = float(
            row.get("monthly_rent",
                    OPTIONAL_COLUMNS["monthly_rent"]) or 0
        )
        notes = str(
            row.get("notes", OPTIONAL_COLUMNS["notes"]) or ""
        ).strip()

        if not address:
            continue

        # Validate brand type
        valid_types = [
            "restaurant", "pharmacy",
            "supermarket", "bank", "school"
        ]
        if brand_type not in valid_types:
            brand_type = "restaurant"

        # Score the site
        result = score_site(address, brand_type)

        entry = {
            "row":        i + 1,
            "address":    address,
            "brand_type": brand_type,
            "notes":      notes,
        }

        if result and "error" not in result:
            entry.update({
                "status":          "scored",
                "total_score":     result["total_score"],
                "verdict":         result["verdict"],
                "demand":          result["scores"]["demand"],
                "footfall":        result["scores"]["footfall"],
                "competition":     result["scores"]["competition"],
                "accessibility":   result["scores"]["accessibility"],
                "catchment":       result["scores"]["catchment"],
                "spending_power":  result["scores"]["spending_power"],
                "lat":             result["lat"],
                "lng":             result["lng"],
                "full_result":     result,
            })

            # Add ROI if rent provided
            if monthly_rent > 0:
                roi = calculate_roi(
                    total_score=result["total_score"],
                    monthly_rent=monthly_rent,
                    brand_type=brand_type,
                )
                entry.update({
                    "monthly_rent":       monthly_rent,
                    "est_revenue":        roi["est_monthly_revenue"],
                    "monthly_profit":     roi["monthly_profit"],
                    "roi_score":          roi["roi_score"],
                    "combined_score":     roi["combined_score"],
                    "rent_label":         roi["rent_label"],
                    "payback_months":     roi["payback_months"],
                    "roi_verdict":        roi["verdict"],
                })
            else:
                entry["monthly_rent"] = 0

        elif result and "error" in result:
            entry.update({
                "status":      "error",
                "total_score": 0,
                "verdict":     "Error",
                "error_msg":   result["error"],
            })
        else:
            entry.update({
                "status":      "error",
                "total_score": 0,
                "verdict":     "Error",
                "error_msg":   "Scoring failed",
            })

        results.append(entry)

        if progress_callback:
            progress_callback(i + 1, len(df), address)

        # Small delay to avoid API rate limits
        time.sleep(0.5)

    # Sort by total_score descending
    results.sort(
        key=lambda x: x.get("total_score", 0),
        reverse=True
    )
    return results


def results_to_dataframe(
    results: List[Dict[str, Any]]
) -> pd.DataFrame:
    """Convert batch results to a clean exportable dataframe."""
    rows = []
    for r in results:
        row = {
            "Rank":          results.index(r) + 1,
            "Address":       r["address"],
            "Brand Type":    r["brand_type"],
            "Status":        r.get("status", "error"),
            "Total Score":   r.get("total_score", 0),
            "Verdict":       r.get("verdict", "Error"),
            "Demand":        r.get("demand", ""),
            "Footfall":      r.get("footfall", ""),
            "Competition":   r.get("competition", ""),
            "Accessibility": r.get("accessibility", ""),
            "Catchment":     r.get("catchment", ""),
            "Spending Power":r.get("spending_power", ""),
            "Monthly Rent":  r.get("monthly_rent", ""),
            "Est. Revenue":  r.get("est_revenue", ""),
            "Monthly Profit":r.get("monthly_profit", ""),
            "ROI Score":     r.get("roi_score", ""),
            "Payback (months)": r.get("payback_months", ""),
            "Rent Rating":   r.get("rent_label", ""),
            "Notes":         r.get("notes", ""),
            "Lat":           r.get("lat", ""),
            "Lng":           r.get("lng", ""),
        }
        if r.get("status") == "error":
            row["Notes"] = r.get("error_msg", "Scoring failed")
        rows.append(row)
    return pd.DataFrame(rows)