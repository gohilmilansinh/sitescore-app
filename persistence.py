from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Try Supabase first, fall back to local file history
try:
    import db as _db
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False


def _get_session_id() -> str:
    """Get stable session ID."""
    try:
        import streamlit as st
        ctx = st.runtime.scriptrunner.get_script_run_ctx()
        if ctx:
            return ctx.session_id.replace("-", "")[:32]
    except Exception:
        pass
    return "local_session"


def load_history() -> List[Dict[str, Any]]:
    """Load history — Supabase if configured, else local file."""
    if _SUPABASE_AVAILABLE and _db.is_configured():
        session_id = _get_session_id()
        return _db.get_history(session_id)
    else:
        return _load_local_history()


def save_to_history(result: Dict[str, Any]) -> None:
    """Save scored site to history."""
    if _SUPABASE_AVAILABLE and _db.is_configured():
        session_id = _get_session_id()
        _db.save_site(session_id, result)
    else:
        _save_local_history(result)


def clear_history() -> None:
    """Clear all history for this session."""
    if _SUPABASE_AVAILABLE and _db.is_configured():
        session_id = _get_session_id()
        _db.clear_session_history(session_id)
    else:
        _clear_local_history()


def update_notes(record_id: str, notes: str) -> bool:
    """Update notes on a history record."""
    if _SUPABASE_AVAILABLE and _db.is_configured():
        return _db.update_notes(record_id, notes)
    return False


def is_db_connected() -> bool:
    """Check if database is connected."""
    return _SUPABASE_AVAILABLE and _db.is_configured()


# ── Local file fallback ───────────────────────────────────
import json
import os
import tempfile
from datetime import datetime


def _get_local_path() -> str:
    try:
        import streamlit as st
        ctx = st.runtime.scriptrunner.get_script_run_ctx()
        if ctx:
            sid = ctx.session_id.replace("-", "")[:16]
            return os.path.join(
                tempfile.gettempdir(),
                f"siteiq_history_{sid}.json"
            )
    except Exception:
        pass
    return os.path.join(
        tempfile.gettempdir(), "siteiq_history.json")


def _load_local_history() -> List[Dict[str, Any]]:
    try:
        path = _get_local_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Local history load failed: %s", e)
    return []


def _save_local_history(result: Dict[str, Any]) -> None:
    history = _load_local_history()
    entry = {
        "timestamp":   datetime.now().strftime(
            "%d %b %Y, %I:%M %p"),
        "address":     result.get("address", ""),
        "brand_type":  result.get("brand_type", "restaurant"),
        "total_score": result.get("total_score", 0),
        "verdict":     result.get("verdict", ""),
        "scores":      result.get("scores", {}),
        "lat":         result.get("lat", 0),
        "lng":         result.get("lng", 0),
        "mode":        result.get("mode", "single"),
        "id":          "",
    }
    history = [
        h for h in history
        if h.get("address") != result.get("address")
    ]
    history.insert(0, entry)
    history = history[:50]
    try:
        with open(_get_local_path(), "w",
                  encoding="utf-8") as f:
            json.dump(history, f)
    except Exception as e:
        logger.warning("Local history save failed: %s", e)


def _clear_local_history() -> None:
    try:
        path = _get_local_path()
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning("Local history clear failed: %s", e)