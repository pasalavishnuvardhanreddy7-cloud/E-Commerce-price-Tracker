"""
Master Automated PDF Generator for PricePulse Project
Compiles all 16 phases, architecture diagrams, troubleshooting logs, and code.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, PageBreak, KeepTogether
)

def build_full_pdf(filename="PricePulse_Complete_Project_Manual.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Typography & Styles
    doc_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        fontName="Helvetica-Bold",
        spaceAfter=4
    )
    doc_subtitle = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    h1 = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e40af"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4
    )
    h2 = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        spaceBefore=6,
        spaceAfter=3
    )
    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4
    )
    code_block = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f8fafc"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=5,
        spaceAfter=6
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("E-Commerce Price Tracker (PricePulse)", doc_title))
    elements.append(Paragraph("<b>End-to-End System Manual: Architecture, 16 Phases, Troubleshooting & Codebase</b>", doc_subtitle))
    elements.append(Spacer(1, 4))

    # 1. Executive Summary & Architecture Table
    elements.append(Paragraph("1. Executive Summary & Polyglot Persistence Architecture", h1))
    summary_p = (
        "PricePulse is an automated web scraping, time-series price monitoring, and analytics engine. "
        "It combines <b>relational database modeling</b> (SQLite/SQLAlchemy) for structured product entities and price checkpoints "
        "with <b>document-based NoSQL storage</b> (MongoDB/PyMongo) for raw DOM snapshots and request payloads. "
        "The system features automated background tasks via APScheduler, Matplotlib headless chart rendering, and a Flask dashboard."
    )
    elements.append(Paragraph(summary_p, body))

    arch_table_data = [
        ["Layer", "Technology", "Key Responsibilities"],
        ["Relational DB", "SQLite / SQLAlchemy ORM", "Products, categories, price history checkpoints, audit scrape logs"],
        ["Document DB", "MongoDB / PyMongo", "Raw HTML DOM snapshots, response headers, schema-less metadata"],
        ["Web Scraper", "Requests / BeautifulSoup4", "HTTP session pooling, custom headers, price/stock/rating parsing"],
        ["Analytics Engine", "Pandas / NumPy", "Moving averages, standard deviations, percentiles, buy/wait heuristics"],
        ["Visualization", "Matplotlib (Headless Agg)", "Base64 PNG rendering for historical trendlines & target thresholds"],
        ["Web & Scheduling", "Flask / Jinja2 / APScheduler", "Dashboard UI, CSV exports, JSON REST API, recurring cron worker"],
        ["Containerization", "Docker & Docker Compose", "Multi-container orchestration (Flask + MongoDB 7.0 + Volumes)"]
    ]
    t_arch = Table(arch_table_data, colWidths=[90, 130, 320])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f1f5f9"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t_arch)
    elements.append(Spacer(1, 6))

    # 2. Complete Troubleshooting Matrix
    elements.append(Paragraph("2. Troubleshooting Log & Error Resolutions", h1))
    trouble_data = [
        ["Issue / Error Message", "Root Cause", "Applied Resolution"],
        ["AttributeError: SQL_DATABASE_URI", "Config key mismatch with DATABASE_URL", "Added fallback resolution in SQLDatabase constructor"],
        ["ModuleNotFoundError: apscheduler", "Package missing in virtualenv", "Executed pip install apscheduler inside active venv"],
        ["AttributeError: SCRAPE_INTERVAL_HOURS", "Missing default in Config object", "Defined SCRAPE_INTERVAL_HOURS = 6 in config.py"],
        ["SyntaxError in services/scheduler.py", "File redirection typo during piping", "Replaced duplicate line with clean single import"],
        ["Browser Bing Search Loop", "Markdown URL syntax pasted in address bar", "Navigated directly to plain http://127.0.0.1:5000"],
        ["docker: term not recognized", "Docker Desktop missing on host", "Specified AMD64 Windows installer with WSL 2 backend"]
    ]
    t_trouble = Table(trouble_data, colWidths=[140, 160, 240])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#b91c1c")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#fff1f2"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_trouble)
    elements.append(Spacer(1, 6))

    # 3. 16 Phases Overview Table
    elements.append(Paragraph("3. 16-Phase Execution Roadmap", h1))
    phase_data = [
        ["Phase", "Description", "Primary Artifacts"],
        ["Phase 1", "Virtualenv, requirements, and environment setup", "requirements.txt, .env, config.py"],
        ["Phase 2", "Relational database schema & ORM models", "database/sql_database.py"],
        ["Phase 3", "Document NoSQL database schema & indexes", "database/mongo_database.py"],
        ["Phase 4", "Domain OOP models and value objects", "models/product.py"],
        ["Phase 5", "Web scraping core engine & DOM parser", "scraper/base_scraper.py, product_scraper.py"],
        ["Phase 6", "Pandas/NumPy statistical analysis engine", "analytics/price_analysis.py"],
        ["Phase 7", "Headless Base64 visualization generator", "visualization/charts.py"],
        ["Phase 8", "Orchestration service & workflow pipeline", "services/price_tracker.py"],
        ["Phase 9", "Comprehensive 22-test automated verification", "tests/test_*.py"],
        ["Phase 10", "Synthetic 14-day time-series history seeder", "seed_history.py"],
        ["Phase 11", "Jinja2 responsive Bootstrap 5 web templates", "templates/*.html"],
        ["Phase 12", "Flask web server controllers & routes", "app.py"],
        ["Phase 13", "Asynchronous APScheduler background worker", "services/scheduler.py"],
        ["Phase 14", "CSV export engine & REST JSON API", "app.py (/export/csv, /api/products)"],
        ["Phase 15", "Price drop alert & webhook notifications", "services/notifier.py"],
        ["Phase 16", "Docker multi-container orchestration & PDF report", "Dockerfile, docker-compose.yml"]
    ]
    t_phase = Table(phase_data, colWidths=[60, 240, 240])
    t_phase.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t_phase)

    elements.append(PageBreak())

    # 4. Verified Test Logs
    elements.append(Paragraph("4. Automated Verification Suite Logs (22 Passed)", h1))
    test_log = (
        "============================= test session starts ==============================\n"
        "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0\n"
        "rootdir: C:\\Users\\pasal\\E-Commerce-price-Tracker\n"
        "collected 22 items\n\n"
        "tests/test_database.py::test_add_product_and_history PASSED             [  4%]\n"
        "tests/test_mongo.py::test_insert_and_retrieve_raw_scrape PASSED         [  9%]\n"
        "tests/test_models.py::test_product_creation_and_latest_price PASSED     [ 18%]\n"
        "tests/test_scraper.py::test_product_scraper_parse PASSED                 [ 36%]\n"
        "tests/test_analytics.py::test_summary_statistics PASSED                 [ 54%]\n"
        "tests/test_analytics.py::test_recommendations PASSED                    [ 63%]\n"
        "tests/test_visualization.py::test_price_history_chart_success PASSED   [ 72%]\n"
        "tests/test_services.py::test_add_product_to_track PASSED                [ 81%]\n"
        "tests/test_services.py::test_get_product_details_with_analytics PASSED [ 86%]\n"
        "tests/test_app.py::test_dashboard_route PASSED                          [ 95%]\n"
        "tests/test_app.py::test_add_page_route PASSED                           [100%]\n\n"
        "============================== 22 passed in 10.47s =============================="
    )
    elements.append(Preformatted(test_log, code_block))

    # 5. Complete Source Code Highlights
    elements.append(Paragraph("5. Complete Core Codebase", h1))

    elements.append(Paragraph("config.py", h2))
    elements.append(Preformatted(
        "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n\n"
        "class Config:\n"
        "    SECRET_KEY = os.getenv('SECRET_KEY', 'default-key-123')\n"
        "    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/ecommerce.db')\n"
        "    SQL_DATABASE_URI = DATABASE_URL\n"
        "    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')\n"
        "    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'ecommerce_raw_data')\n"
        "    SCRAPE_INTERVAL_HOURS = int(os.getenv('SCRAPE_INTERVAL_HOURS', 6))\n"
        "    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))\n"
        "    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 Chrome/122.0')\n",
        code_block
    ))

    elements.append(Paragraph("services/price_tracker.py (Orchestrator)", h2))
    elements.append(Preformatted(
        "class PriceTrackerService:\n"
        "    def __init__(self, sql_db=None, mongo_db=None, scraper=None, notifier=None):\n"
        "        self.sql_db = sql_db or SQLDatabase()\n"
        "        self.mongo_db = mongo_db or MongoDatabase()\n"
        "        self.scraper = scraper or ProductScraper()\n"
        "        self.notifier = notifier or NotificationService()\n\n"
        "    def add_product_to_track(self, url, target_price=None, category=None):\n"
        "        scraped = self.scraper.scrape_product(url)\n"
        "        if not scraped: return None\n"
        "        prod = self.sql_db.add_product(scraped['title'], url, target_price, category)\n"
        "        rec = self.sql_db.add_price_record(prod.id, scraped['price'], scraped['in_stock'], scraped['rating'])\n"
        "        self.mongo_db.insert_raw_scrape(prod.id, url, 200, scraped['raw_data'], scraped['html_snapshot'])\n"
        "        if target_price and scraped['price'] <= target_price:\n"
        "            self.notifier.send_price_drop_alert(prod.title, scraped['price'], target_price, url)\n"
        "        return prod\n",
        code_block
    ))

    elements.append(Paragraph("app.py (Flask Web App & API Engine)", h2))
    elements.append(Preformatted(
        "from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response\n"
        "app = Flask(__name__)\n\n"
        "@app.route('/')\n"
        "def index():\n"
        "    products = sql_db.get_all_products(active_only=False)\n"
        "    return render_template('index.html', products=products)\n\n"
        "@app.route('/product/<int:product_id>/export/csv')\n"
        "def export_csv(product_id):\n"
        "    history = sql_db.get_price_history(product_id, limit=500)\n"
        "    output = io.StringIO()\n"
        "    writer = csv.writer(output)\n"
        "    writer.writerow(['Record ID', 'Product ID', 'Price', 'Stock', 'Timestamp'])\n"
        "    for r in history: writer.writerow([r.id, product_id, r.price, r.in_stock, r.scraped_at])\n"
        "    return Response(output.getvalue(), mimetype='text/csv',\n"
        "                    headers={'Content-Disposition': f'attachment;filename=history_{product_id}.csv'})\n\n"
        "@app.route('/api/products/<int:product_id>')\n"
        "def api_product(product_id):\n"
        "    details = service.get_product_details_with_analytics(product_id)\n"
        "    if not details: return jsonify({'error': 'Not found'}), 404\n"
        "    details.pop('charts', None)\n"
        "    return jsonify(details)\n",
        code_block
    ))

    elements.append(Paragraph("docker-compose.yml", h2))
    elements.append(Preformatted(
        "services:\n"
        "  mongodb:\n"
        "    image: mongo:7.0\n"
        "    ports: ['27017:27017']\n"
        "    volumes: [mongo_data:/data/db]\n"
        "  web:\n"
        "    build: .\n"
        "    ports: ['5000:5000']\n"
        "    environment:\n"
        "      - DATABASE_URL=sqlite:///data/ecommerce.db\n"
        "      - MONGO_URI=mongodb://mongodb:27017/\n"
        "      - SCRAPE_INTERVAL_HOURS=6\n"
        "    volumes: [sqlite_data:/app/data]\n"
        "volumes:\n"
        "  mongo_data:\n"
        "  sqlite_data:\n",
        code_block
    ))

    doc.build(elements)
    print(f"[SUCCESS] Complete manual generated: {filename}")

if __name__ == "__main__":
    build_full_pdf()
