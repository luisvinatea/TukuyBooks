# TukuyBooks Unified Ebook Maker Guide

The `tukuy_ebook_maker.py` script provides a complete workflow for creating ebooks from online documentation sources. It simplifies the process by integrating three main steps:

1. **Running the spider** to scrape documentation
2. **Creating the ebook** from the scraped data
3. **Optimizing the output** to generate smaller, more efficient files

## Quick Start

```bash
# List available spiders
python tukuy_ebook_maker.py --list

# Run the complete workflow for all available spiders
python tukuy_ebook_maker.py --all

# Run the complete workflow for a specific spider
python tukuy_ebook_maker.py --spider python_docs --make-ebook --optimize
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--list` | List all available spiders |
| `--spider SPIDER_ID` | Run the specified spider to scrape documentation |
| `--make-ebook SPIDER_ID` | Create an ebook from the specified spider's output |
| `--optimize` | Optimize the generated ebooks (reduce size, improve compatibility) |
| `--all` | Run the complete workflow for all available spiders |
| `--output OUTPUT` | Specify a custom output filename (without extension) |
| `--help` | Show help message and exit |

## Progress Bars

The unified ebook maker features interactive progress bars for all operations, providing real-time visual feedback on:

- Spider execution progress with animated indicators
- Detailed ebook creation steps showing each processing stage
- Optimization process with step-by-step tracking

This makes it easier to track long-running operations and understand what's happening at each stage of the workflow. The progress bars show both percentage completion and elapsed time, making it clear how long each operation is taking.

Progress bars are enabled by default when the `tqdm` package is installed. If it's not installed, the script will fall back to standard logging output.

### Progress Bar Features

- **Animated indicators** that provide visual feedback even when exact progress can't be determined
- **Detailed step labels** that update to show the current operation
- **Time tracking** to show elapsed time for each operation
- **Smooth transitions** between stages of long-running processes

## Examples

### List Available Spiders

```bash
python tukuy_ebook_maker.py --list
```

This will show all available documentation sources that can be scraped.

### Run a Specific Spider

```bash
python tukuy_ebook_maker.py --spider python_docs
```

This will run the Python documentation spider to scrape the content.

### Create an Ebook from Scraped Data

```bash
python tukuy_ebook_maker.py --make-ebook mdn_docs
```

This will create an EPUB file from the previously scraped MDN JavaScript documentation.

### Optimize an Ebook

```bash
python tukuy_ebook_maker.py --optimize
```

This will optimize all EPUB files in the outputs directory, generating both optimized EPUB and PDF versions.

### Complete Workflow for a Specific Spider

```bash
python tukuy_ebook_maker.py --spider python_docs --make-ebook python_docs --optimize
```

This will run the complete workflow for the Python documentation: scrape, create ebook, and optimize.

### Custom Output Filename

```bash
python tukuy_ebook_maker.py --make-ebook python_docs --output "Python3.12_Docs"
```

This will create an ebook with the custom filename "Python3.12_Docs.epub".

## Output Files

The script generates the following files in the `backend/outputs` directory:

- `spider_id.jl`: The scraped data in JSON Lines format
- `spider_id.epub`: The generated EPUB file
- Optimized versions in `backend/outputs/optimized/`:
  - `spider_id.epub`: Optimized EPUB file
  - `spider_id.pdf`: PDF version of the documentation

## Supported Documentation Sources

Currently, the following documentation sources are supported:

1. **Python Documentation** (`python_docs`)
2. **MDN JavaScript Documentation** (`mdn_docs`)

## Requirements

- Python 3.8+
- BeautifulSoup4
- EbookLib
- Scrapy (for spider functionality)
- Calibre (for ebook conversion and optimization)
- Ghostscript (for PDF optimization)
- tqdm (for progress bars in CLI - recommended but optional)

## Troubleshooting

### Script Can't Find Config File

Ensure you're running the script from the project root directory:

```bash
cd /path/to/TukuyBooks
python tukuy_ebook_maker.py --list
```

### Spider Fails to Run

Check that Scrapy is properly installed:

```bash
pip install scrapy
```

### Optimizations Fail

Ensure you have Calibre and Ghostscript installed:

```bash
# Ubuntu/Debian
sudo apt-get install calibre ghostscript

# Arch Linux
sudo pacman -S calibre ghostscript

# macOS
brew install calibre ghostscript
```

### Large or Unoptimized Files

If the optimization step fails but the EPUB is created, try running the optimizer separately:

```bash
bash backend/scripts/book_optimizer.sh backend/outputs
```
