# PythonDocs EPUB Generator

This project scrapes the Python 3 documentation from `docs.python.org/3/`, generates an EPUB, checks for broken links, optimizes the output, and converts it to PDF. It’s designed as an open-source, collaborative effort to produce a high-quality offline version of the Python docs.

## Prerequisites
- Python 3.12+
- Scrapy (`pip install scrapy`)
- Calibre (`sudo pacman -S calibre` or equivalent)
- Ghostscript (`sudo pacman -S ghostscript`)
- Sigil (for manual EPUB tweaks)

## Directory Structure
- `PythonDocs/spiders/PythonDocsSpider.py`: Scrapy spider for crawling Python docs.
- `PythonDocs/scripts/MakeEbook.py`: Generates the EPUB from scraped data.
- `PythonDocs/scripts/EpubChecker.py`: Checks EPUB for broken `href`s and logs results.
- `PythonDocs/scripts/book_optimizer.sh`: Optimizes EPUBs and PDFs.
- `PythonDocs/outputs/`: Contains `python_docs.jl`, `Python3Docs.epub`, logs, and optimized files.

## Pipeline Instructions
1. **Crawl the Docs**:
   ```bash
   cd ByteBooks/PythonDocs
   scrapy crawl python_docs

- Outputs `outputs/python_docs.jl`.

2. **Generate EPUB**:

   ```bash
   python scripts/MakeEbook.py
   ```

   - Creates `outputs/Python3Docs.epub`.
3. **Check EPUB Links**:

   ```bash
   python scripts/EpubChecker.py
   ```

   - Logs broken links to `outputs/epub_link_check_YYYYMMDD_HHMMSS.log`.
   - Review logs, fix spider or ebook script, and repeat steps 1-3 until satisfactory.
4. **Optimize Files**:

   ```bash
   bash scripts/book_optimizer.sh
   ```

   - Enter `outputs/` as the target directory.
   - Outputs optimized files to `outputs/optimized/`.
5. **Final Tweaks**:

   - Open `outputs/optimized/Python3Docs.epub` in Sigil for manual adjustments.
6. **Convert to PDF**:

   ```bash
   ebook-convert outputs/optimized/Python3Docs.epub outputs/optimized/Python3Docs.pdf
   ```
7. **Host PDFs**:

   - PDFs are uploaded to the [Releases](https://github.com/luisvinatea/ByteBooks/releases) section.

## Contributing

- **Tracking Logs**: Check `outputs/epub_link_check_*.log` for broken links. Submit issues or PRs to fix `PythonDocsSpider.py` or `MakeEbook.py`.
- **Optimizations**: Enhance `book_optimizer.sh` for better compression or format support.
- **Issues**: Report bugs or suggest features via GitHub Issues.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.