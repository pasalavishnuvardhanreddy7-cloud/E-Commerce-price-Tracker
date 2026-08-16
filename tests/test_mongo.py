import pytest
from database.mongo_database import MongoDatabase


@pytest.fixture
def mongo_db():
    db = MongoDatabase(db_name="test_ecommerce_raw_data")
    if not db.ping():
        pytest.skip("MongoDB server is not reachable on localhost:27017")
    yield db
    db.client.drop_database("test_ecommerce_raw_data")
    db.close()


def test_mongo_ping(mongo_db):
    assert mongo_db.ping() is True


def test_insert_and_retrieve_raw_scrape(mongo_db):
    test_payload = {
        "raw_title": "Wireless Headphones",
        "raw_price": "$129.99",
        "raw_rating": "4.5 out of 5 stars",
        "raw_specs": {"Battery": "40h", "Bluetooth": "5.3"},
    }

    doc_id = mongo_db.insert_raw_scrape(
        product_id=101,
        url="https://example.com/headphones",
        http_status=200,
        raw_data=test_payload,
        html_snapshot="<div>Sample HTML block</div>",
    )

    assert doc_id is not None

    latest = mongo_db.get_latest_raw_scrape(product_id=101)
    assert latest is not None
    assert latest["product_id"] == 101
    assert latest["raw_data"]["raw_price"] == "$129.99"
    assert latest["raw_data"]["raw_specs"]["Battery"] == "40h"


def test_get_scrape_history(mongo_db):
    for price in ["$10.00", "$12.00", "$9.50"]:
        mongo_db.insert_raw_scrape(
            product_id=202,
            url="https://example.com/item",
            http_status=200,
            raw_data={"price_str": price},
        )

    history = mongo_db.get_scrape_history(product_id=202, limit=5)
    assert len(history) == 3
    assert history[0]["raw_data"]["price_str"] == "$9.50"
