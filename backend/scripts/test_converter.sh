#!/bin/bash
# Test script to verify book_converter.sh runs non-interactively

echo "Testing book_converter.sh with INPUT_EPUB environment variable"

# Find first available EPUB file
EPUB_FILE=$(find ../outputs -name "*.epub" -print -quit)

if [ -z "$EPUB_FILE" ]; then
    echo "Error: No EPUB file found in ../outputs"
    exit 1
fi

echo "Found EPUB file: $EPUB_FILE"
echo "Running converter..."

# Set environment variable and run converter
INPUT_EPUB="$EPUB_FILE" ./book_converter.sh

echo "Test completed"
