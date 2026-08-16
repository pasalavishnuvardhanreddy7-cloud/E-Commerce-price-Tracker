from bs4 import BeautifulSoup
from scraper.product_scraper import ProductScraper


def test_clean_price():
    scraper = ProductScraper()
    assert scraper._clean_price("51.77") == 51.77
    assert scraper._clean_price("$1,299.99") == 1299.99
    assert scraper._clean_price("Price: 19.50 EUR") == 19.50
    assert scraper._clean_price("Invalid") is None


def test_parse_rating():
    scraper = ProductScraper()
    html = '<p class="star-rating Four"></p>'
    soup = BeautifulSoup(html, "html.parser")
    assert scraper._parse_rating(soup) == 4.0


def test_live_scrape_sample_product():
    scraper = ProductScraper(delay_seconds=0.1)
    target_url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    result = scraper.scrape_product(target_url)

    assert result is not None
    assert result["title"] == "A Light in the Attic"
    assert result["price"] > 0.0
    assert result["in_stock"] is True
    assert result["category"] == "Poetry"
    assert result["rating"] == 3.0
    assert "specifications" in result["raw_data"]

    