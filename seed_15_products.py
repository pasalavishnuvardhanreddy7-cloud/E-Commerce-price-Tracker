"""
Batch Seeder: Adds 15 Tracked Products with 14-day Historical Price Series
"""

import random
from datetime import datetime, timedelta, timezone
from database.sql_database import SQLDatabase, ProductModel, PriceHistoryModel
from database.mongo_database import MongoDatabase

sql_db = SQLDatabase()
sql_db.init_db()
mongo_db = MongoDatabase()

# Catalog of 15 realistic products across diverse categories
PRODUCTS_CATALOG = [
    {
        "title": "A Light in the Attic",
        "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "category": "Poetry",
        "target_price": 50.00,
        "base_price": 51.77,
        "rating": 3.0,
    },
    {
        "title": "Tipping the Velvet",
        "url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
        "category": "Historical Fiction",
        "target_price": 52.00,
        "base_price": 53.74,
        "rating": 1.0,
    },
    {
        "title": "Soumission",
        "url": "https://books.toscrape.com/catalogue/soumission_998/index.html",
        "category": "Fiction",
        "target_price": 48.00,
        "base_price": 50.10,
        "rating": 1.0,
    },
    {
        "title": "Sharp Objects",
        "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
        "category": "Mystery",
        "target_price": 45.00,
        "base_price": 47.82,
        "rating": 4.0,
    },
    {
        "title": "Sapiens: A Brief History of Humankind",
        "url": "https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html",
        "category": "History",
        "target_price": 50.00,
        "base_price": 54.23,
        "rating": 5.0,
    },
    {
        "title": "The Requiem Red",
        "url": "https://books.toscrape.com/catalogue/the-requiem-red_995/index.html",
        "category": "Young Adult",
        "target_price": 20.00,
        "base_price": 22.65,
        "rating": 1.0,
    },
    {
        "title": "The Dirty Little Secrets of Getting Your Dream Job",
        "url": "https://books.toscrape.com/catalogue/the-dirty-little-secrets-of-getting-your-dream-job_994/index.html",
        "category": "Business",
        "target_price": 30.00,
        "base_price": 33.34,
        "rating": 4.0,
    },
    {
        "title": "The Coming Woman: A Novel Based on the Life of Victoria Woodhull",
        "url": "https://books.toscrape.com/catalogue/the-coming-woman-a-novel-based-on-the-life-of-victoria-woodhull_993/index.html",
        "category": "Historical Fiction",
        "target_price": 16.00,
        "base_price": 17.93,
        "rating": 3.0,
    },
    {
        "title": "The Boys in the Boat",
        "url": "https://books.toscrape.com/catalogue/the-boys-in-the-boat-nine-americans-and-their-epic-quest-for-gold-at-the-1936-berlin-olympics_992/index.html",
        "category": "Nonfiction",
        "target_price": 21.00,
        "base_price": 22.60,
        "rating": 4.0,
    },
    {
        "title": "The Black Maria",
        "url": "https://books.toscrape.com/catalogue/the-black-maria_991/index.html",
        "category": "Poetry",
        "target_price": 49.00,
        "base_price": 52.15,
        "rating": 1.0,
    },
    {
        "title": "Starving Hearts (Triangular Trade Trilogy #1)",
        "url": "https://books.toscrape.com/catalogue/starving-hearts-triangular-trade-trilogy-1_990/index.html",
        "category": "Default",
        "target_price": 12.50,
        "base_price": 13.99,
        "rating": 2.0,
    },
    {
        "title": "Shakespeare's Sonnets",
        "url": "https://books.toscrape.com/catalogue/shakespeares-sonnets_989/index.html",
        "category": "Poetry",
        "target_price": 18.00,
        "base_price": 20.66,
        "rating": 4.0,
    },
    {
        "title": "Set Me Free",
        "url": "https://books.toscrape.com/catalogue/set-me-free_988/index.html",
        "category": "Young Adult",
        "target_price": 15.00,
        "base_price": 17.46,
        "rating": 5.0,
    },
    {
        "title": "Scott Pilgrim's Precious Little Life (Scott Pilgrim #1)",
        "url": "https://books.toscrape.com/catalogue/scott-pilgrims-precious-little-life-scott-pilgrim-1_987/index.html",
        "category": "Comics",
        "target_price": 50.00,
        "base_price": 52.29,
        "rating": 5.0,
    },
    {
        "title": "Rip it Up and Start Again",
        "url": "https://books.toscrape.com/catalogue/rip-it-up-and-start-again_986/index.html",
        "category": "Music",
        "target_price": 32.00,
        "base_price": 35.02,
        "rating": 5.0,
    },
]

def seed_products():
    now = datetime.now(timezone.utc)
    print(f"Starting batch population for {len(PRODUCTS_CATALOG)} products...\n")

    for item in PRODUCTS_CATALOG:
        # 1. Relational Product Entry
        db_product = sql_db.add_product(
            title=item["title"],
            url=item["url"],
            target_price=item["target_price"],
            category_name=item["category"],
        )

        with sql_db.SessionLocal() as session:
            # Clear old history for idempotency
            session.query(PriceHistoryModel).filter_by(product_id=db_product.id).delete()
            session.commit()

            # 2. Seed 14 Days of Realistic Daily Observations
            base_p = item["base_price"]
            for days_ago in range(14, -1, -1):
                variance = round(random.uniform(-0.08, 0.06) * base_p, 2)
                observed_price = round(max(5.0, base_p + variance), 2)
                timestamp = now - timedelta(days=days_ago, hours=random.randint(1, 12))

                record = PriceHistoryModel(
                    product_id=db_product.id,
                    price=observed_price,
                    in_stock=True,
                    rating=item["rating"],
                    scraped_at=timestamp,
                )
                session.add(record)

            session.commit()

        # 3. Document Ingestion in MongoDB
        mongo_db.insert_raw_scrape(
            product_id=db_product.id,
            url=item["url"],
            http_status=200,
            raw_data={"title": item["title"], "base_price": item["base_price"], "rating": item["rating"]},
            html_snapshot=f"<html><head><title>{item['title']}</title></head><body><h1>{item['title']}</h1></body></html>",
        )

        print(f"✓ Tracked ID {db_product.id:02d} | [{item['category']:<18}] {item['title'][:35]}")

    print("\n[SUCCESS] All 15 products and 225 price records populated successfully!")

if __name__ == "__main__":
    seed_products()
