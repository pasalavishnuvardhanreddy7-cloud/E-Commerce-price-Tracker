"""
Unit Tests for Price Analytics Engine
"""

from analytics.price_analysis import PriceAnalyzer


def test_empty_dataset_handling():
    analyzer = PriceAnalyzer([])
    assert analyzer.is_valid() is False
    stats = analyzer.compute_summary_statistics()
    assert stats["current_price"] is None
    assert stats["total_observations"] == 0


def test_summary_statistics_calculations():
    sample_records = [
        {"price": 100.0, "scraped_at": "2026-08-01T10:00:00Z"},
        {"price": 120.0, "scraped_at": "2026-08-02T10:00:00Z"},
        {"price": 80.0, "scraped_at": "2026-08-03T10:00:00Z"},
        {"price": 100.0, "scraped_at": "2026-08-04T10:00:00Z"},
    ]

    analyzer = PriceAnalyzer(sample_records)
    assert analyzer.is_valid() is True

    stats = analyzer.compute_summary_statistics()
    assert stats["current_price"] == 100.0
    assert stats["min_price"] == 80.0
    assert stats["max_price"] == 120.0
    assert stats["mean_price"] == 100.0
    assert stats["median_price"] == 100.0
    assert stats["total_observations"] == 4


def test_moving_averages():
    sample_records = [
        {"price": 50.0, "scraped_at": "2026-08-01"},
        {"price": 60.0, "scraped_at": "2026-08-02"},
        {"price": 70.0, "scraped_at": "2026-08-03"},
    ]
    analyzer = PriceAnalyzer(sample_records)
    ma_df = analyzer.compute_moving_averages(window_sizes=[2])

    assert "ma_2" in ma_df.columns
    # Rolling 2 on [50, 60, 70] -> [50.0, 55.0, 65.0]
    assert list(ma_df["ma_2"]) == [50.0, 55.0, 65.0]


def test_recommendation_logic():
    sample_records = [
        {"price": 100.0, "scraped_at": "2026-08-01"},
        {"price": 70.0, "scraped_at": "2026-08-02"},
    ]
    analyzer = PriceAnalyzer(sample_records)

    # Target met
    rec_target = analyzer.generate_recommendation(target_price=75.0)
    assert rec_target["action"] == "BUY_NOW"

    # All-time low
    rec_low = analyzer.generate_recommendation()
    assert rec_low["action"] == "BUY_NOW"
