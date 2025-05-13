"""
Vercel Serverless Function for TukuyBooks API
This serves as the entry point for the TukuyBooks API on Vercel
"""

import sys
import os
from pathlib import Path

# Add backend directory to path for imports
current_dir = Path(__file__).parent  # /backend/api
backend_dir = current_dir.parent  # /backend
sys.path.insert(0, str(backend_dir))

# Set environment variable to indicate Vercel deployment
os.environ["VERCEL_DEPLOYMENT"] = "true"

# Import the Flask app
from app import app  # noqa: E402


# Define the handler function for Vercel Serverless Functions
def handler(request):
    """
    Vercel handler function for processing API requests
    """
    # Handle preflight OPTIONS requests for CORS
    if request.get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            },
        }

    # Process the request through the Flask app
    return app(request.get("environ", {}), request.get("start_response"))
