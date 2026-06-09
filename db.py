from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_client():
    """Get Supabase client. Returns None if not configured."""
    try:
        import streamlit as st
        url = (
            st.secrets.get("SUPABASE_URL", "") or
            os.environ.get("SUPABASE_URL", "")
        )
        key = (
            st.secrets.get("SUPABASE_KEY", "") or
            os.environ.get("SUPABASE_KEY", "")
        )
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        logger.warning(
            "Supabase not configured — "
            "using local history fallback."
        )
        return None

    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning("Supabase client error: %s", e)
        return None


def save_site(
    session_id: str,
    result: Dict[str, Any],
) -> bool:
    """Save a scored site to Supabase."""
    client = _get_client()
    if not client:
        return False

    try:
        data = {
            "session_id":  session_id,
            "address":     result.get("address", ""),
            "brand_type":  result.get("brand_type", "restaurant"),
            "total_score": result.get("total_score", 0),
            "verdict":     result.get("verdict", ""),
            "scores":      result.get("scores", {}),
            "raw":         result.get("raw", {}),
            "lat":         result.get("lat", 0),
            "lng":         result.get("lng", 0),
            "mode":        result.get("mode", "single"),
            "roi":         result.get("roi"),
            "notes":       "",
        }
        client.table("site_history").insert(data).execute()
        return True
    except Exception as e:
        logger.warning("Failed to save site: %s", e)
        return False


def get_history(
    session_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get scored site history for a session."""
    client = _get_client()
    if not client:
        return []

    try:
        response = (
            client.table("site_history")
            .select("*")
            .eq("session_id", session_id)
            .order("scored_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = response.data or []

        # Convert to history format
        history = []
        for row in rows:
            scores = row.get("scores") or {}
            history.append({
                "timestamp":   _format_ts(row.get("scored_at", "")),
                "address":     row.get("address", ""),
                "brand_type":  row.get("brand_type", "restaurant"),
                "total_score": row.get("total_score", 0),
                "verdict":     row.get("verdict", ""),
                "scores":      scores,
                "lat":         row.get("lat", 0),
                "lng":         row.get("lng", 0),
                "mode":        row.get("mode", "single"),
                "roi":         row.get("roi"),
                "notes":       row.get("notes", ""),
                "id":          row.get("id", ""),
            })
        return history
    except Exception as e:
        logger.warning("Failed to get history: %s", e)
        return []


def delete_site(record_id: str) -> bool:
    """Delete a single history record."""
    client = _get_client()
    if not client:
        return False
    try:
        client.table("site_history").delete().eq(
            "id", record_id).execute()
        return True
    except Exception as e:
        logger.warning("Failed to delete site: %s", e)
        return False


def clear_session_history(session_id: str) -> bool:
    """Delete all history for a session."""
    client = _get_client()
    if not client:
        return False
    try:
        client.table("site_history").delete().eq(
            "session_id", session_id).execute()
        return True
    except Exception as e:
        logger.warning("Failed to clear history: %s", e)
        return False


def update_notes(record_id: str, notes: str) -> bool:
    """Update notes for a history record."""
    client = _get_client()
    if not client:
        return False
    try:
        client.table("site_history").update(
            {"notes": notes}
        ).eq("id", record_id).execute()
        return True
    except Exception as e:
        logger.warning("Failed to update notes: %s", e)
        return False


def is_configured() -> bool:
    """Check if Supabase is configured."""
    return _get_client() is not None


def _format_ts(ts: str) -> str:
    """Format ISO timestamp to readable string."""
    if not ts:
        return ""
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(
            ts.replace("Z", "+00:00"))
        local = dt.astimezone()
        return local.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return ts[:16]