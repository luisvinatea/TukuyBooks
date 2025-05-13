import sys
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the app directly
from app import app as backend_app  # noqa: E402

# Add WSGI middleware to handle proxy headers
app = ProxyFix(backend_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


# Entry point for WSGI servers
def handler(environ, start_response):
    """
    WSGI handler function for processing requests
    """
    return app(environ, start_response)
    # Simulate WSGI interface for Vercel
    return app(environ, start_response)
