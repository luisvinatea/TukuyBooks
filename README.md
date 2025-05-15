# TukuyBooks: Transforming Open-Source Internet into Free Access Knowledge

Welcome to **TukuyBooks**, an open-source initiative to scrape, process, and convert freely available online documentation into high-quality, offline-accessible EPUBs and PDFs. Our mission is to preserve and democratize knowledge from the open-source internet, making it available to anyone, anywhere, without barriers.

## Usage Options

### Streamlit Web Interface

TukuyBooks now features a user-friendly web interface built with Streamlit:

```bash
# Clone the repository
git clone https://github.com/luisvinatea/TukuyBooks.git
cd TukuyBooks

# Set up a Python virtual environment
python -m venv .tukuybooks
source .tukuybooks/bin/activate

# Install frontend requirements and launch
cd frontend
pip install -r requirements.txt
./run_streamlit.sh
```

Or use the convenience script with automatic dependency installation:

```bash
./frontend/run_streamlit.sh --install
```

### Command Line Interface

You can also run TukuyBooks spiders and ebook generators directly using the provided scripts:

```bash
# Clone the repository
git clone https://github.com/luisvinatea/TukuyBooks.git
cd TukuyBooks

# Set up a Python virtual environment
python -m venv .tukuybooks
source .tukuybooks/bin/activate
pip install -r backend/requirements.txt

# Use the unified ebook maker script
python tukuy_ebook_maker.py --list                # List available spiders
python tukuy_ebook_maker.py --spider python_docs  # Run a specific spider
python tukuy_ebook_maker.py --make-ebook mdn_docs # Create an ebook from scraped data
python tukuy_ebook_maker.py --convert            # Convert generated ebooks
python tukuy_ebook_maker.py --all                # Run the complete workflow for all spiders

# Or use the individual scripts
python backend/scripts/spider_runner.py --list
python backend/scripts/spider_runner.py python_docs
python backend/scripts/make_ebook.py python_docs

# Build all available ebooks at once
./scripts/build_all_ebooks.sh

# Check the outputs directory for the generated files
ls backend/outputs
```

## Docker Usage

TukuyBooks now provides Docker containers for easy local deployment of spider pipelines. Run our spiders without worrying about dependencies or complex setup:

```bash
# Build the Docker image
./run_docker.sh

# Run the Python documentation spider
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest crawl python_docs

# Run the MDN JavaScript documentation spider
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest crawl mdn_docs

# Generate an ebook from the scraped data
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest make-ebook python_docs
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest make-ebook mdn_docs

# Run the full pipeline (crawl -> make-ebook -> optimize)
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest all python_docs
docker run -v $(pwd)/backend/outputs:/app/backend/outputs tukuybooks:latest all mdn_docs
```

The generated ebooks will be available in your local `./backend/outputs` directory.

## Features

- **Web Scraping**: Capture documentation from open-source websites with custom spiders
- **Ebook Generation**: Transform web content into EPUB and PDF formats with proper formatting
- **Enhanced PDF Conversion**: Convert EPUB files to PDF with configurable styling and formatting options
- **Real-time Status Updates**: Monitor scraping progress with real-time notifications
- **Offline Reading**: Download ebooks for offline reading on e-readers or other devices

## EPUB to PDF Conversion

TukuyBooks provides enhanced PDF conversion capabilities:

```bash
# Convert EPUB to PDF using the interactive interface
./backend/scripts/book_converter.sh

# Non-interactive conversion (useful for automation)
INPUT_EPUB=/path/to/file.epub ./backend/scripts/book_converter.sh

# Parameters can be customized within the script for:
# - Paper size
# - Margins
# - Page numbers
# - Font embedding
# - Text justification
```

In the Streamlit UI, PDF conversion can be performed from the "Convert to PDF" tab, with progress monitoring and automatic error detection.

## Vision

TukuyBooks aims to:

- Capture valuable documentation from open-source websites.
- Transform it into portable, optimized formats (EPUB, PDF).
- Distribute these resources freely via GitHub Releases.
- Foster a collaborative community to maintain and expand this knowledge library.

Each website we target gets its own dedicated spider pipeline within this repository, ensuring modularity and scalability.

## Current Pipelines

Below are the active spider pipelines transforming specific websites into free knowledge assets:

- **PythonDocs**: Scrapes Python 3 documentation from `docs.python.org/3/`.
  - Status: Active
  - Outputs: `Python3Docs.epub`, `Python3Docs.pdf`

- **MDNDocs**: Scrapes MDN JavaScript documentation from `developer.mozilla.org`.
  - Status: Active
  - Outputs: `MDNJavaScriptDocs.epub`, `MDNJavaScriptDocs.pdf`

- **ReactDocs**: Scrapes React documentation from `reactjs.org`.
  - Status: Active
  - Outputs: `ReactDocs.epub`, `ReactDocs.pdf`

*More pipelines coming soon! Suggest new websites via [Issues](https://github.com/luisvinatea/TukuyBooks/issues).*

## General Prerequisites

To contribute or run any pipeline, you’ll need:

- Python 3.12+
- Scrapy (`pip install scrapy`)
- Calibre (`sudo pacman -S calibre` or equivalent)
- Ghostscript (`sudo pacman -S ghostscript`)
- Sigil (optional, for EPUB tweaks)

## Project Structure

The project is organized into the following structure:

```plaintext
TukuyBooks/
├── backend/              # Backend API and server
│   ├── api/             # Flask API for the web interface
│   ├── outputs/         # Generated ebooks and intermediate files
│   ├── scripts/         # Utilities for ebook generation
│   ├── spiders/         # Scrapy spiders for different documentation sites
│   └── utils/           # Shared utility functions
├── frontend/            # Web interface
│   ├── css/             # Stylesheets
│   ├── js/              # Client-side JavaScript
│   └── index.html       # Main HTML file
└── scrapy.cfg           # Scrapy configuration file
```
