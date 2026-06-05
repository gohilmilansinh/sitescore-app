from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, List

import streamlit as st
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_history_file() -> str:
    """Each user gets their own history file based on session ID."""
    session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id
    safe_id = session_id.replace("-", "")[:16]
    return f"/tmp/sitescore_history_{safe_id}.json"


def load_history() -> List[Dict[str, Any]]:
    try:
        path = _get_history_file()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Unable to load history file: %s", exc)
    return []


def save_to_history(result: Dict[str, Any]) -> Dict[str, Any]:
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "address": result["address"],
        "brand_type": result.get("brand_type", "restaurant"),
        "total_score": result["total_score"],
        "verdict": result["verdict"],
        "scores": result["scores"],
        "lat": result["lat"],
        "lng": result["lng"],
        "mode": result.get("mode", "single"),
    }
    history = [h for h in history if h.get("address") != result["address"]]
    history.insert(0, entry)
    history = history[:50]
    try:
        path = _get_history_file()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f)
    except OSError as exc:
        logger.warning("Unable to save history file: %s", exc)
    return entry


def clear_history() -> None:
    try:
        path = _get_history_file()
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Unable to clear history file: %s", exc)
