"""
Orchestration Service Layer: Multi-Tenant Support
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import yfinance as yf

from database.sql_database import SQLDatabase, ProductModel, PriceHistoryModel
from database.mongo_database import MongoDatabase
from scraper.product_scraper import ProductScraper
from models.product import Product, PriceRecord
from analytics.price_analysis import PriceAnalyzer
from visualization.charts import ChartGenerator
from services.notifier import NotificationService

logger = logging.getLogger(__name__)


class PriceTrackerService:
    def __init__(
        self,
        sql_db: Optional[SQLDatabase] = None,
        mongo_db: Optional[MongoDatabase] = None,
        scraper: Optional[ProductScraper] = None,
        notifier: Optional[NotificationService] = None,
    ) -> None:
        self.sql_db = sql_db or SQLDatabase()
        self.sql_db.init_db()
        self.mongo_db = mongo_db or MongoDatabase()
        self.scraper = scraper or ProductScraper()
        self.notifier = notifier or NotificationService()

    def _extract_ticker_symbol(self, url: str) -> Optional[str]:
        if "finance.yahoo.com/quote/" in url:
            return url.split("quote/")[-1].strip("/").split("?")[0].upper()
        return None

    def _fetch_financial_price(self, url: str) -> Optional[Dict[str, Any]]:
        symbol = self._extract_ticker_symbol(url)
        if not symbol:
            return None

        try:
            ticker = yf.Ticker(symbol)
            fast_info = ticker.fast_info
            price = fast_info.last_price
            if price and price > 0:
                info = ticker.info or {}
                title = info.get("shortName") or info.get("longName") or f"{symbol} Asset"
                return {
                    "symbol": symbol,
                    "title": title,
                    "price": round(float(price), 2),
                    "in_stock": True,
                    "rating": 5.0,
                    "category": "Cryptocurrency" if "-USD" in symbol else "Stock & Commodities",
                    "raw_data": {"symbol": symbol, "market_price": price},
                    "html_snapshot": f"<div>Ticker: {symbol} - Price: {price}</div>",
                }
        except Exception as e:
            logger.error(f"Financial fetch error for {symbol}: {e}")
        return None

    def _backfill_ticker_history(self, product_id: int, symbol: str, period: str = "2y") -> None:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")
            if hist.empty:
                return

            with self.sql_db.SessionLocal() as session:
                session.query(PriceHistoryModel).filter_by(product_id=product_id).delete()
                step = 1 if len(hist) < 90 else (3 if len(hist) < 365 else 7)
                sampled_hist = hist.iloc[::step]

                for index_dt, row in sampled_hist.iterrows():
                    close_price = round(float(row["Close"]), 2)
                    ts = index_dt.to_pydatetime()
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)

                    session.add(
                        PriceHistoryModel(
                            product_id=product_id,
                            price=close_price,
                            in_stock=True,
                            rating=5.0,
                            scraped_at=ts,
                        )
                    )
                session.commit()
        except Exception as e:
            logger.error(f"Failed to backfill history for {symbol}: {e}")

    def add_product_to_track(
        self,
        url: str,
        target_price: Optional[float] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Optional[Product]:
        financial_data = self._fetch_financial_price(url)
        scraped_data = financial_data or self.scraper.scrape_product(url)

        if not scraped_data:
            return None

        db_product = self.sql_db.add_product(
            title=scraped_data["title"],
            url=url,
            target_price=target_price,
            category_name=category or scraped_data.get("category", "General"),
            user_id=user_id,
        )

        db_record = self.sql_db.add_price_record(
            product_id=db_product.id,
            price=scraped_data["price"],
            in_stock=scraped_data["in_stock"],
            rating=scraped_data.get("rating"),
        )

        self.mongo_db.insert_raw_scrape(
            product_id=db_product.id,
            url=url,
            http_status=200,
            raw_data=scraped_data.get("raw_data", {}),
            html_snapshot=scraped_data.get("html_snapshot"),
        )

        if financial_data:
            self._backfill_ticker_history(db_product.id, financial_data["symbol"], period="2y")

        product = Product(
            id=db_product.id,
            title=db_product.title,
            url=db_product.url,
            category=category or scraped_data.get("category"),
            target_price=target_price,
        )
        return product

    def track_all_products(self) -> Dict[str, Any]:
        start_time = time.time()
        products = self.sql_db.get_all_products(active_only=True)
        success_count = 0
        alerts = []

        for prod in products:
            scraped = self._fetch_financial_price(prod.url) or self.scraper.scrape_product(prod.url)
            if scraped:
                self.sql_db.add_price_record(
                    product_id=prod.id,
                    price=scraped["price"],
                    in_stock=scraped["in_stock"],
                    rating=scraped.get("rating"),
                )
                success_count += 1
                if prod.target_price and scraped["price"] <= prod.target_price:
                    alerts.append({
                        "product_id": prod.id,
                        "title": prod.title,
                        "current_price": scraped["price"],
                        "target_price": prod.target_price,
                    })

        duration = round(time.time() - start_time, 2)
        status = "SUCCESS" if success_count == len(products) else "PARTIAL"

        self.sql_db.log_scrape_run(
            status=status,
            products_checked=success_count,
            duration_seconds=duration,
        )

        return {
            "status": status,
            "products_checked": success_count,
            "duration_seconds": duration,
            "alerts": alerts,
        }

    def get_product_details_with_analytics(
        self,
        product_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "days",
    ) -> Optional[Dict[str, Any]]:
        db_prod = self.sql_db.get_product_by_id(product_id)
        if not db_prod:
            return None

        history_records = self.sql_db.get_price_history(product_id, limit=3000)

        dict_records = []
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc) if start_date else None
        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) if end_date else None

        for r in reversed(history_records):
            rec_dt = r.scraped_at if r.scraped_at.tzinfo else r.scraped_at.replace(tzinfo=timezone.utc)
            if start_dt and rec_dt < start_dt:
                continue
            if end_dt and rec_dt > end_dt:
                continue

            dict_records.append({
                "id": r.id,
                "price": r.price,
                "in_stock": r.in_stock,
                "rating": r.rating,
                "scraped_at": rec_dt.isoformat(),
            })

        analyzer = PriceAnalyzer(dict_records)
        stats = analyzer.compute_summary_statistics()
        percentiles = analyzer.compute_percentiles()
        recommendation = analyzer.generate_recommendation(target_price=db_prod.target_price)

        history_chart = ChartGenerator.generate_price_history_chart(
            records=dict_records,
            product_title=db_prod.title,
            target_price=db_prod.target_price,
            interval=interval,
        )

        return {
            "product": {
                "id": product_id,
                "title": db_prod.title,
                "url": db_prod.url,
                "target_price": db_prod.target_price,
                "category": db_prod.category.name if db_prod.category else "Uncategorized",
                "is_active": db_prod.is_active,
                "user_id": db_prod.user_id,
            },
            "history": dict_records,
            "statistics": stats,
            "percentiles": percentiles,
            "recommendation": recommendation,
            "charts": {
                "history_chart": history_chart,
            },
            "filter_params": {
                "start_date": start_date or "",
                "end_date": end_date or "",
                "interval": interval,
            },
        }
