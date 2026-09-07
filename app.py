import io
import csv
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from authlib.integrations.flask_client import OAuth
from config import Config
from database.sql_database import SQLDatabase, ProductModel
from database.mongo_database import MongoDatabase
from scraper.product_scraper import ProductScraper
from services.price_tracker import PriceTrackerService
from services.scheduler import PriceTrackerScheduler
from services.universal_search import UniversalSearchEngine

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv("SECRET_KEY", "pricetracker-secret-key-2026")

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", "mock-id"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "mock-secret"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

sql_db = SQLDatabase()
sql_db.init_db()
mongo_db = MongoDatabase()
scraper = ProductScraper()
service = PriceTrackerService(sql_db=sql_db, mongo_db=mongo_db, scraper=scraper)

scheduler = PriceTrackerScheduler(service=service)
scheduler.start()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            flash("Please sign in to access your personal price tracker.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if "user_email" not in session:
        return render_template("landing.html")

    user = sql_db.get_or_create_user(session["user_email"])
    products = sql_db.get_user_products(user.id, active_only=False)

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
    return render_template("index.html", products=product_list, user_email=session["user_email"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if email:
            session["user_email"] = email
            sql_db.get_or_create_user(email)
            flash(f"Welcome back, {email}!", "success")
            return redirect(url_for("index"))
        flash("Please enter a valid email address.", "warning")
    return render_template("login.html")


@app.route("/login/google")
def google_login():
    if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_ID") != "mock-id":
        redirect_uri = url_for("google_callback", _external=True)
        return google.authorize_redirect(redirect_uri)

    session["user_email"] = "user.demo@gmail.com"
    sql_db.get_or_create_user(session["user_email"])
    flash("Signed in with Google Account (Dev Mode: user.demo@gmail.com)!", "success")
    return redirect(url_for("index"))


@app.route("/login/google/callback")
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get("userinfo")
        if user_info and "email" in user_info:
            session["user_email"] = user_info["email"]
            sql_db.get_or_create_user(user_info["email"])
            flash(f"Welcome, {user_info['email']}!", "success")
    except Exception as e:
        flash(f"Google login failed: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("index"))
    result = UniversalSearchEngine.search(query)
    return render_template("search_results.html", query=query, result=result)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_product():
    user = sql_db.get_or_create_user(session["user_email"])

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        target_price_raw = request.form.get("target_price", "").strip()
        category = request.form.get("category", "").strip() or None
        target_price = float(target_price_raw) if target_price_raw else None

        if not url:
            flash("Please provide a valid product URL or ticker symbol.", "danger")
            return redirect(url_for("add_product"))

        product = service.add_product_to_track(
            url=url,
            target_price=target_price,
            category=category,
            user_id=user.id,
        )
        if product:
            flash(f"Added '{product.title}' to your tracking list!", "success")
            return redirect(url_for("product_detail", product_id=product.id))
        else:
            flash("Failed to extract product details.", "danger")

    return render_template("add_product.html")


@app.route("/product/<int:product_id>")
@login_required
def product_detail(product_id: int):
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    interval = request.args.get("interval", "days").strip()

    details = service.get_product_details_with_analytics(
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
    )
    if not details:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))
    return render_template("product_detail.html", **details)


@app.route("/scrape-now", methods=["POST"])
@login_required
def trigger_scrape():
    result = service.track_all_products()
    flash(f"Finished scrape! Checked {result['products_checked']} items.", "info")
    return redirect(url_for("index"))


@app.route("/product/<int:product_id>/export/csv")
@login_required
def export_csv(product_id: int):
    db_prod = sql_db.get_product_by_id(product_id)
    if not db_prod:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))

    history = sql_db.get_price_history(product_id, limit=2000)
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
    filename = f"price_history_{product_id}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
