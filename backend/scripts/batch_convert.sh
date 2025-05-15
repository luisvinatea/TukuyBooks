#!/bin/bash
# batch_convert.sh
# Script to convert multiple EPUB files to PDF in batch mode
# Usage:
#   ./batch_convert.sh [input_directory] [output_directory]

# Set default directories
INPUT_DIR=${1:-"../outputs"}
OUTPUT_DIR=${2:-"../outputs/converted"}

echo "========================================================"
echo "  TukuyBooks: Batch EPUB to PDF Converter"
echo "========================================================"
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "========================================================"

# Check if directories exist
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check for required tool
if ! command -v ebook-convert &>/dev/null; then
    echo "Calibre (ebook-convert) is not installed."
    echo "Install it with: sudo apt install calibre (or equivalent for your OS)"
    exit 1
fi

# Find all EPUB files
EPUB_FILES=("$INPUT_DIR"/*.epub)
EPUB_LIST=()
for file in "${EPUB_FILES[@]}"; do
    [ -e "$file" ] && EPUB_LIST+=("$file")
done

if [ ${#EPUB_LIST[@]} -eq 0 ]; then
    echo "No EPUB files found in $INPUT_DIR."
    exit 1
fi

echo "Found ${#EPUB_LIST[@]} EPUB files to convert."
echo "------------------------------------------------------"

# Process each EPUB file
COUNT=0
SUCCESSFUL=0
FAILED=0

for epub_file in "${EPUB_LIST[@]}"; do
    COUNT=$((COUNT + 1))
    BASENAME=$(basename "$epub_file" .epub)
    PDF_OUTPUT="$OUTPUT_DIR/$BASENAME.pdf"

    echo "[$COUNT/${#EPUB_LIST[@]}] Converting: $(basename "$epub_file")"

    # Use the book_converter.sh script with environment variable
    if INPUT_EPUB="$epub_file" ./book_converter.sh; then
        SUCCESSFUL=$((SUCCESSFUL + 1))
        echo "✅ Conversion successful: $(basename "$epub_file") -> $(basename "$PDF_OUTPUT")"
    else
        FAILED=$((FAILED + 1))
        echo "❌ Conversion failed: $(basename "$epub_file")"
    fi

    echo "------------------------------------------------------"
done

echo "========================================================"
echo "Batch conversion completed."
echo "Total files: ${#EPUB_LIST[@]}"
echo "Successful: $SUCCESSFUL"
echo "Failed: $FAILED"
echo "========================================================"
