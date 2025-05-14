#!/bin/bash
# run_docker.sh - Script to build and run the TukuyBooks Docker container

set -e

# Display banner
echo "========================================================"
echo "  TukuyBooks Docker Runner"
echo "========================================================"

# Create output directory if it doesn't exist
mkdir -p outputs

# Build the Docker image
echo "Building Docker image..."
docker build -t tukuybooks:latest .

# Display usage
echo ""
echo "Docker image built successfully!"
echo ""
echo "To run the container, use one of the following commands:"
echo ""
echo "  Get help:"
echo "    docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks:latest help"
echo ""
echo "  Run the python_docs spider:"
echo "    docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks:latest crawl python_docs"
echo ""
echo "  Create an ebook from crawled data:"
echo "    docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks:latest make-ebook python_docs"
echo ""
echo "  Run the full pipeline (crawl, make-ebook, optimize):"
echo "    docker run -v \$(pwd)/outputs:/app/backend/outputs tukuybooks:latest all python_docs"
echo ""
echo "The output files will be available in the ./outputs directory"
echo "========================================================"
