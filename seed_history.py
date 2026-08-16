"""
Seed realistic price history data for testing trends, charts, and recommendations.
"""
from datetime import datetime, timedelta, timezone
import random
from database.sql_database import SQLDatabase, ProductModel, PriceHistoryModel

db = SQLDatabase()
db.init_db()

with db.SessionLocal() as session:
    # Find the first product
    product = session.query(ProductModel).first()
    if not product:
        print("No product found. Please track a product first from the web interface.")
        exit()

    print(f"Adding 14 days of price history for: {product.title}")

    # Clean old history
    session.query(PriceHistoryModel).filter_by(product_id=product.id).delete()

    base_price = 55.0
    now = datetime.now(timezone.utc)

    # Generate 14 days of realistic price fluctuations
    for days_ago in range(14, -1, -1):
        fluctuation = round(random.uniform(-4.5, 3.5), 2)
        price = round(base_price + fluctuation, 2)
        timestamp = now - timedelta(days=days_ago, hours=random.randint(1, 6))

        record = PriceHistoryModel(
            product_id=product.id,
            price=price,
            in_stock=True,
            rating=3.0,
            scraped_at=timestamp,
        )
        session.add(record)

    session.commit()
    print("Successfully added 15 price points across the last 14 days!")
