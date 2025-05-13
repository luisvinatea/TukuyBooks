#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}┌──────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│   TUKUYBOOKS DEBUG DEPLOYMENT CHECKER    │${NC}"
echo -e "${GREEN}└──────────────────────────────────────────┘${NC}"

# Define directories
BACKEND_DIR="./backend"
ROOT_API_DIR="./api"
LOG_FILE="vercel-debug-$(date +%Y%m%d-%H%M%S).log"

# Function to check files
check_file() {
    if [ -f "$1" ]; then
        echo -e "✅ ${GREEN}File exists:${NC} $1"

        # For Python files, check for syntax errors
        if [[ $1 == *.py ]]; then
            if python -m py_compile "$1" 2>/dev/null; then
                echo -e "   ${GREEN}- Python syntax OK${NC}"
            else
                echo -e "   ${RED}- Python syntax ERROR${NC}"
                python -m py_compile "$1"
                return 1
            fi
        fi

        return 0
    else
        echo -e "❌ ${RED}File missing:${NC} $1"
        return 1
    fi
}

# Check Python version
echo -e "\n${YELLOW}Checking Python version:${NC}"
python --version

# Check project structure
echo -e "\n${YELLOW}Checking critical files:${NC}"
check_file "$BACKEND_DIR/vercel.json"
check_file "$BACKEND_DIR/api/index.py"
check_file "$BACKEND_DIR/api/app.py"
check_file "$BACKEND_DIR/api/requirements.txt"
check_file "$BACKEND_DIR/api/wsgi.py"
check_file "$ROOT_API_DIR/index.py"
check_file "$ROOT_API_DIR/requirements.txt"

# Check configuration file for conflicts
echo -e "\n${YELLOW}Checking for configuration conflicts:${NC}"
if [ -f "$BACKEND_DIR/now.json" ]; then
    echo -e "⚠️ ${YELLOW}Warning:${NC} now.json found in $BACKEND_DIR, may conflict with vercel.json"
else
    echo -e "✅ ${GREEN}No now.json found${NC}"
fi

# Check for multiple vercel.json files
echo -e "\n${YELLOW}Checking for multiple vercel.json files:${NC}"
VERCEL_FILES=$(find . -name "vercel.json" | sort)
echo -e "Found $(echo "$VERCEL_FILES" | wc -l) vercel.json files:"
echo "$VERCEL_FILES" | sed 's/^/  - /'

# Check for app import issues
echo -e "\n${YELLOW}Testing app imports:${NC}"
cd "$BACKEND_DIR/api" || exit 1
echo "import sys; sys.path.append('..'); from app import app; print('Import successful')" | python
cd ../..

echo -e "\n${YELLOW}Testing handler function:${NC}"
cd "$BACKEND_DIR/api" || exit 1
cat >test_handler.py <<'EOF'
import sys
import os
import index

# Mock request
request = {
    "method": "GET",
    "path": "/api/health",
    "query": {},
    "environ": {"PATH_INFO": "/api/health"},
    "start_response": lambda status, headers: print(f"start_response called with status: {status}")
}

# Try the handler
try:
    print("Testing handler...")
    response = index.handler(request)
    print(f"Handler returned: {type(response)}")
    print("Handler test completed")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
EOF

python test_handler.py
rm test_handler.py
cd ../..

echo -e "\n${YELLOW}Checking paths and files:${NC}"
echo "import sys, os; print(f'sys.path = {sys.path}'); print(f'Current dir: {os.getcwd()}'); print(f'Files: {os.listdir(\".\")}')" | python

# Output summary
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Debug Info Saved to:${NC} $LOG_FILE"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
