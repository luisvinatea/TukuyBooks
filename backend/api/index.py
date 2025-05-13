"""
Vercel Serverless Function for TukuyBooks API
This serves as the entry point for the TukuyBooks API on Vercel
"""

import sys
import os
import json
import traceback
from pathlib import Path

# Configure proper logging for Vercel
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add backend directory to path for imports
current_dir = Path(__file__).parent  # /backend/api
backend_dir = current_dir.parent  # /backend
sys.path.insert(0, str(backend_dir))

# Set environment variable to indicate Vercel deployment
os.environ["VERCEL_DEPLOYMENT"] = "true"

try:
    # Import the Flask app
    from app import app  # noqa: E402

    logger.info("Successfully imported Flask app")
except Exception as e:
    logger.error(f"Failed to import app: {str(e)}")
    logger.error(traceback.format_exc())


# Define the handler function for Vercel Serverless Functions
def handler(request):
    """
    Vercel handler function for processing API requests
    """
    try:
        logger.info(f"Received request: {json.dumps(str(request))[:200]}...")

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

        # Process the request through the Flask app
        logger.info("Forwarding request to Flask app")
        return app(request.get("environ", {}), request.get("start_response"))

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        logger.error(traceback.format_exc())

        # Return a proper error response
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": str(e), "trace": traceback.format_exc()}
            ),
            "headers": {"Content-Type": "application/json"},
        }
