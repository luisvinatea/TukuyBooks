#!/bin/bash
# Script to run the TukuyBooks Streamlit frontend

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting TukuyBooks Streamlit frontend...${NC}"

# Check if we need to install requirements first
if [ "$1" == "--install" ] || [ "$1" == "-i" ]; then
    echo -e "${BLUE}Installing required packages...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}Packages installed successfully!${NC}"
fi

# Start the Streamlit app
echo -e "${BLUE}Launching Streamlit...${NC}"
streamlit run app.py

# Exit code
exit $?
