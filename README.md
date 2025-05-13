# TukuyBooks: Transforming Open-Source Internet into Free Access Knowledge

Welcome to **TukuyBooks**, an open-source initiative to scrape, process, and convert freely available online documentation into high-quality, offline-accessible EPUBs and PDFs. Our mission is to preserve and democratize knowledge from the open-source internet, making it available to anyone, anywhere, without barriers.

## Online Interface

The TukuyBooks web interface allows you to:

- View available documentation sources
- Start scraping processes
- Generate EPUB/PDF files from scraped content
- Download pre-generated ebooks

**Visit the online interface:** [https://luisvinatea.github.io/TukuyBooks/](https://luisvinatea.github.io/TukuyBooks/)

## Vision

TukuyBooks aims to:

- Capture valuable documentation from open-source websites.
- Transform it into portable, optimized formats (EPUB, PDF).
- Distribute these resources freely via GitHub Releases.
- Foster a collaborative community to maintain and expand this knowledge library.

Each website we target gets its own dedicated spider pipeline within this repository, ensuring modularity and scalability.

## Current Pipelines

Below are the active spider pipelines transforming specific websites into free knowledge assets:

- **[PythonDocs](PythonDocs/)**: Scrapes Python 3 documentation from `docs.python.org/3/`.
  - Status: Active
  - Outputs: `Python3Docs.epub`, `Python3Docs.pdf`
  - See [PythonDocs README](PythonDocs/README.md) for details.

*More pipelines coming soon! Suggest new websites via [Issues](#contributing).*

## General Prerequisites

To contribute or run any pipeline, you’ll need:

- Python 3.12+
- Scrapy (`pip install scrapy`)
- Calibre (`sudo pacman -S calibre` or equivalent)
- Ghostscript (`sudo pacman -S ghostscript`)
- Sigil (optional, for EPUB tweaks)

## Project Structure

The project is organized into the structure:

```text
TukuyBooks/
│
├── backend/             # Backend code
│   ├── api/             # Flask API for the frontend
│   ├── outputs/         # Generated files (JL, EPUB, PDF)
│   ├── scripts/         # Utility scripts for ebook generation
│   ├── spiders/         # Scrapy spiders for different sites
│   └── utils/           # Common utility functions
│
├── frontend/            # Frontend code (deploys to GitHub Pages)
│   ├── assets/          # Images and other assets
│   ├── components/      # Reusable UI components
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
│
├── PythonDocs/          # Legacy structure (being migrated)
├── .github/workflows/   # GitHub Actions workflows
└── CONTRIBUTING.md, LICENSE, README.md, etc.
```

## How to Use

### Option 1: Web Interface (Easiest)

Visit [https://luisvinatea.github.io/TukuyBooks/](https://luisvinatea.github.io/TukuyBooks/) to:

1. Select a documentation source
2. Generate EPUB/PDF files
3. Download the results

### Option 2: Local Setup

To run locally:

1. Clone the repository:

   ```bash
   git clone https://github.com/luisvinatea/TukuyBooks.git
   cd TukuyBooks
   ```

2. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run a spider:

   ```bash
   cd backend
   scrapy crawl python_docs -o outputs/python_docs.jl
   ```

4. Generate an ebook:

   ```bash
   python -m backend.scripts.make_ebook
   ```

5. Run the API (optional):

   ```bash
   python backend/api/app.py
   ```

## Workflow

Each pipeline follows these steps:

1. **Crawl**: Use a Scrapy spider to scrape a target website.
2. **Generate EPUB**: Convert scraped data into an EPUB file.
3. **Check Links**: Validate EPUB for broken links and log issues.
4. **Optimize**: Reduce file size and improve formatting.
5. **Convert**: Generate a PDF from the optimized EPUB.
6. **Download**: Access the files through the web interface.

## Contributing

We welcome contributions to expand ByteBooks! Here’s how you can help:

- **New Pipelines**: Propose or build a spider for a new open-source website (e.g., via Issues).
- **Fix Broken Links**: Analyze logs (e.g., `epub_link_check_*.log`) and submit PRs.
- **Optimize Tools**: Enhance scripts like `BookOptimizer.sh` or `MakeEbook.py`.
- **Report Bugs**: Open an Issue with details.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

TukuyBooks is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Get Involved

- Star this repo to show support!
- Fork and submit Pull Requests.
- Join the discussion in [Issues](https://github.com/luisvinatea/ByteBooks/issues).
