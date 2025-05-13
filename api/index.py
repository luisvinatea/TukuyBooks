"""
Vercel Serverless Function for TukuyBooks API
This serves as the entry point for the TukuyBooks API on Vercel
"""

import sys
from pathlib import Path

# Add project root and backend directories to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

# Import the Flask app from the backend
from backend.api.app import app


# Define the handler function for Vercel Serverless Functions
def handler(request, **kwargs):
    """
    Vercel handler function for processing API requests
    """
    # Process the request through the Flask app
    return app(request["environ"], request.start_response)
