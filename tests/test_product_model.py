"""
Unit Tests for Domain Product Models
Tests OOP calculations, deltas, and serialized dictionaries.
"""

from datetime import datetime, timezone, timedelta
from models.product import Product, PriceRecord


def test_product_price_calculations():
    product = Product(
        title="Mechanical Keyboard",
        url="https://example.com/keyboard",
        target_price=80.0,
        category="Peripherals",
    )

    t0 = datetime.now(timezone.utc) - timedelta(days=2)
    t1 = datetime.now(timezone.utc) - timedelta(days=1)
    t2 = datetime.now(timezone.utc)

    product.add_price_record(PriceRecord(price=100.0, scraped_at=t0))
    product.add_price_record(PriceRecord(price=120.0, scraped_at=t1))
    product.add_price_record(PriceRecord(price=75.0, scraped_at=t2))

    assert product.current_price == 75.0
    assert product.lowest_price == 75.0
    assert product.highest_price == 120.0
    assert product.price_change_percentage == -25.0  # From 100 -> 75 is -25%
    assert product.is_target_met is True


def test_product_to_dict_serialization():
    product = Product(
        id=1,
        title="Wireless Mouse",
        url="https://example.com/mouse",
        target_price=50.0,
    )
    product.add_price_record(PriceRecord(price=45.0))

    data = product.to_dict()
    assert data["id"] == 1
    assert data["title"] == "Wireless Mouse"
    assert data["current_price"] == 45.0
    assert data["is_target_met"] is True
    assert len(data["price_history"]) == 1

    