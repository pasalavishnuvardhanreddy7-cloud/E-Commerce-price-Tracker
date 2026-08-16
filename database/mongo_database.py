"""
MongoDB Document Database Layer
Persists unstructured raw HTTP responses, DOM snapshots, and headers.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from config import Config


class MongoDatabase:
    """Handles raw JSON / HTML ingestion into MongoDB collections."""

    def __init__(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None) -> None:
        self.uri = mongo_uri or Config.MONGO_URI
        self.db_name = db_name or Config.MONGO_DB_NAME
        self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
        self.db = self.client[self.db_name]
        self.raw_scrapes = self.db["raw_scrapes"]
        self.ensure_indexes()

    def ping(self) -> bool:
        """Health-check method verifying connection to MongoDB server."""
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Closes active MongoDB client connections."""
        try:
            self.client.close()
        except Exception:
            pass

    def ensure_indexes(self) -> None:
        try:
            self.raw_scrapes.create_index("product_id")
            self.raw_scrapes.create_index("scraped_at")
        except Exception:
            pass

    def insert_raw_scrape(
        self,
        product_id: int,
        url: str,
        http_status: int,
        raw_data: Dict[str, Any],
        html_snapshot: Optional[str] = None,
    ) -> str:
        document = {
            "product_id": product_id,
            "url": url,
            "http_status": http_status,
            "raw_data": raw_data,
            "html_snapshot": html_snapshot,
            "scraped_at": datetime.now(timezone.utc),
        }
        res = self.raw_scrapes.insert_one(document)
        return str(res.inserted_id)

    def get_latest_raw_scrape(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent raw document for a given product ID."""
        return self.raw_scrapes.find_one({"product_id": product_id}, sort=[("scraped_at", -1)])

    def get_scrape_history(self, product_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = (
            self.raw_scrapes.find({"product_id": product_id})
            .sort("scraped_at", -1)
            .limit(limit)
        )
        return list(cursor)
