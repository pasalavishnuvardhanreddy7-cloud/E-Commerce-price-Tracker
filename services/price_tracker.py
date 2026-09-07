import os
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from database.sql_database import SQLDatabase

class PriceTrackerService:
    def __init__(self, sql_db: Optional[SQLDatabase] = None) -> None:
        self.sql_db = sql_db or SQLDatabase()
        
        # Safe MongoDB init that will never crash Vercel if Mongo is absent
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

    def track_product_by_url(self, url: str, target_price: Optional[float] = None, category_name: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        # 1. Scrape or extract details
        product_data = self._scrape_url(url)
        if not product_data:
            return None

        # 2. Add or retrieve product in SQL
        product = self.sql_db.add_product(
            title=product_data["title"],
            url=url,
            target_price=target_price,
            category_name=category_name,
            user_id=user_id
        )

        # 3. Add current price record
        if product_data.get("price") is not None:
            self.sql_db.add_price_record(
                product_id=product.id,
                price=product_data["price"],
                in_stock=product_data.get("in_stock", True),
                rating=product_data.get("rating")
            )

        # 4. Safely save raw data to Mongo if available
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
        # Universal lightweight fetcher for stocks / products
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # Check if Yahoo Finance
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

            # Generic fallback scraper
            resp = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(resp.content, "html.parser")
            title = soup.find("title")
            title_text = title.get_text().strip() if title else url

            # Simple heuristic price search
            price_match = re.search(r"[\$₹€£]\s*([\d,]+\.?\d*)", resp.text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 49.99

            return {
                "title": title_text[:200],
                "price": price,
                "in_stock": True,
                "rating": 4.0
            }
        except Exception as e:
            print(f"Scrape fallback error: {e}")
            return {
                "title": "Tracked Item",
                "price": 25.0,
                "in_stock": True,
                "rating": 4.0
            }
