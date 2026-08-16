"""
Integration Tests for Price Tracker Service
"""

from unittest.mock import MagicMock
import pytest
from database.sql_database import SQLDatabase
from database.mongo_database import MongoDatabase
from services.price_tracker import PriceTrackerService


@pytest.fixture
def service_fixture():
    sql_db = SQLDatabase(db_url="sqlite:///:memory:")
    sql_db.init_db()

    mongo_mock = MagicMock(spec=MongoDatabase)
    mongo_mock.insert_raw_scrape.return_value = "mocked_mongo_id_123"

    scraper_mock = MagicMock()
    scraper_mock.scrape_product.return_value = {
        "title": "Clean Code",
        "price": 32.50,
        "in_stock": True,
        "rating": 4.8,
        "category": "Tech Books",
        "raw_data": {"isbn": "9780132350884"},
        "html_snapshot": "<html>mock</html>",
    }

    service = PriceTrackerService(
        sql_db=sql_db,
        mongo_db=mongo_mock,
        scraper=scraper_mock,
    )
    return service, sql_db, mongo_mock


def test_add_product_to_track(service_fixture):
    service, sql_db, mongo_mock = service_fixture

    product = service.add_product_to_track(
        url="https://books.toscrape.com/mock-item",
        target_price=35.0,
        category="Tech Books",
    )

    assert product is not None
    assert product.title == "Clean Code"
    assert product.current_price == 32.50
    assert product.is_target_met is True
    assert mongo_mock.insert_raw_scrape.called


def test_get_product_details_with_analytics(service_fixture):
    service, sql_db, _ = service_fixture

    prod = service.add_product_to_track(url="https://books.toscrape.com/mock-item")
    details = service.get_product_details_with_analytics(prod.id)

    assert details is not None
    assert details["product"]["title"] == "Clean Code"
    assert details["statistics"]["current_price"] == 32.50
    assert "charts" in details
