# TukuyBooks: Transforming Open-Source Internet into Free Access Knowledge

Welcome to **ByteBooks**, an open-source initiative to scrape, process, and convert freely available online documentation into high-quality, offline-accessible EPUBs and PDFs. Our mission is to preserve and democratize knowledge from the open-source internet, making it available to anyone, anywhere, without barriers.

## Vision

ByteBooks aims to:

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

## Directory Structure

- `ByteBooks/`: Root directory.
  - `PythonDocs/`: Subdirectory for the Python documentation pipeline.
    - `spiders/`: Contains `PythonDocsSpider.py`.
    - `scripts/`: Tools like `MakeEbook.py`, `EpubChecker.py`, `BookOptimizer.sh`.
    - `outputs/`: Generated files (e.g., `python_docs.jl`, `Python3Docs.epub`).
  - `scrapy.cfg`: Scrapy configuration for all pipelines.
  - *(Future subdirectories for other websites will follow this pattern.)*

## General Pipeline Workflow

Each pipeline follows these steps:

1. **Crawl**: Use a Scrapy spider to scrape a target website.
2. **Generate EPUB**: Convert scraped data into an EPUB file.
3. **Check Links**: Validate EPUB for broken `href`s and log issues.
4. **Optimize**: Reduce file size and improve formatting.
5. **Tweak**: Manually adjust the EPUB in Sigil if needed.
6. **Convert**: Generate a PDF from the optimized EPUB.
7. **Release**: Host the PDF in [GitHub Releases](https://github.com/luisvinatea/ByteBooks/releases).

See individual pipeline READMEs (e.g., [PythonDocs](PythonDocs/README.md)) for specific instructions.

## Contributing

We welcome contributions to expand ByteBooks! Here’s how you can help:

- **New Pipelines**: Propose or build a spider for a new open-source website (e.g., via Issues).
- **Fix Broken Links**: Analyze logs (e.g., `epub_link_check_*.log`) and submit PRs.
- **Optimize Tools**: Enhance scripts like `BookOptimizer.sh` or `MakeEbook.py`.
- **Report Bugs**: Open an Issue with details.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

ByteBooks is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Get Involved

- Star this repo to show support!
- Fork and submit Pull Requests.
- Join the discussion in [Issues](https://github.com/luisvinatea/ByteBooks/issues).
