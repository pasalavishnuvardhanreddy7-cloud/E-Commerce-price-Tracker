"""
Gold Market Time-Series Seeder (2020 - 2026)
Seeds gold investment assets with realistic multi-year historical trajectories.
"""

from datetime import datetime, timezone
import random
from database.sql_database import SQLDatabase, ProductModel, PriceHistoryModel
from database.mongo_database import MongoDatabase

sql_db = SQLDatabase()
sql_db.init_db()
mongo_db = MongoDatabase()

# Representative annual average benchmark prices (USD per Troy Oz)
BENCHMARK_GOLD_SPOT = {
    2020: 1770.0,
    2021: 1798.0,
    2022: 1800.0,
    2023: 1940.0,
    2024: 2380.0,
    2025: 2650.0,
    2026: 2850.0,
}

GOLD_CATALOG = [
    {
        "title": "Gold Spot Price (1 Troy Oz .999 Fine)",
        "url": "https://markets.pricepulse.local/assets/gold-spot-1oz",
        "category": "Precious Metals",
        "target_price": 2700.0,
        "multiplier": 1.0,
        "rating": 5.0,
    },
    {
        "title": "SPDR Gold Trust ETF (GLD)",
        "url": "https://markets.pricepulse.local/assets/etf-gld",
        "category": "Gold ETFs",
        "target_price": 250.0,
        "multiplier": 0.092,
        "rating": 4.8,
    },
    {
        "title": "American Eagle 1 oz Gold Bullion Coin",
        "url": "https://markets.pricepulse.local/assets/american-eagle-gold-1oz",
        "category": "Physical Bullion",
        "target_price": 2800.0,
        "multiplier": 1.05,  # Premium over spot
        "rating": 4.9,
    },
    {
        "title": "iShares Gold Trust (IAU)",
        "url": "https://markets.pricepulse.local/assets/etf-iau",
        "category": "Gold ETFs",
        "target_price": 50.0,
        "multiplier": 0.019,
        "rating": 4.7,
    },
    {
        "title": "PAMP Suisse Lady Fortuna 10g Gold Bar",
        "url": "https://markets.pricepulse.local/assets/pamp-suisse-10g-gold",
        "category": "Physical Bullion",
        "target_price": 850.0,
        "multiplier": 0.335,
        "rating": 5.0,
    },
]

def seed_gold_market_data():
    print("Populating Gold Products & 2020-2026 Time-Series Analytics...\n")

    for item in GOLD_CATALOG:
        # 1. Insert or Retrieve Relational Product
        db_product = sql_db.add_product(
            title=item["title"],
            url=item["url"],
            target_price=item["target_price"],
            category_name=item["category"],
        )

        with sql_db.SessionLocal() as session:
            session.query(PriceHistoryModel).filter_by(product_id=db_product.id).delete()
            session.commit()

            # 2. Generate Bi-Monthly Price Checkpoints from 2020 to 2026
            for year in range(2020, 2027):
                base_spot = BENCHMARK_GOLD_SPOT[year]
                for month in [2, 4, 6, 8, 10, 12]:
                    # Stop if date is in the future
                    if year == 2026 and month > 8:
                        continue

                    # Asset pricing calculation with market noise
                    volatility = random.uniform(-0.04, 0.04)
                    asset_price = round(base_spot * item["multiplier"] * (1 + volatility), 2)
                    timestamp = datetime(year, month, random.randint(10, 25), 14, 0, tzinfo=timezone.utc)

                    record = PriceHistoryModel(
                        product_id=db_product.id,
                        price=asset_price,
                        in_stock=True,
                        rating=item["rating"],
                        scraped_at=timestamp,
                    )
                    session.add(record)

            session.commit()

        # 3. Document Persistence in MongoDB
        mongo_db.insert_raw_scrape(
            product_id=db_product.id,
            url=item["url"],
            http_status=200,
            raw_data={
                "asset_type": "Gold Asset",
                "timeframe": "2020-2026",
                "base_multiplier": item["multiplier"],
            },
            html_snapshot=f"<div><h1>{item['title']}</h1><p>Historical Gold Asset Data (2020-2026)</p></div>",
        )

        print(f"✓ Seeded Asset ID {db_product.id:02d} | [{item['category']:<16}] {item['title']}")

    print("\n[SUCCESS] Multi-year Gold analytics time-series populated successfully!")

if __name__ == "__main__":
    seed_gold_market_data()
