#!/bin/bash
# filepath: /home/luisvinatea/DEVinatea/Repos/TukuyBooks/backend/scripts/test_unified_workflow.sh
# test_unified_workflow.sh - Script to test the unified ebook maker workflow

# Set up colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}       TukuyBooks Unified Workflow Test Script         ${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Check if we're in the right directory
if [[ ! -f "tukuy_ebook_maker.py" && ! -f "backend/scripts/tukuy_ebook_maker.py" ]]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}cd /path/to/TukuyBooks${NC}"
    exit 1
fi

# Function to handle errors
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Find the unified script
UNIFIED_SCRIPT=""
if [[ -f "tukuy_ebook_maker.py" ]]; then
    UNIFIED_SCRIPT="./tukuy_ebook_maker.py"
elif [[ -f "backend/scripts/tukuy_ebook_maker.py" ]]; then
    UNIFIED_SCRIPT="./backend/scripts/tukuy_ebook_maker.py"
else
    handle_error "Could not find tukuy_ebook_maker.py"
fi

echo -e "${YELLOW}Step 1: List available spiders${NC}"
python $UNIFIED_SCRIPT --list || handle_error "Failed to list spiders"

echo -e "\n${YELLOW}Step 2: Run the Python docs spider${NC}"
python $UNIFIED_SCRIPT --spider python_docs || handle_error "Failed to run the Python docs spider"

echo -e "\n${YELLOW}Step 3: Create an ebook from the Python docs${NC}"
python $UNIFIED_SCRIPT --make-ebook python_docs --output "python_test" || handle_error "Failed to create the Python docs ebook"

# Check if the ebook was created
if [[ -f "backend/outputs/python_test.epub" ]]; then
    echo -e "${GREEN}✓ Successfully created Python docs ebook at backend/outputs/python_test.epub${NC}"
else
    handle_error "Could not find the generated ebook file"
fi

echo -e "\n${YELLOW}Step 4: Optimize the ebook${NC}"
python $UNIFIED_SCRIPT --optimize || handle_error "Failed to optimize ebooks"

# Check if the optimized ebook was created
if [[ -f "backend/outputs/optimized/python_test.epub" && -f "backend/outputs/optimized/python_test.pdf" ]]; then
    echo -e "${GREEN}✓ Successfully optimized ebooks at backend/outputs/optimized/${NC}"
    echo -e "${GREEN}  - backend/outputs/optimized/python_test.epub${NC}"
    echo -e "${GREEN}  - backend/outputs/optimized/python_test.pdf${NC}"
else
    handle_error "Could not find optimized ebook files"
fi

echo -e "\n${YELLOW}Step 5: Test MDN docs with the --all option${NC}"
python $UNIFIED_SCRIPT --all || handle_error "Failed to run the --all workflow"

echo -e "\n${GREEN}=======================================================${NC}"
echo -e "${GREEN}       All tests passed successfully!                  ${NC}"
echo -e "${GREEN}=======================================================${NC}"

echo -e "\n${BLUE}Generated files:${NC}"
find backend/outputs -type f -name "*.epub" -o -name "*.pdf" | sort

echo -e "\nYou can now use the ebooks generated in backend/outputs directory."
