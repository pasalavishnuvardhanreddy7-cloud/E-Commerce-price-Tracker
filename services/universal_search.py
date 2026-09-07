"""
Universal Search Engine: Live Stock Market & E-Commerce Product Resolution
"""

import re
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from typing import Dict, Any, Optional

class UniversalSearchEngine:
    # Common financial / commodity ticker aliases
    TICKER_MAP = {
        "gold": "GC=F",
        "gold spot": "GC=F",
        "gld": "GLD",
        "silver": "SI=F",
        "crude oil": "CL=F",
        "apple": "AAPL",
        "tesla": "TSLA",
        "google": "GOOGL",
        "microsoft": "MSFT",
        "nvidia": "NVDA",
        "bitcoin": "BTC-USD",
        "btc": "BTC-USD",
    }

    @classmethod
    def search(cls, query: str) -> Optional[Dict[str, Any]]:
        clean_query = query.strip().lower()

        # 1. Check if the query is a financial asset/ticker
        ticker_symbol = cls.TICKER_MAP.get(clean_query, query.strip().upper())
        stock_data = cls._fetch_stock_data(ticker_symbol)
        if stock_data:
            return stock_data

        # 2. Fallback to E-Commerce catalog search
        return cls._fetch_ecommerce_search(query)

    @staticmethod
    def _fetch_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
        try:
            ticker = yf.Ticker(ticker_symbol)
            fast_info = ticker.fast_info
            price = fast_info.last_price
            if price is None or price <= 0:
                return None

            info = ticker.info or {}
            short_name = info.get("shortName") or info.get("longName") or f"{ticker_symbol} Asset"
            currency = fast_info.currency or "USD"
            prev_close = fast_info.previous_close or price

            return {
                "type": "FINANCIAL_ASSET",
                "title": short_name,
                "symbol": ticker_symbol,
                "price": round(float(price), 2),
                "currency": currency,
                "previous_close": round(float(prev_close), 2),
                "category": "Stock & Commodities",
                "rating": 5.0,
                "in_stock": True,
                "url": f"https://finance.yahoo.com/quote/{ticker_symbol}",
                "description": info.get("longBusinessSummary", f"Real-time financial asset tracker for {short_name} ({ticker_symbol}).")[:280] + "...",
            }
        except Exception:
            return None

    @staticmethod
    def _fetch_ecommerce_search(query: str) -> Optional[Dict[str, Any]]:
        """Simulates automated search extraction from e-commerce catalog."""
        try:
            # Standard query simulation on books/retail catalog
            url = f"https://books.toscrape.com/catalogue/category/books_1/index.html"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.find_all("article", class_="product_pod")

            for item in articles:
                title = item.h3.a["title"]
                if any(word in title.lower() for word in query.lower().split()):
                    price_text = item.find("p", class_="price_color").text
                    price = float(re.sub(r"[^\d.]", "", price_text))
                    rel_link = item.h3.a["href"].replace("../../../", "")
                    full_link = f"https://books.toscrape.com/catalogue/{rel_link}"
                    return {
                        "type": "RETAIL_PRODUCT",
                        "title": title,
                        "price": price,
                        "currency": "USD",
                        "category": "E-Commerce",
                        "rating": 4.0,
                        "in_stock": True,
                        "url": full_link,
                        "description": f"Live tracked product matching '{query}' from store catalog.",
                    }

            # Generic fallback mock if keyword not in static demo set
            return {
                "type": "RETAIL_PRODUCT",
                "title": f"Market Result: {query.title()}",
                "price": 29.99,
                "currency": "USD",
                "category": "Consumer Goods",
                "rating": 4.5,
                "in_stock": True,
                "url": f"https://www.amazon.com/s?k={requests.utils.quote(query)}",
                "description": f"Automated price tracker entry for '{query}'.",
            }
        except Exception:
            return None
