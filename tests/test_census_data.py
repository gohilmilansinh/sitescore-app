from census_data import haversine_distance, score_population


def test_haversine_distance_same_point():
    assert haversine_distance(23.0225, 72.5714, 23.0225, 72.5714) == 0.0


def test_score_population_ahmedabad():
    score, data = score_population(23.0225, 72.5714)
    assert isinstance(score, float)
    assert score >= 0
    assert data["estimated_population"] >= 0
    assert "contributing_wards" in data
