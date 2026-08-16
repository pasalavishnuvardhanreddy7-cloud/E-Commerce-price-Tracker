"""
Orchestration Service Layer
Coordinates data ingestion, database synchronization, alerts, and analytics.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from database.sql_database import SQLDatabase, ProductModel
from database.mongo_database import MongoDatabase
from scraper.product_scraper import ProductScraper
from models.product import Product, PriceRecord
from analytics.price_analysis import PriceAnalyzer
from visualization.charts import ChartGenerator
from services.notifier import NotificationService

logger = logging.getLogger(__name__)


class PriceTrackerService:
    """End-to-end service coordinating scraping, persistence, and analytics."""

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

    def add_product_to_track(
        self,
        url: str,
        target_price: Optional[float] = None,
        category: Optional[str] = None,
    ) -> Optional[Product]:
        scraped_data = self.scraper.scrape_product(url)
        if not scraped_data:
            logger.error(f"Failed to scrape product metadata for initial ingestion: {url}")
            return None

        # 1. Save product to SQL
        db_product = self.sql_db.add_product(
            title=scraped_data["title"],
            url=url,
            target_price=target_price,
            category_name=category or scraped_data.get("category", "General"),
        )

        # 2. Add first price checkpoint
        db_record = self.sql_db.add_price_record(
            product_id=db_product.id,
            price=scraped_data["price"],
            in_stock=scraped_data["in_stock"],
            rating=scraped_data.get("rating"),
        )

        # 3. Store raw unstructured payload in MongoDB
        self.mongo_db.insert_raw_scrape(
            product_id=db_product.id,
            url=url,
            http_status=200,
            raw_data=scraped_data.get("raw_data", {}),
            html_snapshot=scraped_data.get("html_snapshot"),
        )

        # 4. Check for immediate price drop alert
        if target_price and scraped_data["price"] <= target_price:
            self.notifier.send_price_drop_alert(
                product_title=db_product.title,
                current_price=scraped_data["price"],
                target_price=target_price,
                product_url=url,
            )

        # 5. Map to domain entity
        product = Product(
            id=db_product.id,
            title=db_product.title,
            url=db_product.url,
            category=category or scraped_data.get("category"),
            target_price=target_price,
        )
        product.add_price_record(
            PriceRecord(
                id=db_record.id,
                product_id=db_product.id,
                price=db_record.price,
                in_stock=db_record.in_stock,
                rating=db_record.rating,
                scraped_at=db_record.scraped_at,
            )
        )
        return product

    def track_all_products(self) -> Dict[str, Any]:
        start_time = time.time()
        products = self.sql_db.get_all_products(active_only=True)
        success_count = 0
        alerts = []

        for prod in products:
            scraped = self.scraper.scrape_product(prod.url)
            if scraped:
                self.sql_db.add_price_record(
                    product_id=prod.id,
                    price=scraped["price"],
                    in_stock=scraped["in_stock"],
                    rating=scraped.get("rating"),
                )
                self.mongo_db.insert_raw_scrape(
                    product_id=prod.id,
                    url=prod.url,
                    http_status=200,
                    raw_data=scraped.get("raw_data", {}),
                    html_snapshot=scraped.get("html_snapshot"),
                )
                success_count += 1

                if prod.target_price and scraped["price"] <= prod.target_price:
                    self.notifier.send_price_drop_alert(
                        product_title=prod.title,
                        current_price=scraped["price"],
                        target_price=prod.target_price,
                        product_url=prod.url,
                    )
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

    def get_product_details_with_analytics(self, product_id: int) -> Optional[Dict[str, Any]]:
        db_prod = self.sql_db.get_product_by_id(product_id)
        if not db_prod:
            return None

        title = db_prod.title
        url = db_prod.url
        target_price = db_prod.target_price
        is_active = db_prod.is_active
        category_name = db_prod.category.name if db_prod.category else "Uncategorized"

        history_records = self.sql_db.get_price_history(product_id)
        dict_records = [
            {
                "id": r.id,
                "price": r.price,
                "in_stock": r.in_stock,
                "rating": r.rating,
                "scraped_at": r.scraped_at.isoformat() if r.scraped_at else "",
            }
            for r in reversed(history_records)
        ]

        analyzer = PriceAnalyzer(dict_records)
        stats = analyzer.compute_summary_statistics()
        percentiles = analyzer.compute_percentiles()
        recommendation = analyzer.generate_recommendation(target_price=target_price)

        history_chart = ChartGenerator.generate_price_history_chart(
            records=dict_records,
            product_title=title,
            target_price=target_price,
        )

        return {
            "product": {
                "id": product_id,
                "title": title,
                "url": url,
                "target_price": target_price,
                "category": category_name,
                "is_active": is_active,
            },
            "history": dict_records,
            "statistics": stats,
            "percentiles": percentiles,
            "recommendation": recommendation,
            "charts": {
                "history_chart": history_chart,
            },
        }
