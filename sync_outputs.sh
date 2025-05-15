#!/bin/bash
# sync_outputs.sh - Script to synchronize backend/outputs to outputs directory
# This is useful when you need to access files in the root outputs directory

set -e

# Display banner
echo "========================================================"
echo "  TukuyBooks Output Sync"
echo "========================================================"

# Create both directories if they don't exist
mkdir -p backend/outputs
mkdir -p outputs

# Sync files from backend/outputs to outputs
echo "Syncing files from backend/outputs to outputs directory..."
cp -r backend/outputs/* outputs/

echo "✅ Files synchronized successfully!"
echo "The generated ebooks are now available in both:"
echo "  - ./backend/outputs/"
echo "  - ./outputs/"
echo "========================================================"
