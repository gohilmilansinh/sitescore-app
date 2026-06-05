import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import scorer


def test_validate_address_rejects_short_address():
    valid, message = scorer.validate_address("Abc")
    assert not valid
    assert "too short" in message.lower()


def test_validate_address_rejects_non_gujarat():
    valid, message = scorer.validate_address("Powai, Mumbai")
    assert not valid
    assert "does not appear to be in gujarat" in message.lower()


def test_geocode_no_client_returns_none(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", None)
    assert scorer.geocode("Bopal, Ahmedabad, Gujarat") == (None, None)


def test_score_competition_with_places(monkeypatch):
    class DummyGMAPS:
        def places_nearby(self, *args, **kwargs):
            return {
                "results": [
                    {"name": "A", "user_ratings_total": 100, "rating": 4.5},
                    {"name": "B", "user_ratings_total": 10, "rating": 3.0},
                ]
            }

    monkeypatch.setattr(scorer, "gmaps", DummyGMAPS())
    score, details = scorer.score_competition(23.0, 72.0)
    assert 0 <= score <= 100
    assert len(details) == 2
    assert details[0]["name"] == "A"


def test_score_spending_power_calculates_average(monkeypatch):
    class DummyGMAPS:
        def places_nearby(self, *args, **kwargs):
            return {"results": [{"price_level": 1}, {"price_level": 3}, {"price_level": 2}]}

    monkeypatch.setattr(scorer, "gmaps", DummyGMAPS())
    score, data = scorer.score_spending_power(23.0, 72.0)
    assert score == round(min((1 + 3 + 2) / 3 / 4 * 100, 100), 1)
    assert data["sample_size"] == 3
    assert data["distribution"]["budget (0-1)"] == 1


def test_score_site_returns_error_for_invalid_address():
    result = scorer.score_site("mumbai")
    assert "error" in result
    assert "gujarat" in result["error"].lower()


def test_score_site_uses_fallback_with_no_gmaps(monkeypatch):
    monkeypatch.setattr(scorer, "validate_address", lambda address: (True, "Valid"))
    monkeypatch.setattr(scorer, "cached_geocode", lambda address: (23.0, 72.0))
    monkeypatch.setattr(scorer, "gmaps", None)

    result = scorer.score_site("Bopal, Ahmedabad, Gujarat")
    assert result["scores"]["footfall"] == 50.0
    assert result["scores"]["competition"] == 50.0
    assert result["scores"]["catchment"] == 30.0
    assert result["scores"]["spending_power"] == 50.0
    assert "total_score" in result
    assert result["verdict"] in {"Strong", "Moderate", "Weak"}


def test_score_footfall_no_gmaps_returns_default(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", None)
    score, data = scorer.score_footfall(23.0, 72.0)
    assert score == 50.0
    assert data == {}


def test_score_catchment_no_gmaps_returns_default(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", None)
    score, count = scorer.score_catchment(23.0, 72.0)
    assert score == 30.0
    assert count == 0


def test_score_spending_power_no_gmaps_returns_default(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", None)
    score, data = scorer.score_spending_power(23.0, 72.0)
    assert score == 50.0
    assert data["sample_size"] == 0


def test_score_competition_no_gmaps_returns_default(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", None)
    score, details = scorer.score_competition(23.0, 72.0)
    assert score == 50.0
    assert details == []


class DummyGMAPS:
    def __init__(self, results=None, raise_on=None):
        self._results = results or []
        self._raise_on = raise_on

    def places_nearby(self, *args, **kwargs):
        if self._raise_on:
            raise RuntimeError(self._raise_on)
        return {"results": self._results}

    def geocode(self, address):
        return [{"geometry": {"location": {"lat": 23.0, "lng": 72.0}},
                 "address_components": [{"types": ["administrative_area_level_1"], "long_name": "Gujarat"}],
                 "formatted_address": "Ahmedabad, Gujarat, India"}]


def test_score_demand_fallback(monkeypatch):
    monkeypatch.setattr(scorer, "score_population", lambda lat, lng: (0.0, {"estimated_population": 0}))
    class DummyOx:
        @staticmethod
        def features_from_point(point, tags, dist):
            return [1] * 10
    monkeypatch.setattr(scorer, "ox", DummyOx)

    score, data = scorer.score_demand(23.0, 72.0)
    assert score == 5.0
    assert data["method"] == "osm_buildings"
    assert data["count"] == 10


def test_score_competition_no_places(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", DummyGMAPS(results=[]))
    score, details = scorer.score_competition(23.0, 72.0)
    assert score == 100.0
    assert details == []


def test_score_competition_exception(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", DummyGMAPS(raise_on="fail"))
    score, details = scorer.score_competition(23.0, 72.0)
    assert score == 50.0
    assert details == []


def test_score_spending_power_empty(monkeypatch):
    monkeypatch.setattr(scorer, "gmaps", DummyGMAPS(results=[]))
    score, data = scorer.score_spending_power(23.0, 72.0)
    assert score == 50.0
    assert data["sample_size"] == 0


def test_score_site_computes_total(monkeypatch):
    monkeypatch.setattr(scorer, "validate_address", lambda address: (True, "Valid"))
    monkeypatch.setattr(scorer, "cached_geocode", lambda address: (23.0, 72.0))
    monkeypatch.setattr(scorer, "cached_demand", lambda lat, lng: (80.0, {}))
    monkeypatch.setattr(scorer, "cached_footfall", lambda lat, lng, bt: (60.0, {}))
    monkeypatch.setattr(scorer, "cached_competition", lambda lat, lng, bt: (70.0, []))
    monkeypatch.setattr(scorer, "cached_accessibility", lambda lat, lng: (50.0, {"intersections": 5, "total_nodes": 20}))
    monkeypatch.setattr(scorer, "cached_catchment", lambda lat, lng: (40.0, 5))
    monkeypatch.setattr(scorer, "cached_spending", lambda lat, lng: (30.0, {}))

    result = scorer.score_site("Bopal, Ahmedabad, Gujarat")
    assert result["total_score"] == round(
        80 * scorer.WEIGHTS["demand"]
        + 60 * scorer.WEIGHTS["footfall"]
        + 70 * scorer.WEIGHTS["competition"]
        + 50 * scorer.WEIGHTS["accessibility"]
        + 40 * scorer.WEIGHTS["catchment"]
        + 30 * scorer.WEIGHTS["spending_power"], 1
    )
    assert result["verdict"] in {"Strong", "Moderate", "Weak"}
