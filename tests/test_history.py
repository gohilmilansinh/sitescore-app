import json
import os
import tempfile

import history


def test_save_load_clear_history(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "history.json")
        monkeypatch.setattr(history, "_get_history_file", lambda: file_path)

        entry = {
            "address": "Bopal, Ahmedabad, Gujarat",
            "brand_type": "restaurant",
            "total_score": 75.0,
            "verdict": "Strong",
            "scores": {"demand": 80, "footfall": 70},
            "lat": 23.0,
            "lng": 72.0,
        }

        saved = history.save_to_history(entry)
        assert saved["address"] == entry["address"]

        loaded = history.load_history()
        assert len(loaded) == 1
        assert loaded[0]["address"] == entry["address"]

        history.clear_history()
        assert not os.path.exists(file_path)


def test_load_history_invalid_json(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "history.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("not-json")

        monkeypatch.setattr(history, "_get_history_file", lambda: file_path)
        loaded = history.load_history()
        assert loaded == []
