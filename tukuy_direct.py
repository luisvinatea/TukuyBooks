#!/usr/bin/env python3
"""
tukuy_direct.py - Direct module version of TukuyBooks Unified Ebook Maker
This version avoids subprocess calls by importing modules directly.
"""

import sys
import os
import argparse
import logging
import importlib.util
import time

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tukuy_direct")

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def import_module_from_path(module_name, file_path):
    """Import a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec:
        logger.error(f"Could not find module at {file_path}")
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_spider_direct(spider_id):
    """Run a spider directly by importing the module"""
    try:
        logger.info(f"Running spider {spider_id} directly...")

        # First, try to import spider_runner from backend.scripts
        try:
            from backend.scripts.spider_runner import run_spider

            success = run_spider(spider_id)
            return success
        except ImportError:
            # Try to import from path
            spider_runner_path = os.path.join(
                project_root, "backend", "scripts", "spider_runner.py"
            )
            if not os.path.exists(spider_runner_path):
                logger.error(
                    f"Could not find spider_runner.py at {spider_runner_path}"
                )
                return False

            spider_runner = import_module_from_path(
                "spider_runner", spider_runner_path
            )
            if not spider_runner:
                return False

            success = spider_runner.run_spider(spider_id)
            return success
    except Exception as e:
        logger.error(f"Error running spider {spider_id}: {e}")
        return False


def make_ebook_direct(spider_id, output_filename=None):
    """Create an ebook directly by importing the module"""
    try:
        logger.info(f"Creating ebook for {spider_id} directly...")

        # Import the tukuy_ebook_maker module
        maker_path = os.path.join(
            project_root, "backend", "scripts", "tukuy_ebook_maker.py"
        )
        if not os.path.exists(maker_path):
            logger.error(
                f"Could not find tukuy_ebook_maker.py at {maker_path}"
            )
            return False

        maker_module = import_module_from_path("maker_module", maker_path)
        if not maker_module:
            return False

        # Get the make_ebook function and call it
        make_ebook_func = getattr(maker_module, "make_ebook", None)
        if not make_ebook_func:
            logger.error(
                "Could not find make_ebook function in tukuy_ebook_maker.py"
            )
            return False

        result = make_ebook_func(spider_id, output_filename)
        return result is not None
    except Exception as e:
        logger.error(f"Error creating ebook for {spider_id}: {e}")
        return False


def optimize_ebooks_direct():
    """Optimize ebooks directly by importing the module"""
    try:
        logger.info("Optimizing ebooks directly...")

        # Import the tukuy_ebook_maker module
        maker_path = os.path.join(
            project_root, "backend", "scripts", "tukuy_ebook_maker.py"
        )
        if not os.path.exists(maker_path):
            logger.error(
                f"Could not find tukuy_ebook_maker.py at {maker_path}"
            )
            return False

        maker_module = import_module_from_path("maker_module", maker_path)
        if not maker_module:
            return False

        # Get the optimize_ebook function and call it
        optimize_func = getattr(maker_module, "optimize_ebook", None)
        if not optimize_func:
            logger.error(
                "Could not find optimize_ebook function in tukuy_ebook_maker.py"
            )
            return False

        result = optimize_func()
        return result
    except Exception as e:
        logger.error(f"Error optimizing ebooks: {e}")
        return False


def list_spiders_direct():
    """List available spiders directly by importing the module"""
    try:
        # Import the tukuy_ebook_maker module
        maker_path = os.path.join(
            project_root, "backend", "scripts", "tukuy_ebook_maker.py"
        )
        if not os.path.exists(maker_path):
            logger.error(
                f"Could not find tukuy_ebook_maker.py at {maker_path}"
            )
            return False

        maker_module = import_module_from_path("maker_module", maker_path)
        if not maker_module:
            return False

        # Get the list_spiders function and call it
        list_func = getattr(maker_module, "list_spiders", None)
        if not list_func:
            logger.error(
                "Could not find list_spiders function in tukuy_ebook_maker.py"
            )
            return False

        list_func()
        return True
    except Exception as e:
        logger.error(f"Error listing spiders: {e}")
        return False


def main():
    """Parse arguments and run the appropriate functions"""
    parser = argparse.ArgumentParser(
        description="TukuyBooks Direct Ebook Maker"
    )
    parser.add_argument(
        "--spider", help="Run the specified spider before creating ebooks"
    )
    parser.add_argument(
        "--make-ebook",
        help="Create an ebook from the specified spider's output",
    )
    parser.add_argument(
        "--optimize", action="store_true", help="Optimize the generated ebooks"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run the complete workflow"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available spiders"
    )
    parser.add_argument(
        "--output", help="Specify output filename (without extension)"
    )

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return True

    # List available spiders
    if args.list:
        return list_spiders_direct()

    success = True

    # Run complete workflow
    if args.all:
        # Import the load_spider_config function
        try:
            from backend.scripts.tukuy_ebook_maker import load_spider_config

            spider_configs = load_spider_config()
        except ImportError:
            maker_path = os.path.join(
                project_root, "backend", "scripts", "tukuy_ebook_maker.py"
            )
            maker_module = import_module_from_path("maker_module", maker_path)
            spider_configs = maker_module.load_spider_config()

        if not spider_configs:
            logger.error("No spiders found in configuration")
            return False

        print("\n==========================================")
        print("  STARTING COMPLETE WORKFLOW")
        print("==========================================")

        # Process each spider
        for i, spider_id in enumerate(spider_configs.keys(), 1):
            print(
                f"\n[{i}/{len(spider_configs)}] Processing {spider_id.upper()}:"
            )
            print("------------------------------------------")

            # Run spider
            print(f"➤ Step 1: Running spider for {spider_id}")
            start_time = time.time()
            if run_spider_direct(spider_id):
                elapsed = time.time() - start_time
                print(f"✓ Spider completed in {elapsed:.2f} seconds")
            else:
                print(f"✘ Failed to run spider: {spider_id}")
                success = False
                continue

            # Create ebook
            print(f"➤ Step 2: Creating ebook for {spider_id}")
            start_time = time.time()
            if make_ebook_direct(spider_id, args.output):
                elapsed = time.time() - start_time
                print(f"✓ Ebook created in {elapsed:.2f} seconds")
            else:
                print(f"✘ Failed to create ebook for: {spider_id}")
                success = False

        # Optimize ebooks
        print("\n➤ Step 3: Optimizing all ebooks")
        start_time = time.time()
        if optimize_ebooks_direct():
            elapsed = time.time() - start_time
            print(f"✓ Ebooks optimized in {elapsed:.2f} seconds")
        else:
            print("✘ Failed to optimize ebooks")
            success = False

        print("\n==========================================")
        if success:
            print("  ✓ WORKFLOW COMPLETED SUCCESSFULLY")
        else:
            print("  ⚠ WORKFLOW COMPLETED WITH ERRORS")
        print("==========================================\n")

        return success

    # Run individual steps
    if args.spider:
        if not run_spider_direct(args.spider):
            success = False

    if args.make_ebook:
        if not make_ebook_direct(args.make_ebook, args.output):
            success = False

    if args.optimize:
        if not optimize_ebooks_direct():
            success = False

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
