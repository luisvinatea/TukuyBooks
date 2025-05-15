#!/bin/bash
# Script to run the TukuyBooks Streamlit frontend in Docker

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building TukuyBooks Streamlit frontend Docker image...${NC}"

# Navigate to project root directory
cd "$(dirname "$(dirname "$(readlink -f "$0")")")" || exit

# Build the Docker image
docker build -t tukuybooks-streamlit -f frontend/Dockerfile .

echo -e "${GREEN}Docker image built successfully!${NC}"

# Run the Docker container
echo -e "${BLUE}Starting TukuyBooks Streamlit frontend...${NC}"

# Run with port mapping and volume mount for persistent data
docker run --rm -it \
    -p 8501:8501 \
    -v "$(pwd)/backend/outputs:/app/backend/outputs" \
    --name tukuybooks-streamlit \
    tukuybooks-streamlit

# Exit code
exit $?
