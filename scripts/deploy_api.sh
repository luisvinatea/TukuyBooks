#!/bin/bash

# Define variables
BACKEND_DIR="./backend"
VERCEL_CONFIG="$BACKEND_DIR/vercel.json"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
LOG_FILE="vercel-deploy-$TIMESTAMP.log"

# Display banner
echo "==============================================="
echo "  TUKUYBOOKS API DEPLOYMENT TO VERCEL"
echo "==============================================="

# Check if Vercel CLI is installed
if ! command -v vercel &>/dev/null; then
    echo "⚠️ Vercel CLI is not installed. Installing..."
    npm install -g vercel
fi

# Ensure we're in the project root
cd "$(dirname "$0")/.." || exit 1

# Check if vercel.json exists
if [ ! -f "$VERCEL_CONFIG" ]; then
    echo "❌ Error: vercel.json not found at $VERCEL_CONFIG"
    exit 1
fi

# Verify we don't have configuration conflicts
if [ -f "$BACKEND_DIR/now.json" ]; then
    echo "⚠️ Warning: now.json found, which may conflict with vercel.json"
    read -r -p "Do you want to remove now.json? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm "$BACKEND_DIR/now.json"
        echo "✅ Removed now.json to prevent conflicts"
    else
        echo "⚠️ Proceeding with potential configuration conflicts..."
    fi
fi

# Check for nested vercel.json files that could cause conflicts
NESTED_VERCEL_FILES=$(find "$BACKEND_DIR" -path "$BACKEND_DIR/vercel.json" -prune -o -name "vercel.json" -print)
if [ -n "$NESTED_VERCEL_FILES" ]; then
    echo "⚠️ Warning: Found nested vercel.json files that may cause conflicts:"
    echo "$NESTED_VERCEL_FILES"
    read -r -p "Do you want to remove these nested config files? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        for file in $NESTED_VERCEL_FILES; do
            rm "$file"
            echo "✅ Removed $file to prevent conflicts"
        done
    else
        echo "⚠️ Proceeding with potential configuration conflicts..."
    fi
fi

# Deploy to Vercel
echo "🚀 Deploying TukuyBooks backend to Vercel..."
cd "$BACKEND_DIR" || exit 1

# Run deployment with production flag if specified
if [ "$1" == "--prod" ]; then
    echo "🔥 Deploying to PRODUCTION environment..."
    if vercel --prod | tee "../$LOG_FILE"; then
        DEPLOYMENT_SUCCESS=true
    else
        DEPLOYMENT_SUCCESS=false
    fi
else
    echo "🧪 Deploying to PREVIEW environment..."
    if vercel | tee "../$LOG_FILE"; then
        DEPLOYMENT_SUCCESS=true
    else
        DEPLOYMENT_SUCCESS=false
    fi
fi

# Check deployment status
if [ "$DEPLOYMENT_SUCCESS" = true ]; then
    echo "✅ Deployment completed successfully!"
    DEPLOY_URL=$(grep -o 'https://[^ ]*\.vercel\.app' "../$LOG_FILE" | head -1)
    if [ -n "$DEPLOY_URL" ]; then
        echo "🌐 Deployed to: $DEPLOY_URL"
        echo "🔍 Testing API health endpoint..."
        HEALTH_URL="$DEPLOY_URL/_vercel/health"
        if curl -s "$HEALTH_URL" | grep -q "ok"; then
            echo "✅ API health check passed!"
        else
            echo "⚠️ API health check may have failed. Check $HEALTH_URL manually."
        fi
    fi
else
    echo "❌ Deployment encountered issues. Check the log for details."
fi

echo "📝 Deployment log saved to: $LOG_FILE"
echo "==============================================="
