#!/bin/bash
# deploy_docker.sh - Script to build and push the Docker image to Docker Hub

set -e

# Config
DOCKER_HUB_USERNAME="luisvinatea" # Change this to your Docker Hub username
DOCKER_REPO="tukuybooks"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${DOCKER_REPO}:${IMAGE_TAG}"

# Display banner
echo "========================================================"
echo "  TukuyBooks Docker Deployment"
echo "========================================================"

# Check if docker is installed
if ! command -v docker &>/dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Build the Docker image
echo "Building Docker image: ${FULL_IMAGE_NAME}"
docker build -t ${FULL_IMAGE_NAME} .

# Prompt for Docker Hub login
echo ""
echo "Please log in to Docker Hub to push the image."
docker login

# Push the image to Docker Hub
echo ""
echo "Pushing image to Docker Hub: ${FULL_IMAGE_NAME}"
docker push ${FULL_IMAGE_NAME}

echo ""
echo "✅ Image deployed successfully!"
echo ""
echo "Users can pull this image with:"
echo "docker pull ${FULL_IMAGE_NAME}"
echo ""
echo "Or run it directly:"
echo "docker run -v \$(pwd)/outputs:/app/backend/outputs ${FULL_IMAGE_NAME} all python_docs"
echo "========================================================"
