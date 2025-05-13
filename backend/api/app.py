"""api.py
This module provides a Flask API for interacting with the TukuyBooks backend.
It allows running spiders, generating ebooks, and downloading the results.
"""

import os
import sys
import json
import subprocess
import logging
import uuid
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from scripts.make_ebook import EbookMaker, PythonDocsEbookMaker
from scripts.epub_checker import EpubChecker

# Import our custom modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.dirname(parent_dir))

# Set up logging
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(parent_dir, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, "logs", "api.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load spider configuration
SPIDERS_CONFIG_PATH = os.path.join(parent_dir, "spiders", "config.json")
try:
    with open(SPIDERS_CONFIG_PATH, "r") as f:
        SPIDERS_CONFIG = json.load(f)
except Exception as e:
    logger.error(f"Failed to load spider configuration: {e}")
    SPIDERS_CONFIG = {"spiders": []}


# Helper functions
def get_available_spiders():
    """Get a list of available spiders.

    Returns:
        list: List of spider configurations.
    """
    return SPIDERS_CONFIG.get("spiders", [])


def get_spider_by_id(spider_id):
    """Get a spider configuration by ID.

    Args:
        spider_id (str): ID of the spider.

    Returns:
        dict: Spider configuration or None if not found.
    """
    for spider in get_available_spiders():
        if spider.get("id") == spider_id:
            return spider
    return None


def run_spider(spider_id):
    """Run a spider to scrape documentation.

    Args:
        spider_id (str): ID of the spider to run.

    Returns:
        dict: Status of the spider run.
    """
    spider = get_spider_by_id(spider_id)
    if not spider:
        return {
            "success": False,
            "message": f"Spider with ID '{spider_id}' not found",
        }

    # Create a unique job ID
    job_id = str(uuid.uuid4())

    # Prepare output directory
    output_dir = os.path.join(parent_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # Run the spider using Scrapy
    cmd = [
        "scrapy",
        "crawl",
        spider_id,
        "-o",
        os.path.join(output_dir, f"{spider_id}.jl"),
        "-s",
        f"JOBDIR={os.path.join(output_dir, 'job_state')}",
    ]

    try:
        # Run the process in the background
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )

        return {
            "success": True,
            "message": f"Spider '{spider.get('name')}' started",
            "job_id": job_id,
            "spider_id": spider_id,
        }
    except Exception as e:
        logger.error(f"Failed to run spider: {e}")
        return {"success": False, "message": f"Failed to run spider: {str(e)}"}


def get_spider_status(spider_id):
    """Get the status of a spider.

    Args:
        spider_id (str): ID of the spider.

    Returns:
        dict: Status information.
    """
    spider = get_spider_by_id(spider_id)
    if not spider:
        return {
            "success": False,
            "message": f"Spider with ID '{spider_id}' not found",
        }

    # Check if output file exists
    output_file = os.path.join(parent_dir, "outputs", f"{spider_id}.jl")
    if not os.path.exists(output_file):
        return {
            "success": True,
            "spider_id": spider_id,
            "status": "not_started",
            "message": "Spider has not been run yet",
        }

    # Check if the spider is still running
    job_state_dir = os.path.join(parent_dir, "outputs", "job_state")
    is_running = os.path.exists(job_state_dir)

    # Get some stats about the output file
    try:
        with open(output_file, "r") as f:
            line_count = sum(1 for _ in f)

        file_size = os.path.getsize(output_file)

        return {
            "success": True,
            "spider_id": spider_id,
            "status": "running" if is_running else "completed",
            "items_scraped": line_count,
            "file_size": file_size,
            "file_size_human": f"{file_size / (1024 * 1024):.2f} MB",
        }
    except Exception as e:
        logger.error(f"Failed to get spider status: {e}")
        return {
            "success": False,
            "message": f"Failed to get spider status: {str(e)}",
        }


def create_ebook(spider_id, format="epub"):
    """Create an ebook from scraped data.

    Args:
        spider_id (str): ID of the spider that generated the data.
        format (str): Format of the ebook ('epub' or 'pdf').

    Returns:
        dict: Status of the ebook creation.
    """
    spider = get_spider_by_id(spider_id)
    if not spider:
        return {
            "success": False,
            "message": f"Spider with ID '{spider_id}' not found",
        }

    # Check if output file exists
    output_file = os.path.join(parent_dir, "outputs", f"{spider_id}.jl")
    if not os.path.exists(output_file):
        return {
            "success": False,
            "message": f"No data found for spider '{spider_id}'",
        }

    # Create ebook maker based on spider ID
    if spider_id == "python_docs":
        ebook_maker = PythonDocsEbookMaker()
    else:
        # Use generic ebook maker
        ebook_maker = EbookMaker(
            spider_id,
            title=spider.get("name", "Documentation"),
            author=spider.get("author", "Unknown"),
        )

    # Generate EPUB
    try:
        output_filename = f"{spider.get('output_prefix', spider_id)}.epub"
        epub_path = ebook_maker.create_epub(output_filename)

        if not epub_path or not os.path.exists(epub_path):
            return {"success": False, "message": "Failed to create EPUB"}

        # Check EPUB for broken links
        checker = EpubChecker(epub_path)
        check_results = checker.check_links()

        # If PDF is requested, convert EPUB to PDF
        pdf_path = None
        if format.lower() == "pdf":
            pdf_filename = f"{spider.get('output_prefix', spider_id)}.pdf"
            pdf_path = os.path.join(parent_dir, "outputs", pdf_filename)

            # Use Calibre for conversion
            cmd = [
                "ebook-convert",
                epub_path,
                pdf_path,
                "--paper-size",
                "letter",
                "--pdf-page-numbers",
                "--preserve-cover-aspect-ratio",
            ]

            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to convert EPUB to PDF: {e}")
                return {
                    "success": False,
                    "message": f"Failed to convert EPUB to PDF: {str(e)}",
                }

        return {
            "success": True,
            "spider_id": spider_id,
            "epub_path": epub_path,
            "pdf_path": pdf_path,
            "check_results": check_results,
        }
    except Exception as e:
        logger.error(f"Failed to create ebook: {e}")
        return {
            "success": False,
            "message": f"Failed to create ebook: {str(e)}",
        }


def get_available_ebooks():
    """Get a list of available ebooks in the outputs directory.

    Returns:
        list: List of ebook information dictionaries.
    """
    ebooks = []
    outputs_dir = os.path.join(parent_dir, "outputs")

    # Create outputs dir if it doesn't exist
    os.makedirs(outputs_dir, exist_ok=True)

    # Map of spider IDs to names/descriptions
    spider_info = {}
    for spider in get_available_spiders():
        spider_info[spider["id"]] = {
            "name": spider.get("name", "Unknown"),
            "description": spider.get("description", ""),
            "output_prefix": spider.get("output_prefix", spider["id"]),
        }

    # Get all files in the outputs directory
    for filename in os.listdir(outputs_dir):
        file_path = os.path.join(outputs_dir, filename)
        if not os.path.isfile(file_path):
            continue

        # Skip temporary files
        if filename.startswith(".") or filename.startswith("_"):
            continue

        # Get file extension
        _, ext = os.path.splitext(filename)

        # Find the spider that created this file
        spider_id = None
        title = (
            filename  # Default to filename if we can't determine the spider
        )
        description = ""

        for sid, info in spider_info.items():
            prefix = info["output_prefix"]
            if filename.startswith(prefix):
                spider_id = sid
                title = info["name"]
                description = info["description"]
                break

        # See if we already have an entry for this ebook
        ebook_entry = None
        for ebook in ebooks:
            if ebook["title"] == title:
                ebook_entry = ebook
                break

        # Create new entry if needed
        if not ebook_entry:
            ebook_entry = {
                "title": title,
                "description": description,
                "spider_id": spider_id,
                "epub_path": None,
                "pdf_path": None,
            }
            ebooks.append(ebook_entry)

        # Add the file path based on extension
        if ext.lower() == ".epub":
            ebook_entry["epub_path"] = file_path
        elif ext.lower() == ".pdf":
            ebook_entry["pdf_path"] = file_path

    return ebooks


# API routes
@app.route("/api/spiders", methods=["GET"])
def api_get_spiders():
    """Get a list of available spiders."""
    return jsonify({"success": True, "spiders": get_available_spiders()})


@app.route("/api/spiders/<spider_id>/run", methods=["POST"])
def api_run_spider(spider_id):
    """Run a spider."""
    return jsonify(run_spider(spider_id))


@app.route("/api/spiders/<spider_id>/status", methods=["GET"])
def api_spider_status(spider_id):
    """Get the status of a spider."""
    return jsonify(get_spider_status(spider_id))


@app.route("/api/spiders/<spider_id>/ebook", methods=["POST"])
def api_create_ebook(spider_id):
    """Create an ebook from scraped data."""
    format = request.json.get("format", "epub")
    return jsonify(create_ebook(spider_id, format))


@app.route("/api/ebooks", methods=["GET"])
def api_get_ebooks():
    """Get a list of available ebooks."""
    try:
        ebooks = get_available_ebooks()
        return jsonify({"success": True, "ebooks": ebooks})
    except Exception as e:
        logger.error(f"Failed to get available ebooks: {e}")
        return jsonify(
            {
                "success": False,
                "message": f"Failed to get available ebooks: {str(e)}",
            }
        ), 500


@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Download a file."""
    try:
        file_path = os.path.join(parent_dir, "outputs", filename)
        if not os.path.exists(file_path):
            return jsonify(
                {"success": False, "message": f"File '{filename}' not found"}
            ), 404

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return jsonify(
            {"success": False, "message": f"Failed to download file: {str(e)}"}
        ), 500


# Run the app
if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join("backend", "logs"), exist_ok=True)

    # Run the app
    app.run(debug=True, port=5000)
