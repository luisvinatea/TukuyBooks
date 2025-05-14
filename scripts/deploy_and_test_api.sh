#!/bin/bash

# Vercel deployment script with API testing
# This script deploys the API to Vercel and tests the endpoints

# Set variables
BACKEND_DIR="$(pwd)/backend"
PROJECT_NAME="tukuybooks"
API_URL="https://tukuybooks.vercel.app/api"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &>/dev/null; then
    echo -e "${RED}Error: Vercel CLI is not installed${NC}"
    echo "Please install it with: npm i -g vercel"
    exit 1
fi

# Navigate to backend directory
cd "$BACKEND_DIR" || {
    echo -e "${RED}Error: Backend directory not found${NC}"
    exit 1
}

echo -e "${BLUE}=== Deploying TukuyBooks API to Vercel ===${NC}"
echo ""

# Login to Vercel if needed (will skip if already logged in)
echo -e "${YELLOW}Checking Vercel authentication...${NC}"
vercel whoami &>/dev/null || vercel login

# Install dependencies if needed
echo -e "${YELLOW}Installing dependencies...${NC}"
npm install

# Deploy to Vercel
echo -e "${YELLOW}Deploying to Vercel...${NC}"
vercel deploy --prod --yes

# Wait a bit for the deployment to propagate
echo -e "${YELLOW}Waiting for deployment to propagate...${NC}"
sleep 10

# Test the API endpoints
echo -e "${YELLOW}Testing API endpoints...${NC}"
node scripts/test-api.js

# Completion message
echo ""
echo -e "${GREEN}Deployment completed!${NC}"
echo -e "API URL: ${BLUE}$API_URL${NC}"
echo -e "Frontend should connect to this URL for API requests"
echo -e "${YELLOW}If you encounter connection issues, verify CORS settings in the API${NC}"

exit 0
