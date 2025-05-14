#!/bin/bash
# build_all_ebooks.sh - Builds all available ebooks from scraped content

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Building ebooks from all available spider outputs..."

# Get list of spider files from the outputs directory
SPIDER_FILES=$(find ./backend/outputs -name "*.jl" -type f)

if [ -z "$SPIDER_FILES" ]; then
    echo "No spider output files found in backend/outputs/"
    exit 1
fi

# Build ebooks from each spider output
for file in $SPIDER_FILES; do
    SPIDER_ID=$(basename "$file" .jl)
    echo "Building ebook for $SPIDER_ID"
    python backend/scripts/make_ebook.py "$SPIDER_ID"
done

echo "All ebooks built successfully!"
echo "Output files are in backend/outputs/ directory"

# List created ebooks
EBOOKS=$(find ./backend/outputs -name "*.epub" -type f)
echo "Created ebooks:"
for book in $EBOOKS; do
    echo "- $(basename "$book")"
done
