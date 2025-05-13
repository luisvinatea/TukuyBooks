import sys
import logging
import traceback
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Add current directory to path for imports
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    logger.info(f"Added {current_dir} to Python path")

    # Import the app directly
    from app import app as backend_app  # noqa: E402

    logger.info("Successfully imported Flask app in wsgi.py")

    # Add WSGI middleware to handle proxy headers
    app = ProxyFix(
        backend_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
    )
    logger.info("Applied ProxyFix middleware")

except Exception as e:
    logger.error(f"Error in wsgi.py setup: {str(e)}")
    logger.error(traceback.format_exc())
    # Re-raise to make the error visible
    raise


# Entry point for WSGI servers
def handler(environ, start_response):
    """
    WSGI handler function for processing requests
    """
    try:
        return app(environ, start_response)
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        logger.error(traceback.format_exc())

        # Return a 500 error response
        status = "500 Internal Server Error"
        response_headers = [("Content-type", "text/plain")]
        start_response(status, response_headers)
        return [b"Internal Server Error"]
