#!/usr/bin/env python3
"""
spider_runner.py - A utility script to run spiders programmatically
This script allows the Node.js API to execute spiders and track their progress
"""

import sys
import os
import logging
import importlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("spider_runner")


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

        # Import the spider module dynamically
        try:
            spider_module = importlib.import_module(
                f"spiders.{spider_name}_spider"
            )
            spider_class = None

            # Find the spider class
            for attr_name in dir(spider_module):
                attr = getattr(spider_module, attr_name)
                if isinstance(attr, type) and attr_name.lower().endswith(
                    "spider"
                ):
                    spider_class = attr
                    break

            if not spider_class:
                logger.error(
                    f"Could not find spider class in {spider_name}_spider.py"
                )
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
    if len(sys.argv) != 2:
        logger.error("Usage: python spider_runner.py <spider_name>")
        sys.exit(1)

    spider_name = sys.argv[1]
    success = run_spider(spider_name)

    sys.exit(0 if success else 1)
