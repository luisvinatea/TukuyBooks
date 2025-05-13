#!/bin/bash
# deploy_to_vercel.sh - Script to deploy TukuyBooks API to Vercel

# Make sure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR/.." || exit

echo "===== Deploying TukuyBooks API to Vercel ====="

# Check if Vercel CLI is installed
if ! command -v vercel &>/dev/null; then
    echo "Vercel CLI is not installed. Please install it with:"
    echo "npm install -g vercel"
    exit 1
fi

# Make sure we're in the backend directory
cd backend || exit

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes that won't be included in the deployment."
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verify Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Verify Python dependencies for spider execution
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel --prod

echo "===== Deployment Complete ====="
echo "Your API should now be available at https://tukuybooks.vercel.app"
