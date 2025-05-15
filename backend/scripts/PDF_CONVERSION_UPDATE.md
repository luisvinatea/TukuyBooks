# TukuyBooks PDF Conversion Update

This document explains the changes made to fix the PDF conversion process in the Streamlit UI.

## Issue

The PDF conversion process was hanging in the Streamlit UI because the `book_converter.sh` script was expecting interactive input from the user to select which EPUB file to convert, but when run from the Streamlit UI there was no way for the user to provide this input.

## Solution

1. Updated the `book_converter.sh` script to accept an EPUB file path via the `INPUT_EPUB` environment variable
2. Modified the script to skip the interactive prompt when this variable is provided
3. Enhanced the script to provide more detailed progress information during conversion
4. Updated the Streamlit frontend's `convert_epub_to_pdf` function with:
   - Better progress tracking
   - Error handling
   - Timeout mechanisms to prevent indefinite hanging

## Usage

### From the UI

The updated conversion process in the Streamlit UI will automatically pass the selected EPUB file to the converter script using the environment variable, no changes required in how users interact with the UI.

### From the Command Line

You can now run the conversion script in two ways:

1. **Interactive Mode** (original behavior):

   ```bash
   ./book_converter.sh
   ```

2. **Non-interactive Mode** (new feature):

   ```bash
   INPUT_EPUB=/path/to/ebook.epub ./book_converter.sh
   ```

## Testing

A test script is available to verify the non-interactive functionality:

```bash
./test_converter.sh
```
