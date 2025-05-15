#!/bin/bash
# book_converter.sh
# Script to convert an EPUB file to PDF
# Usage:
#   Option 1: ./book_converter.sh [input_directory] [output_directory]
#   Option 2: INPUT_EPUB=/path/to/ebook.epub ./book_converter.sh

INPUT_DIR=${1:-"../outputs"}
OUTPUT_DIR=${2:-"../outputs/converted"}

# Set DOCKER_CONTAINER=1 in Docker entrypoint to trigger non-interactive mode automatically
DOCKER_CONTAINER=${DOCKER_CONTAINER:-0}

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

# Function to process a single EPUB file
process_file() {
    local epub_file="$1"
    local base_name
    local pdf_output
    
    base_name=$(basename "$epub_file" .epub)
    pdf_output="$OUTPUT_DIR/$base_name.pdf"

    echo "Starting conversion..."
    echo "Converting EPUB to PDF: '$epub_file' to '$pdf_output'..."

    # Run the conversion with verbose output to show progress
    if ebook-convert "$epub_file" "$pdf_output" \
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
        echo "✅ PDF conversion complete: $(basename "$pdf_output")"
        echo "   Output file: $pdf_output"
        return 0
    else
        echo "❌ Error converting: $(basename "$epub_file")"
        return 1
    fi
}

# Get list of EPUB files
EPUB_FILES=("$INPUT_DIR"/*.epub)
EPUB_LIST=()
for file in "${EPUB_FILES[@]}"; do
    [ -e "$file" ] && EPUB_LIST+=("$file")
done

if [ ${#EPUB_LIST[@]} -eq 0 ]; then
    echo "No EPUB files found in $INPUT_DIR."
    exit 1
fi

# Check if INPUT_EPUB environment variable is set for direct file mode
if [ -n "$INPUT_EPUB" ]; then
    if [ ! -f "$INPUT_EPUB" ]; then
        echo "Error: Input EPUB file '$INPUT_EPUB' does not exist"
        exit 1
    fi
    echo "Starting conversion of specified file: $(basename "$INPUT_EPUB")"
    process_file "$INPUT_EPUB"
    exit $?
fi

# Check if we're running in a terminal or in Docker
if [ -t 0 ] && [ "$DOCKER_CONTAINER" != "1" ]; then
    # Interactive mode - show menu
    echo "Available EPUB files:"
    for i in "${!EPUB_LIST[@]}"; do
        echo "  [$((i + 1))] $(basename "${EPUB_LIST[$i]}")"
    done

    # Prompt user to select a file
    while true; do
        read -rp "Enter the number of the EPUB to convert (or 'a' for all): " selection
        if [ "$selection" = "a" ] || [ "$selection" = "A" ]; then
            echo "Converting all EPUB files..."
            for epub in "${EPUB_LIST[@]}"; do
                process_file "$epub"
            done
            break
        elif [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#EPUB_LIST[@]}" ]; then
            process_file "${EPUB_LIST[$((selection - 1))]}"
            break
        else
            echo "Invalid selection. Please enter a number between 1 and ${#EPUB_LIST[@]}, or 'a' for all."
        fi
    done
else
    # Non-interactive mode (e.g., Docker) - process all files
    echo "Running in non-interactive mode. Converting all EPUB files:"
    for epub in "${EPUB_LIST[@]}"; do
        echo "  - $(basename "$epub")"
        process_file "$epub"
    done
fi

echo "========================================================"
echo "Done."
echo "========================================================"
