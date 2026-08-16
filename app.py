"""
Flask Web Application Entrypoint
Exposes REST, Export, and UI routes for price tracking and analytics.
"""

import io
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from config import Config
from database.sql_database import SQLDatabase, ProductModel, PriceHistoryModel
from database.mongo_database import MongoDatabase
from scraper.product_scraper import ProductScraper
from services.price_tracker import PriceTrackerService
from services.scheduler import PriceTrackerScheduler

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database, scraper & services
sql_db = SQLDatabase()
sql_db.init_db()
mongo_db = MongoDatabase()
scraper = ProductScraper()
service = PriceTrackerService(sql_db=sql_db, mongo_db=mongo_db, scraper=scraper)

# Start background scheduler
scheduler = PriceTrackerScheduler(service=service)
scheduler.start()


@app.route("/")
def index():
    """Dashboard displaying all active tracked products."""
    products = sql_db.get_all_products(active_only=False)
    product_list = []
    for p in products:
        history = sql_db.get_price_history(p.id, limit=1)
        current_price = history[0].price if history else 0.0
        product_list.append({
            "id": p.id,
            "title": p.title,
            "url": p.url,
            "target_price": p.target_price,
            "category": p.category.name if p.category else "General",
            "current_price": current_price,
            "is_active": p.is_active,
            "is_target_met": (p.target_price is not None and current_price <= p.target_price),
        })
    return render_template("index.html", products=product_list)


@app.route("/add", methods=["GET", "POST"])
def add_product():
    """Form to submit a new product URL for scraping and tracking."""
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        target_price_raw = request.form.get("target_price", "").strip()
        category = request.form.get("category", "").strip() or None

        target_price = float(target_price_raw) if target_price_raw else None

        if not url:
            flash("Please provide a valid product URL.", "danger")
            return redirect(url_for("add_product"))

        product = service.add_product_to_track(url=url, target_price=target_price, category=category)
        if product:
            flash(f"Successfully tracked '{product.title}'!", "success")
            return redirect(url_for("product_detail", product_id=product.id))
        else:
            flash("Failed to extract product details from the URL. Please verify the link.", "danger")

    return render_template("add_product.html")


@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
    """Detailed analytical view with time-series charts for a single item."""
    details = service.get_product_details_with_analytics(product_id)
    if not details:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))
    return render_template("product_detail.html", **details)


@app.route("/scrape-now", methods=["POST"])
def trigger_scrape():
    """Triggers an immediate batch scrape for all items."""
    result = service.track_all_products()
    flash(f"Scrape finished! Checked {result['products_checked']} items in {result['duration_seconds']}s.", "info")
    return redirect(url_for("index"))


@app.route("/product/<int:product_id>/export/csv")
def export_csv(product_id: int):
    """Exports time-series price history to a CSV file."""
    db_prod = sql_db.get_product_by_id(product_id)
    if not db_prod:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))

    history = sql_db.get_price_history(product_id, limit=500)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Record ID", "Product ID", "Product Title", "Price (USD)", "In Stock", "Rating", "Timestamp (UTC)"])

    for record in reversed(history):
        writer.writerow([
            record.id,
            product_id,
            db_prod.title,
            f"{record.price:.2f}",
            record.in_stock,
            record.rating or "",
            record.scraped_at.isoformat() if record.scraped_at else "",
        ])

    output.seek(0)
    filename = f"price_history_product_{product_id}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route("/product/<int:product_id>/toggle-status", methods=["POST"])
def toggle_product_status(product_id: int):
    """Pauses or resumes automated tracking for a product."""
    with sql_db.SessionLocal() as session:
        prod = session.query(ProductModel).filter_by(id=product_id).first()
        if prod:
            prod.is_active = not prod.is_active
            session.commit()
            status_str = "resumed" if prod.is_active else "paused"
            flash(f"Tracking {status_str} for '{prod.title}'.", "info")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/api/products/<int:product_id>")
def api_product(product_id: int):
    """REST API endpoint returning structured product JSON metrics."""
    details = service.get_product_details_with_analytics(product_id)
    if not details:
        return jsonify({"error": "Product not found"}), 404
    # Strip base64 image strings from JSON API response for efficiency
    details.pop("charts", None)
    return jsonify(details)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
