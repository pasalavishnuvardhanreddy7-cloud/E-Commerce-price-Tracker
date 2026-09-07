import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["VERCEL"] = "1"

from app import app, db, sql_db

# Ensure SQLite schema exists in /tmp before serving requests
try:
    with app.app_context():
        if hasattr(db, "create_all"):
            db.create_all()
        if hasattr(sql_db, "init_db"):
            sql_db.init_db()
except Exception as e:
    print(f"Database pre-init warning: {e}")
