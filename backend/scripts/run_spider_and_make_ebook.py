#!/usr/bin/env python3
"""
run_spider_and_make_ebook.py - Run a spider and create an ebook from its output
This script combines spider_runner.py and make_ebook functionality
"""

import sys
import os
import logging
import importlib
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("run_spider_and_make_ebook")


def run_spider(spider_name):
    """
    Run a spider using spider_runner.py

    Args:
        spider_name (str): The name of the spider to run

    Returns:
        bool: True if the spider ran successfully, False otherwise
    """
    logger.info(f"Running spider: {spider_name}")

    # Get the path to the spider_runner.py script
    script_dir = Path(__file__).resolve().parent
    spider_runner_path = script_dir / "spider_runner.py"

    try:
        # Run the spider_runner.py script with the given spider name
        result = subprocess.run(
            [sys.executable, str(spider_runner_path), spider_name],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Spider output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running spider {spider_name}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


def make_ebook(spider_name, output_filename=None):
    """
    Create an ebook from the output of a spider

    Args:
        spider_name (str): The name of the spider that produced the data
        output_filename (str): Optional name for the output file

    Returns:
        bool: True if the ebook was created successfully, False otherwise
    """
    logger.info(f"Creating ebook for {spider_name}")

    # Get the path to the ebook maker scripts
    script_dir = Path(__file__).resolve().parent

    try:
        # Choose the appropriate ebook maker script based on the spider name
        if spider_name == "python_docs":
            ebook_maker_path = script_dir / "make_ebook_pydocs.py"
        elif spider_name == "mdn_docs":
            ebook_maker_path = script_dir / "make_ebook_mdn.py"
        else:
            logger.error(f"No ebook maker available for {spider_name}")
            return False

        # Build the command
        cmd = [sys.executable, str(ebook_maker_path)]
        if output_filename:
            cmd.append(output_filename)

        # Run the ebook maker script
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True
        )
        logger.info(f"Ebook maker output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating ebook for {spider_name}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
        logger.info(
            "Usage: python run_spider_and_make_ebook.py <spider_name> [output_filename] [--ebook-only]"
        )
        logger.info("")
        logger.info("Options:")
        logger.info(
            "  --ebook-only    Skip running the spider, just create the ebook"
        )
        sys.exit(1)

    # Parse command line arguments
    spider_name = sys.argv[1]
    output_filename = None
    ebook_only = False

    for arg in sys.argv[2:]:
        if arg == "--ebook-only":
            ebook_only = True
        else:
            output_filename = arg

    # Run the spider if needed
    if not ebook_only:
        if not run_spider(spider_name):
            logger.error(f"Failed to run spider {spider_name}")
            sys.exit(1)

    # Create the ebook
    if not make_ebook(spider_name, output_filename):
        logger.error(f"Failed to create ebook for {spider_name}")
        sys.exit(1)

    logger.info(f"Successfully created ebook for {spider_name}")
    sys.exit(0)
