from benchmarks import get_benchmark_stats, get_percentile, get_category_context


def test_get_benchmark_stats_restaurant():
    stats = get_benchmark_stats("restaurant")
    assert stats["brand_type"] == "restaurant"
    assert stats["count"] > 0
    assert stats["average"] >= 0


def test_get_percentile_bounds():
    percentile = get_percentile(50.0, "restaurant")
    assert 0 <= percentile <= 100


def test_get_category_context_contains_context():
    context = get_category_context(80.0, "restaurant")
    assert "context" in context
    assert "tier" in context
