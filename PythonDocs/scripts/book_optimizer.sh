#!/bin/bash

# Prompt user for directory path
echo -n "Enter the directory path containing PDFs and EPUBs to optimize: "
read -r TARGET_DIR

# Check if a path was entered
if [ -z "$TARGET_DIR" ]; then
    echo "Error: No directory path provided"
    exit 1
fi

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

# Create optimized subdirectory if it doesn't exist
OPTIMIZED_DIR="$TARGET_DIR/optimized"
mkdir -p "$OPTIMIZED_DIR"

# Check if required tools are installed
if ! command -v gs &> /dev/null; then
    echo "Error: Ghostscript (gs) is not installed"
    echo "Install it with: sudo pacman -S ghostscript"
    exit 1
fi

if ! command -v ebook-convert &> /dev/null; then
    echo "Error: Calibre (ebook-convert) is not installed"
    echo "Install it with: sudo pacman -S calibre"
    exit 1
fi

# Counter for processed files
count=0

# Process PDF files
for file in "$TARGET_DIR"/*.pdf; do
    if [ -e "$file" ]; then
        filename=$(basename "$file")

        # Skip if it's already in optimized directory
        if [[ "$file" == "$OPTIMIZED_DIR"* ]]; then
            continue
        fi

        echo "Processing PDF: $filename"

        gs -sDEVICE=pdfwrite \
           -dCompatibilityLevel=1.7 \
           -dPDFSETTINGS=/screen \
           -dNOPAUSE \
           -dQUIET \
           -dBATCH \
           -sOutputFile="$OPTIMIZED_DIR/$filename" \
           "$file"

        if [ $? -eq 0 ]; then
            rm "$file"
            echo "Optimized and deleted original: $filename"
            ((count++))
        else
            echo "Error optimizing: $filename"
        fi
    fi
done

# Process EPUB files
for file in "$TARGET_DIR"/*.epub; do
    if [ -e "$file" ]; then
        filename=$(basename "$file")

        # Skip if it's already in optimized directory
        if [[ "$file" == "$OPTIMIZED_DIR"* ]]; then
            continue
        fi

        echo "Processing EPUB: $filename"

        ebook-convert "$file" "$OPTIMIZED_DIR/$filename" \
            --max-toc-links 0 \
            --level1-toc "" \
            --level2-toc "" \
            --level3-toc ""

        if [ $? -eq 0 ]; then
            rm "$file"
            echo "Optimized and deleted original: $filename"
            ((count++))
        else
            echo "Error optimizing: $filename"
        fi
    fi
done

# Check if any files were processed
if [ $count -eq 0 ]; then
    echo "No PDF or EPUB files found in $TARGET_DIR"
else
    echo "Processed $count files (PDFs and/or EPUBs)"
    echo "Optimized files are in: $OPTIMIZED_DIR"
fi
