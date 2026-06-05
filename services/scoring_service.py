from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit not available in tests
    st = None

import scorer


def _wrap_cache(fn, ttl: int = 3600):
    if st:
        return st.cache_data(ttl=ttl)(fn)
    return fn


cached_geocode = _wrap_cache(lambda address: scorer.geocode(address))
cached_demand = _wrap_cache(lambda lat, lng: scorer.score_demand(lat, lng))
cached_footfall = _wrap_cache(lambda lat, lng, bt: scorer.score_footfall(lat, lng, bt))
cached_competition = _wrap_cache(lambda lat, lng, bt: scorer.score_competition(lat, lng, bt))
cached_accessibility = _wrap_cache(lambda lat, lng: scorer.score_accessibility(lat, lng))
cached_catchment = _wrap_cache(lambda lat, lng: scorer.score_catchment(lat, lng))
cached_spending = _wrap_cache(lambda lat, lng: scorer.score_spending_power(lat, lng))


if st:
    @st.cache_data(ttl=3600)
    def score_site(address: str, brand_type: str = "restaurant") -> Dict[str, Any]:
        return scorer.score_site(address, brand_type)
else:
    def score_site(address: str, brand_type: str = "restaurant") -> Dict[str, Any]:
        return scorer.score_site(address, brand_type)
