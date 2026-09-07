import sys
import os

# Add root directory to sys.path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel needs the WSGI callable named 'app'
app = app
