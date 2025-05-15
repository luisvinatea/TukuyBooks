#!/bin/bash
# book_converter.sh
# Script to convert an EPUB file to PDF
# Usage:
#   Option 1: ./book_converter.sh [input_directory] [output_directory]
#   Option 2: INPUT_EPUB=/path/to/ebook.epub ./book_converter.sh

INPUT_DIR=${1:-"../outputs"}
OUTPUT_DIR=${2:-"../outputs/converted"}

echo "========================================================"
echo "  TukuyBooks: Book Converter"
echo "  Converts an EPUB file to PDF"
echo "========================================================"
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "========================================================"

# Check if directories exist
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Check for required tool
if ! command -v ebook-convert &>/dev/null; then
    echo "Calibre (ebook-convert) is not installed."
    echo "Install it with: sudo apt install calibre (or equivalent for your OS)"
    exit 1
fi

# Check if INPUT_EPUB environment variable is set
if [ -n "$INPUT_EPUB" ]; then
    # Direct file mode - use the provided file path
    if [ ! -f "$INPUT_EPUB" ]; then
        echo "Error: Input EPUB file '$INPUT_EPUB' does not exist"
        exit 1
    fi
    echo "Starting conversion of specified file: $(basename "$INPUT_EPUB")"
    EPUB_FILE="$INPUT_EPUB"
else
    # Interactive mode - list files and ask user to select
    # List available EPUB files
    EPUB_FILES=("$INPUT_DIR"/*.epub)
    EPUB_LIST=()
    for file in "${EPUB_FILES[@]}"; do
        [ -e "$file" ] && EPUB_LIST+=("$file")
    done

    if [ ${#EPUB_LIST[@]} -eq 0 ]; then
        echo "No EPUB files found in $INPUT_DIR."
        exit 1
    fi

    echo "Available EPUB files:"
    for i in "${!EPUB_LIST[@]}"; do
        echo "  [$((i + 1))] $(basename "${EPUB_LIST[$i]}")"
    done

    # Prompt user to select a file
    while true; do
        read -rp "Enter the number of the EPUB to convert: " selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#EPUB_LIST[@]}" ]; then
            EPUB_FILE="${EPUB_LIST[$((selection - 1))]}"
            break
        else
            echo "Invalid selection. Please enter a number between 1 and ${#EPUB_LIST[@]}."
        fi
    done
fi

BASENAME=$(basename "$EPUB_FILE" .epub)
PDF_OUTPUT="$OUTPUT_DIR/$BASENAME.pdf"

echo "Starting conversion..."
echo "Converting EPUB to PDF: '$EPUB_FILE' to '$PDF_OUTPUT'..."

# Run the conversion with verbose output to show progress
if ebook-convert "$EPUB_FILE" "$PDF_OUTPUT" \
    --verbose \
    --paper-size letter \
    --pdf-page-margin-left 36 \
    --pdf-page-margin-right 36 \
    --pdf-page-margin-top 36 \
    --pdf-page-margin-bottom 36 \
    --pdf-page-numbers \
    --embed-all-fonts \
    --extra-css "body {text-align: justify;}" \
    --preserve-cover-aspect-ratio; then
    echo "Conversion completed successfully"
    echo "✅ PDF conversion complete: $(basename "$PDF_OUTPUT")"
    echo "   Output file: $PDF_OUTPUT"
else
    echo "❌ Error converting: $(basename "$EPUB_FILE")"
    exit 1
fi

echo "========================================================"
echo "Done."
echo "========================================================"
