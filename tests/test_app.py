"""
Functional Web Route Tests
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_dashboard_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"PricePulse" in response.data


def test_add_page_route(client):
    response = client.get("/add")
    assert response.status_code == 200
    assert b"Track New Product" in response.data
