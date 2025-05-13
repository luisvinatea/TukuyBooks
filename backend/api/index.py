"""
Vercel Serverless Function for TukuyBooks API
This serves as the entry point for the TukuyBooks API on Vercel
"""

import sys
import os
import json
import time
import traceback
from pathlib import Path

# Configure proper logging for Vercel
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Log startup information
logger.info(f"Starting TukuyBooks API at {time.strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

# Add all possible paths for imports
current_dir = Path(__file__).parent  # /api
project_root = current_dir.parent  # /project_root
backend_dir = project_root / "backend"  # /backend
backend_api_dir = backend_dir / "api"  # /backend/api

# Add all paths to sys.path
for path in [
    str(current_dir),
    str(project_root),
    str(backend_dir),
    str(backend_api_dir),
]:
    if path not in sys.path:
        sys.path.insert(0, path)
        logger.info(f"Added {path} to Python path")

# Set environment variable to indicate Vercel deployment
os.environ["VERCEL_DEPLOYMENT"] = "true"

# Try different import paths for the Flask app
app = None
errors = []

try:
    # Try importing from backend.api module
    from backend.api.app import app

    logger.info("Successfully imported Flask app from backend.api.app")
except Exception as e:
    errors.append(f"Failed to import app from backend.api.app: {str(e)}")
    try:
        # Try importing directly from the file
        sys.path.insert(0, str(backend_api_dir))
        from app import app

        logger.info("Successfully imported Flask app from app module")
    except Exception as e:
        errors.append(f"Failed to import app from app module: {str(e)}")

# If we still don't have the app, log all errors
if app is None:
    for error in errors:
        logger.error(error)
    logger.error(traceback.format_exc())
    # Create a dummy app that returns 500 errors
    from flask import Flask

    app = Flask(__name__)

    @app.route("/<path:path>")
    def error_handler(path):
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "Application initialization failed",
                    "details": errors,
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }
else:
    logger.info("Flask app successfully imported and ready to handle requests")


# Define the handler function for Vercel Serverless Functions
def handler(request):
    """
    Vercel handler function for processing API requests
    """
    try:
        # Basic request logging
        request_method = request.get("method", "UNKNOWN")
        request_path = request.get("path", "UNKNOWN")
        request_query = request.get("query", {})
        logger.info(
            f"Handling {request_method} request to {request_path} with query: {request_query}"
        )

        # Debug: Print Python path
        logger.info(f"Python path: {sys.path}")

        # Handle preflight OPTIONS requests for CORS
        if request.get("method") == "OPTIONS":
            logger.info("Handling OPTIONS request")
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                },
            }

        # Check if we successfully imported the app
        if app is None:
            logger.error("Flask app is not available - import failed")
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "error": "Server configuration error: Flask app not available",
                        "message": "The API server failed to initialize properly.",
                    }
                ),
                "headers": {"Content-Type": "application/json"},
            }

        # Process the request through the Flask app
        logger.info("Forwarding request to Flask app")

        environ = request.get("environ", {})
        start_response = request.get("start_response")

        # Debug the request structure
        logger.info(
            f"Request environ keys: {list(environ.keys()) if environ else 'None'}"
        )
        logger.info(f"Start response available: {start_response is not None}")

        # Handle WSGI standard interface
        return app(environ, start_response)

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        logger.error(traceback.format_exc())

        # Return a detailed error response
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "message": "The server encountered an unexpected error.",
                    "trace": traceback.format_exc(),
                    "timestamp": time.time(),
                    "request_info": {
                        "method": request.get("method", "UNKNOWN"),
                        "path": request.get("path", "UNKNOWN"),
                        "query": request.get("query", {}),
                    },
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }
