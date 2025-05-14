#!/bin/bash
# docker-entrypoint.sh - Entry point for the Docker container
set -e

# Default command
COMMAND=${1:-"help"}
SPIDER=${2:-"python_docs"}

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
    cd scripts
    python make_ebook.py "$SPIDER"
    cd ..
    ;;

"optimize")
    echo "Optimizing ebooks"
    cd backend
    ./scripts/book_optimizer.sh "./outputs" "./outputs/optimized"
    ;;

"all")
    echo "Running full pipeline: crawl -> make-ebook -> optimize"
    cd backend

    # Run the spider
    echo "Step 1: Running spider $SPIDER"
    scrapy crawl "$SPIDER"

    # Create the ebook
    echo "Step 2: Creating ebook"
    cd scripts
    python make_ebook.py "$SPIDER"
    cd ..

    # Optimize the ebook
    echo "Step 3: Optimizing ebook"
    ./scripts/book_optimizer.sh "./outputs" "./outputs/optimized"
    ;;

"help" | *)
    echo "Available commands:"
    echo "  crawl [spider_name]    - Run a spider (default: python_docs)"
    echo "  make-ebook [spider_id] - Create an ebook from spider data"
    echo "  optimize               - Optimize the generated ebooks"
    echo "  all [spider_name]      - Run the full pipeline"
    echo "  help                   - Show this help message"
    echo ""
    echo "Examples:"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks crawl python_docs"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks make-ebook python_docs"
    echo "  docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks all python_docs"
    ;;
esac

echo "========================================================"
