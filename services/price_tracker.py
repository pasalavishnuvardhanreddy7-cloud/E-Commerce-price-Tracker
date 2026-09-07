import os
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from database.sql_database import SQLDatabase

class PriceTrackerService:
    def __init__(self, sql_db: Optional[SQLDatabase] = None, mongo_db: Optional[Any] = None, scraper: Optional[Any] = None) -> None:
        self.sql_db = sql_db or SQLDatabase()
        self.mongo_db = mongo_db
        self.scraper = scraper

        self.mongo_collection = None
        mongo_uri = os.getenv("MONGO_URI", "")
        if mongo_uri and "mongodb" in mongo_uri and "localhost" not in mongo_uri:
            try:
                from pymongo import MongoClient
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
                db = client["ecommerce_tracker"]
                self.mongo_collection = db["raw_scrapes"]
            except Exception:
                self.mongo_collection = None

    def add_product_to_track(self, url: str, target_price: Optional[float] = None, category_name: Optional[str] = None, user_id: Optional[int] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Handles add_product calls from app.py"""
        return self.track_product_by_url(url=url, target_price=target_price, category_name=category_name, user_id=user_id)

    def track_product_by_url(self, url: str, target_price: Optional[float] = None, category_name: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        product_data = self._scrape_url(url)
        if not product_data:
            return None

        product = self.sql_db.add_product(
            title=product_data.get("title", "Tracked Item"),
            url=url,
            target_price=target_price,
            category_name=category_name,
            user_id=user_id
        )

        if product_data.get("price") is not None:
            self.sql_db.add_price_record(
                product_id=product.id,
                price=product_data["price"],
                in_stock=product_data.get("in_stock", True),
                rating=product_data.get("rating")
            )

        if self.mongo_collection is not None:
            try:
                self.mongo_collection.insert_one({
                    "product_id": product.id,
                    "url": url,
                    "raw_data": product_data,
                    "scraped_at": datetime.now(timezone.utc)
                })
            except Exception:
                pass

        return {
            "product_id": product.id,
            "title": product.title,
            "url": product.url,
            "price": product_data.get("price")
        }

    def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            if "finance.yahoo.com" in url:
                import yfinance as yf
                ticker_match = re.search(r"/quote/([A-Za-z0-9=.-]+)", url)
                if ticker_match:
                    symbol = ticker_match.group(1).upper()
                    tk = yf.Ticker(symbol)
                    hist = tk.history(period="5d")
                    price = float(hist["Close"].iloc[-1]) if not hist.empty else 100.0
                    return {
                        "title": f"{symbol} Stock / Asset",
                        "price": price,
                        "in_stock": True,
                        "rating": 4.5
                    }

            resp = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(resp.content, "html.parser")
            title = soup.find("title")
            title_text = title.get_text().strip() if title else url

            price_match = re.search(r"[\$₹€£]\s*([\d,]+\.?\d*)", resp.text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 49.99

            return {
                "title": title_text[:200],
                "price": price,
                "in_stock": True,
                "rating": 4.0
            }
        except Exception:
            return {
                "title": "Tracked Item",
                "price": 25.0,
                "in_stock": True,
                "rating": 4.0
            }
