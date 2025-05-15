#!/bin/bash
# docker-entrypoint.sh - Entry point for TukuyBooks Docker container

set -e

# Default command
COMMAND=${1:-"help"}
SPIDER=${2:-"python_docs"}

# Install tqdm for progress bars if not already installed
if ! python -c "import tqdm" &>/dev/null; then
    echo "Installing tqdm for progress bar support..."
    pip install --no-cache-dir tqdm
fi

echo "========================================================"
echo "  TukuyBooks Spider Docker Container"
echo "========================================================"

case "$COMMAND" in
"crawl")
    echo "Running spider: $SPIDER"
    cd backend
    # Run the spider using scrapy
    scrapy crawl "$SPIDER"
    ;;

"make-ebook")
    echo "Creating ebook from spider data: $SPIDER"
    cd backend
    python scripts/tukuy_ebook_maker.py --make-ebook "$SPIDER"
    ;;

"convert")
    echo "Converting ebooks"
    cd backend
    # Set DOCKER_CONTAINER=1 to ensure non-interactive mode
    export DOCKER_CONTAINER=1
    python scripts/tukuy_ebook_maker.py --convert
    ;;

"unified")
    echo "Using unified ebook maker"
    shift # Remove the 'unified' command
    cd backend
    python scripts/tukuy_ebook_maker.py "$@"
    ;;

"all")
    echo "Running full pipeline: crawl -> make-ebook -> convert"
    cd backend

    # Set DOCKER_CONTAINER=1 to ensure non-interactive mode
    export DOCKER_CONTAINER=1
    
    # Use the unified ebook maker for the full pipeline
    echo "Running unified ebook maker pipeline for $SPIDER"
    python scripts/tukuy_ebook_maker.py --spider "$SPIDER" --make-ebook "$SPIDER" --convert
    ;;

"legacy-all")
    echo "Running legacy full pipeline: crawl -> make-ebook -> convert"
    cd backend

    # Run the spider
    echo "Step 1: Running spider $SPIDER"
    scrapy crawl "$SPIDER"

    # Create the ebook
    echo "Step 2: Creating ebook"
    cd scripts
    python make_ebook.py "$SPIDER"
    cd ..

    # Convert the ebook
    echo "Step 3: converting ebook"
    ./scripts/book_converter.sh "./outputs" "./outputs/converted"
    ;;

"help" | *)
    echo "Available commands:"
    echo "  crawl [spider_name]    - Run a spider (default: python_docs)"
    echo "  make-ebook [spider_id] - Create an ebook from spider data"
    echo "  convert               -  Convert the generated ebooks"
    echo "  all [spider_name]      - Run the full pipeline with unified tool"
    echo "  legacy-all [spider]    - Run full pipeline with original tools"
    echo "  unified [options]      - Run the unified ebook maker directly"
    echo "  help                   - Show this help message"
    echo ""
    echo "Unified Tool Options:"
    echo "  --list                - List available spiders"
    echo "  --spider SPIDER_ID    - Run the specified spider"
    echo "  --make-ebook SPIDER_ID - Create an ebook"
    echo "  --convert               - Convert the generated ebooks"
    echo "  --all                 - Run complete workflow for all spiders"
    echo "  --output OUTPUT       - Specify output filename"
    echo ""
    echo "Examples:"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks crawl python_docs"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks make-ebook python_docs"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks all python_docs"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks unified --all"
    ;;
esac

echo "========================================================"
