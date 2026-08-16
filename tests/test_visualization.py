"""
Unit Tests for Data Visualization Engine
"""

from visualization.charts import ChartGenerator


def test_empty_chart_generation():
    chart = ChartGenerator.generate_price_history_chart([], "Empty Item")
    assert chart is None


def test_price_history_chart_success():
    records = [
        {"price": 100.0, "scraped_at": "2026-08-01T10:00:00Z"},
        {"price": 95.0, "scraped_at": "2026-08-02T10:00:00Z"},
        {"price": 89.99, "scraped_at": "2026-08-03T10:00:00Z"},
    ]
    chart_data = ChartGenerator.generate_price_history_chart(
        records=records,
        product_title="Wireless Keyboard",
        target_price=90.0,
    )

    assert chart_data is not None
    assert chart_data.startswith("data:image/png;base64,")
    assert len(chart_data) > 100


def test_price_distribution_chart_success():
    records = [
        {"price": 50.0, "scraped_at": "2026-08-01"},
        {"price": 55.0, "scraped_at": "2026-08-02"},
        {"price": 48.0, "scraped_at": "2026-08-03"},
    ]
    dist_chart = ChartGenerator.generate_price_distribution_chart(
        records=records,
        product_title="Gaming Mouse",
    )

    assert dist_chart is not None
    assert dist_chart.startswith("data:image/png;base64,")
