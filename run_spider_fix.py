#!/usr/bin/env python3
"""
Fix for the hanging issue in tukuy_ebook_maker.py
This script directly runs the spider_runner module with proper Python path setup.
"""

import sys
import os
import subprocess
import time
import importlib


def run_fixed_spider(spider_id):
    """
    Run a spider using the module import approach rather than subprocess

    Args:
        spider_id (str): ID of the spider to run

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Running spider: {spider_id}")

    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        # Try to import the spider_runner module
        from backend.scripts.spider_runner import run_spider

        # Run the spider directly
        success = run_spider(spider_id)
        return success
    except ImportError as e:
        print(f"Error importing spider_runner module: {e}")
        return False
    except Exception as e:
        print(f"Error running spider {spider_id}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_spider_fix.py <spider_id>")
        sys.exit(1)

    success = run_fixed_spider(sys.argv[1])
    sys.exit(0 if success else 1)
