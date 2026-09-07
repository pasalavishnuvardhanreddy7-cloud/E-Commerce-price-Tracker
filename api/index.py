import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["VERCEL"] = "1"

from app import app

# WSGI wrapper to guarantee root path routing works uniformly
def handler(environ, start_response):
    path = environ.get('PATH_INFO', '')
    if path.startswith('/api/index'):
        environ['PATH_INFO'] = path.replace('/api/index', '') or '/'
    return app(environ, start_response)
