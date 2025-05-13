from flask import jsonify
from app import app as flask_app


# For Vercel health checks and simple testing
@flask_app.route("/_vercel/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "TukuyBooks API is running"})


# Export the Flask app for Vercel
app = flask_app


# Handler for Vercel serverless functions
def handler(event, context):
    """
    AWS Lambda / Vercel serverless handler for the Flask app
    """
    return app(event, context)
