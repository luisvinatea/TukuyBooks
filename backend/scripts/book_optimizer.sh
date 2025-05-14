#!/bin/bash
# book_optimizer.sh
# Script to optimize PDF and EPUB files
# Usage: ./book_optimizer.sh [input_directory] [output_directory]

# Set default directories if not provided
INPUT_DIR=${1:-"../outputs"}
OUTPUT_DIR=${2:-"../outputs/optimized"}

# Display banner
echo "========================================================"
echo "  TukuyBooks: Book Optimizer"
echo "  Optimizes PDF and EPUB files for smaller size"
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

# Check if required tools are installed
echo "Checking for required tools..."

MISSING_TOOLS=0

# In Docker environment, we'll attempt to install missing tools
INSIDE_DOCKER=0
if [ -f /.dockerenv ]; then
    INSIDE_DOCKER=1
    echo "Running inside Docker container"
fi

if ! command -v gs &>/dev/null; then
    echo "Ghostscript (gs) is not installed"
    if [ $INSIDE_DOCKER -eq 1 ]; then
        echo "Attempting to install Ghostscript..."
        apt-get update && apt-get install -y ghostscript
        if command -v gs &>/dev/null; then
            echo "✅ Ghostscript installed successfully"
        else
            echo "❌ Failed to install Ghostscript"
            MISSING_TOOLS=1
        fi
    else
        echo "Install it with: sudo apt install ghostscript (or equivalent for your OS)"
        MISSING_TOOLS=1
    fi
fi

if ! command -v ebook-convert &>/dev/null; then
    echo "Calibre (ebook-convert) is not installed"
    if [ $INSIDE_DOCKER -eq 1 ]; then
        echo "Attempting to install Calibre..."
        apt-get update && apt-get install -y calibre
        if command -v ebook-convert &>/dev/null; then
            echo "✅ Calibre installed successfully"
        else
            echo "❌ Failed to install Calibre"
            MISSING_TOOLS=1
        fi
    else
        echo "Install it with: sudo apt install calibre (or equivalent for your OS)"
        MISSING_TOOLS=1
    fi
fi

if [ $MISSING_TOOLS -eq 1 ]; then
    exit 1
fi

echo "All required tools are installed."
echo "========================================================"

# Function to optimize PDF
optimize_pdf() {
    local input_file=$1
    local output_file=$2

    echo "Optimizing PDF: $(basename "$input_file")"

    if gs -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.7 \
        -dPDFSETTINGS=/screen \
        -dNOPAUSE \
        -dQUIET \
        -dBATCH \
        -sOutputFile="$output_file" \
        "$input_file"; then
        echo "✅ PDF optimized: $(basename "$output_file")"
        echo "   Original size: $(du -h "$input_file" | cut -f1)"
        echo "   Optimized size: $(du -h "$output_file" | cut -f1)"
        return 0
    else
        echo "❌ Error optimizing: $(basename "$input_file")"
        return 1
    fi
}

# Function to optimize EPUB
optimize_epub() {
    local input_file=$1
    local output_file=$2

    echo "Optimizing EPUB: $(basename "$input_file")"

    if ebook-convert "$input_file" "$output_file" \
        --max-toc-links 0 \
        --level1-toc "" \
        --level2-toc "" \
        --level3-toc "" \
        --extra-css "body {text-align: justify;}" \
        --no-default-epub-cover \
        --preserve-cover-aspect-ratio; then
        echo "✅ EPUB optimized: $(basename "$output_file")"
        echo "   Original size: $(du -h "$input_file" | cut -f1)"
        echo "   Optimized size: $(du -h "$output_file" | cut -f1)"
        return 0
    else
        echo "❌ Error optimizing: $(basename "$input_file")"
        return 1
    fi
}

# Function to convert EPUB to PDF
convert_to_pdf() {
    local input_file=$1
    local output_file=$2

    echo "Converting EPUB to PDF: $(basename "$input_file")"

    if ebook-convert "$input_file" "$output_file" \
        --paper-size letter \
        --pdf-page-margin-left 36 \
        --pdf-page-margin-right 36 \
        --pdf-page-margin-top 36 \
        --pdf-page-margin-bottom 36 \
        --pdf-page-numbers \
        --embed-all-fonts \
        --extra-css "body {text-align: justify;}" \
        --preserve-cover-aspect-ratio; then
        echo "✅ PDF conversion complete: $(basename "$output_file")"
        return 0
    else
        echo "❌ Error converting: $(basename "$input_file")"
        return 1
    fi
}

# Process PDF files
echo "Processing PDF files..."
PDF_COUNT=0
for file in "$INPUT_DIR"/*.pdf; do
    if [ -e "$file" ]; then
        # Skip if it's already in output directory
        if [[ "$file" == "$OUTPUT_DIR"/* ]]; then
            continue
        fi

        filename=$(basename "$file")
        output_file="$OUTPUT_DIR/$filename"

        if optimize_pdf "$file" "$output_file"; then
            ((PDF_COUNT++))
        fi
    fi
done

if [ $PDF_COUNT -eq 0 ]; then
    echo "No PDF files found for optimization."
fi
echo "========================================================"

# Process EPUB files
echo "Processing EPUB files..."
EPUB_COUNT=0
for file in "$INPUT_DIR"/*.epub; do
    if [ -e "$file" ]; then
        # Skip if it's already in output directory
        if [[ "$file" == "$OUTPUT_DIR"/* ]]; then
            continue
        fi

        filename=$(basename "$file")
        output_file="$OUTPUT_DIR/$filename"

        if optimize_epub "$file" "$output_file"; then
            # Also generate PDF from EPUB
            pdf_filename="${filename%.epub}.pdf"
            pdf_output="$OUTPUT_DIR/$pdf_filename"

            if convert_to_pdf "$output_file" "$pdf_output"; then
                echo "   Also created PDF: $pdf_filename"
            fi

            ((EPUB_COUNT++))
        fi
    fi
done

if [ $EPUB_COUNT -eq 0 ]; then
    echo "No EPUB files found for optimization."
fi
echo "========================================================"

# Summary
echo "Summary:"
echo "Processed $PDF_COUNT PDF files"
echo "Processed $EPUB_COUNT EPUB files"
echo "Optimized files are in: $OUTPUT_DIR"
echo "========================================================"
