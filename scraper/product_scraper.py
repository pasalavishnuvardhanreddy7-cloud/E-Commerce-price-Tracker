import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, logger


class ProductScraper(BaseScraper):
    STAR_MAPPING = {
        "One": 1.0,
        "Two": 2.0,
        "Three": 3.0,
        "Four": 4.0,
        "Five": 5.0,
    }

    def _clean_price(self, price_str: str) -> Optional[float]:
        if not price_str:
            return None
        cleaned = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_rating(self, soup: BeautifulSoup) -> Optional[float]:
        star_elem = soup.select_one("p.star-rating")
        if star_elem:
            classes = star_elem.get("class", [])
            for cls in classes:
                if cls in self.STAR_MAPPING:
                    return self.STAR_MAPPING[cls]
        return None

    def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        html = self.fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        try:
            title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"

            price_elem = soup.select_one(".price_color, .product_main .price_color, .price")
            raw_price_str = price_elem.get_text(strip=True) if price_elem else ""
            numeric_price = self._clean_price(raw_price_str)

            if numeric_price is None:
                logger.warning(f"Could not parse valid price from {url}")
                return None

            avail_elem = soup.select_one(".availability, .instock")
            avail_text = avail_elem.get_text(strip=True) if avail_elem else ""
            in_stock = "In stock" in avail_text or "available" in avail_text.lower()

            rating = self._parse_rating(soup)

            category = "General"
            breadcrumb_links = soup.select("ul.breadcrumb li a")
            if len(breadcrumb_links) >= 3:
                category = breadcrumb_links[2].get_text(strip=True)

            raw_specs = {}
            table_rows = soup.select("table.table-striped tr")
            for row in table_rows:
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    raw_specs[th.get_text(strip=True)] = td.get_text(strip=True)

            return {
                "title": title,
                "price": numeric_price,
                "in_stock": in_stock,
                "rating": rating,
                "category": category,
                "url": url,
                "raw_data": {
                    "raw_price_str": raw_price_str,
                    "availability_str": avail_text,
                    "specifications": raw_specs,
                },
                "html_snapshot": html[:2000],
            }

        except Exception as exc:
            logger.error(f"Error parsing DOM for {url}: {exc}")
            return None
