#!/usr/bin/env python3
"""
tukuy_ebook_maker_wrapper.py - Wrapper to ensure correct module imports
"""

import sys
import os
import runpy

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Run the actual script as if it was the main module
if __name__ == "__main__":
    # Pass all command-line arguments to the main script
    sys.argv[0] = "backend/scripts/tukuy_ebook_maker.py"
    runpy.run_path("backend/scripts/tukuy_ebook_maker.py", run_name="__main__")
