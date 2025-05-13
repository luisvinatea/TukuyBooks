import sys
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix

# Add project directories to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
backend_dir = project_root / "backend"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

# Import the app from backend
from backend.api.app import app as backend_app

# Add WSGI middleware to handle proxy headers
app = ProxyFix(backend_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


# Handler for Vercel serverless function
def handler(environ, start_response):
    # Simulate WSGI interface for Vercel
    return app(environ, start_response)
