#!/usr/bin/env python3
"""
rebuild_python_docs.py - Rebuilds the entire Python documentation e-book
This script deletes the existing Python docs outputs and rebuilds them from scratch
"""

import os
import logging
import sys
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("rebuild_python_docs")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "backend" / "outputs"
PYTHON_DOCS_JL = OUTPUTS_DIR / "python_docs.jl"
PYTHON_DOCS_EPUB = OUTPUTS_DIR / "python_docs.epub"


def clean_existing_outputs():
    """Remove existing Python documentation outputs"""
    logger.info("Cleaning existing Python documentation outputs")

    if PYTHON_DOCS_JL.exists():
        logger.info(f"Removing {PYTHON_DOCS_JL}")
        PYTHON_DOCS_JL.unlink()

    if PYTHON_DOCS_EPUB.exists():
        logger.info(f"Removing {PYTHON_DOCS_EPUB}")
        PYTHON_DOCS_EPUB.unlink()


def run_spider(max_depth=4):
    """Run the Python documentation spider"""
    logger.info(
        f"Running Python documentation spider with max_depth={max_depth}"
    )

    # Allow specifying the max_depth value to the spider
    spider_runner_path = SCRIPT_DIR / "spider_runner.py"
    cmd = [
        sys.executable,
        str(spider_runner_path),
        "python_docs",
        "-a",
        f"max_depth={max_depth}",
    ]

    try:
        subprocess.run(cmd, check=True)
        logger.info("Spider completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Spider failed with error code {e.returncode}")
        return False


def make_ebook():
    """Create the Python documentation ebook"""
    logger.info("Creating Python documentation ebook")

    ebook_maker_path = SCRIPT_DIR / "make_ebook_pydocs.py"
    cmd = [sys.executable, str(ebook_maker_path)]

    try:
        subprocess.run(cmd, check=True)
        logger.info("Ebook created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ebook creation failed with error code {e.returncode}")
        return False


if __name__ == "__main__":
    # Parse command-line arguments
    max_depth = 4  # Default depth
    skip_spider = False
    skip_clean = False

    for arg in sys.argv[1:]:
        if arg.startswith("--depth="):
            try:
                max_depth = int(arg.split("=")[1])
            except (IndexError, ValueError):
                logger.warning(
                    f"Invalid depth argument: {arg}, using default={max_depth}"
                )
        elif arg == "--skip-spider":
            skip_spider = True
        elif arg == "--skip-clean":
            skip_clean = True

    # Print help if requested
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: rebuild_python_docs.py [options]")
        print("")
        print("Options:")
        print("  --depth=N       Set the maximum crawl depth (default: 4)")
        print(
            "  --skip-spider   Skip running the spider, just create the ebook"
        )
        print("  --skip-clean    Don't delete existing files before running")
        print("  --help, -h      Show this help message")
        sys.exit(0)

    # Step 1: Clean existing outputs (optional)
    if not skip_clean:
        clean_existing_outputs()

    # Step 2: Run the spider (optional)
    if not skip_spider:
        success = run_spider(max_depth)
        if not success:
            logger.error("Spider failed, aborting")
            sys.exit(1)

    # Step 3: Make the ebook
    success = make_ebook()
    if not success:
        logger.error("Ebook creation failed")
        sys.exit(1)

    logger.info("Python documentation rebuild completed successfully")

    # Report success
    if PYTHON_DOCS_EPUB.exists():
        size_mb = PYTHON_DOCS_EPUB.stat().st_size / (1024 * 1024)
        logger.info(f"Created {PYTHON_DOCS_EPUB} ({size_mb:.2f} MB)")

    sys.exit(0)
