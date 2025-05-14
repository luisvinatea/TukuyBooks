#!/usr/bin/env python3
"""
spider_runner.py - A utility script to run spiders programmatically
This script allows the Node.js API to execute spiders and track their progress
"""

import sys
import os
import logging
import importlib
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("spider_runner")


def load_spider_config():
    """
    Load the spider configuration from config.json

    Returns:
        dict: Dictionary of spider configurations by ID
    """
    # Try the path depending on where we're running from
    possible_paths = [
        os.path.join("backend", "spiders", "config.json"),  # From project root
        os.path.join("spiders", "config.json"),  # From backend directory
        os.path.join("..", "spiders", "config.json"),  # From scripts directory
    ]

    for config_path in possible_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    return {
                        spider["id"]: spider
                        for spider in config.get("spiders", [])
                    }
            except Exception as e:
                logger.error(
                    f"Error loading spider config from {config_path}: {e}"
                )
                continue

    logger.error("Could not find config.json in any expected location")
    return {}


def run_spider(spider_name):
    """
    Run a spider by name

    Args:
        spider_name (str): The name of the spider to run

    Returns:
        bool: True if the spider ran successfully, False otherwise
    """
    logger.info(f"Starting spider: {spider_name}")

    try:
        # Add necessary paths to sys.path
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent

        for path in [str(current_dir), str(project_root)]:
            if path not in sys.path:
                sys.path.insert(0, path)

        # Load spider configuration
        spider_configs = load_spider_config()
        if spider_name not in spider_configs:
            logger.error(f"Spider {spider_name} not found in configuration")
            return False

        config = spider_configs[spider_name]

        # Import the spider module dynamically
        try:
            # Adjust module name based on how it's referenced in config.json
            raw_module_name = config.get(
                "module", f"spiders.{spider_name}_spider"
            )

            # Try different module name variations
            possible_module_names = [
                raw_module_name,
                raw_module_name.replace("backend.", ""),
                f"spiders.{spider_name}_spider",
            ]

            spider_module = None
            for possible_name in possible_module_names:
                try:
                    spider_module = importlib.import_module(possible_name)
                    logger.info(
                        f"Successfully imported module: {possible_name}"
                    )
                    break
                except ImportError as e:
                    logger.debug(f"Could not import {possible_name}: {e}")
                    continue

            if not spider_module:
                logger.error(
                    f"Could not import any module variation for {spider_name}"
                )
                return False

            class_name = config.get("class")
            spider_class = None

            if class_name:
                # Use the class name from config
                spider_class = getattr(spider_module, class_name, None)
            else:
                # Find the spider class by naming convention
                for attr_name in dir(spider_module):
                    attr = getattr(spider_module, attr_name)
                    if isinstance(attr, type) and attr_name.lower().endswith(
                        "spider"
                    ):
                        spider_class = attr
                        break

            if not spider_class:
                logger.error(f"Could not find spider class for {spider_name}")
                return False

            # Create a spider instance
            spider = spider_class()

            # Configure scrapy and run the spider
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings

            settings = get_project_settings()
            settings.set("FEED_FORMAT", "jsonlines")
            settings.set(
                "FEED_URI",
                os.path.join("backend", "outputs", f"{spider_name}.jl"),
            )

            process = CrawlerProcess(settings)
            process.crawl(spider)
            process.start()  # This blocks until the spider is finished

            logger.info(f"Spider {spider_name} finished successfully")
            return True

        except ImportError as e:
            logger.error(f"Could not import spider module: {e}")
            return False

    except Exception as e:
        logger.error(f"Error running spider {spider_name}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
        logger.info("Usage: python spider_runner.py <spider_name>")
        logger.info("       python spider_runner.py --list")
        logger.info("")
        logger.info("Options:")
        logger.info("  --list, -l    List available spiders")
        sys.exit(1)

    if sys.argv[1] == "--list" or sys.argv[1] == "-l":
        spider_configs = load_spider_config()
        if not spider_configs:
            logger.info("No spiders found in configuration")
        else:
            logger.info("Available spiders:")
            for spider_id, config in spider_configs.items():
                logger.info(
                    f"  - {spider_id}: {config.get('name', 'Unnamed')} - {config.get('description', 'No description')}"
                )
        sys.exit(0)

    spider_name = sys.argv[1]
    success = run_spider(spider_name)

    sys.exit(0 if success else 1)
