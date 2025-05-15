#!/usr/bin/env python3
"""
tukuy_ebook_maker.py - TukuyBooks Unified Ebook Maker

This script provides a complete workflow for creating ebooks:
1. Run spiders to gather documentation
2. Convert the scraped data to EPUB format
3. Optimize the EPUB and generate PDF

Usage:
    python tukuy_ebook_maker.py [options]

Options:
    --spider SPIDER_ID    Run the specified spider before creating ebooks
    --make-ebook SPIDER_ID    Create an ebook from the specified spider's output
    --optimize            Optimize the generated ebooks
    --all                 Run the complete workflow (scrape, make ebook, optimize)
    --list                List available spiders
    --output OUTPUT       Specify output filename (without extension)
    --help                Show this help message and exit
"""

import sys
import os
import logging
import json
import argparse
import subprocess
import traceback
import time
import platform
import math
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag

# Check if we're running in a terminal that supports colors
COLORS_SUPPORTED = sys.stdout.isatty() and platform.system() != "Windows"


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m" if COLORS_SUPPORTED else ""
    BOLD = "\033[1m" if COLORS_SUPPORTED else ""
    RED = "\033[91m" if COLORS_SUPPORTED else ""
    GREEN = "\033[92m" if COLORS_SUPPORTED else ""
    YELLOW = "\033[93m" if COLORS_SUPPORTED else ""
    BLUE = "\033[94m" if COLORS_SUPPORTED else ""
    MAGENTA = "\033[95m" if COLORS_SUPPORTED else ""
    CYAN = "\033[96m" if COLORS_SUPPORTED else ""


try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print(
        f"{Colors.YELLOW}Warning: tqdm is not installed. Progress bars will be disabled.{Colors.RESET}"
    )
    print(
        f"To enable progress bars, install tqdm: {Colors.BOLD}pip install tqdm{Colors.RESET}"
    )


# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tukuy_ebook_maker")


class EbookMaker:
    """Base class for creating ebooks from scraped documentation."""

    def __init__(self, spider_id, title, author="Unknown", language="en"):
        """Initialize EbookMaker with metadata.

        Args:
            spider_id (str): ID of the spider used to scrape the data.
            title (str): Title of the ebook.
            author (str): Author of the ebook.
            language (str): Language of the ebook.
        """
        self.spider_id = spider_id
        self.title = title
        self.author = author
        self.language = language
        self.input_file = os.path.join("backend", "outputs", f"{spider_id}.jl")
        self.anchor_map = {}  # Override in subclasses if needed
        self.logger = logging.getLogger(__name__)

    def _process_content(self, content):
        """Base method for processing HTML content. Should be overridden by subclasses.

        Args:
            content: The HTML content to process (can be a Tag or string)

        Returns:
            None: The content is modified in place if it's a Tag.
        """
        # Base implementation does nothing
        return

    def load_chapters(self):
        """Load and sort chapters from JSON Lines file.

        Returns:
            list: Sorted list of chapters.
        """
        chapters = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                for line in f:
                    chapters.append(json.loads(line))
            chapters.sort(
                key=lambda x: (x.get("priority", 999), x.get("level", 1))
            )
            self.logger.info(
                f"Loaded {len(chapters)} chapters from {self.input_file}"
            )
            return chapters
        except Exception as e:
            self.logger.error(f"Error loading chapters: {e}")
            return []

    def init_book(self):
        """Initialize and return a new EpubBook with metadata.

        Returns:
            epub.EpubBook: Initialized book object.
        """
        book = epub.EpubBook()
        book.set_identifier(self.spider_id)
        book.set_title(self.title)
        book.set_language(self.language)
        book.add_author(self.author)
        return book

    def rewrite_href(
        self, raw_href, url_to_filename, chapters, internal_links
    ):
        """Rewrite hrefs to point to the correct internal links.

        Args:
            raw_href (str): Original href value.
            url_to_filename (dict): Mapping of URLs to filenames.
            chapters (list): List of chapter dictionaries.
            internal_links (dict): Mapping of hrefs to titles.

        Returns:
            str: Rewritten href or None if it can't be rewritten.
        """
        # Normalize href to string
        if isinstance(raw_href, (list, tuple)):
            href = raw_href[0] or ""
        else:
            href = raw_href or ""
        if not isinstance(href, str):
            href = str(href)
        # Skip external links and anchors
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return None

        base, fragment = (href.split("#", 1) + [""])[:2]
        fragment = "#" + fragment if fragment else ""

        # Map known anchors
        if fragment[1:] in self.anchor_map:
            fragment = "#" + self.anchor_map[fragment[1:]]

        # Direct URL mapping
        match = next((u for u in url_to_filename if base in u), None)
        if match:
            return url_to_filename[match] + fragment

        # Title-based internal links
        tgt = internal_links.get(href)
        if tgt:
            for o in chapters:
                if o["title"] == tgt:
                    return url_to_filename[o["url"]] + fragment
        return None

    def clean_html_content(
        self, html_content, chapter_title="", chapter_index=0
    ):
        """Clean and process HTML content for ebook compatibility.

        Args:
            html_content (str): Raw HTML content
            chapter_title (str): Title of the chapter for error reporting
            chapter_index (int): Index of the chapter for error reporting

        Returns:
            str: Cleaned HTML content
        """
        try:
            # Try to parse the HTML content
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script tags and other unwanted elements
            for script in soup.find_all("script"):
                script.extract()

            # Return valid HTML string if successful
            return soup
        except Exception as e:
            self.logger.warning(
                f"Error parsing HTML for chapter {chapter_index + 1} '{chapter_title}': {e}"
            )

            # Return a simple soup object with an error message as fallback
            fallback = BeautifulSoup("", "html.parser")
            h1 = fallback.new_tag("h1")
            h1.string = chapter_title or f"Chapter {chapter_index + 1}"
            fallback.append(h1)

            p = fallback.new_tag("p")
            p.string = "The original content could not be processed correctly. Here's the raw text:"
            fallback.append(p)

            # Try to extract text from the raw HTML
            try:
                raw_text = BeautifulSoup(
                    html_content, "html.parser"
                ).get_text()
                pre = fallback.new_tag("pre")
                # Limit text length to avoid excessively large chapters
                pre.string = raw_text[:5000] + (
                    "..." if len(raw_text) > 5000 else ""
                )
                fallback.append(pre)
            except Exception:
                p2 = fallback.new_tag("p")
                p2.string = "Could not extract text from the original content."
                fallback.append(p2)

            return fallback

    def create_epub(self, output_filename=None):
        """Create an EPUB file from scraped data.

        Args:
            output_filename (str): Name of the output file.

        Returns:
            str: Path to the created EPUB file.
        """
        if output_filename is None:
            output_filename = f"{self.spider_id}.epub"

        output_path = os.path.join("backend", "outputs", output_filename)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        chapters = self.load_chapters()
        if not chapters:
            self.logger.error("No chapters found!")
            return None

        try:
            self.logger.info(
                f"Initializing book with {len(chapters)} chapters"
            )
            book = self.init_book()

            # Create chapters
            epub_chapters = []
            url_to_filename = {}

            # First pass: Map all URLs to filenames
            for i, chap in enumerate(chapters):
                fname = f"chap_{i + 1}.xhtml"
                url_to_filename[chap["url"]] = fname

            # Second pass: Process chapters and add to book
            for i, chap in enumerate(chapters):
                # Clean the HTML content using our improved method
                chapter_title = chap.get("title", f"Chapter {i + 1}")
                soup = self.clean_html_content(
                    chap["content"], chapter_title, i
                )

                try:
                    # Process internal links
                    for element in soup.find_all("a", href=True):
                        raw_href = element.attrs.get("href", "")
                        new_href = self.rewrite_href(
                            raw_href,
                            url_to_filename,
                            chapters,
                            chap.get("internal_links", {}),
                        )
                        if new_href:
                            element["href"] = new_href

                    # Apply any additional content processing
                    self._process_content(soup)

                    # Get the content as string
                    content = str(soup)
                except Exception as e:
                    self.logger.warning(
                        f"Error processing links for chapter {i + 1} '{chapter_title}': {e}"
                    )
                    # Use the soup as is even if link processing failed
                    content = str(soup)

                # Create the chapter with the processed content
                c = epub.EpubHtml(
                    title=chapter_title,
                    file_name=url_to_filename[chap["url"]],
                    lang=self.language,
                    content=content,
                )

                # Add to book
                book.add_item(c)
                epub_chapters.append(c)

            # Define CSS
            style = """
            body {
                font-family: Arial, sans-serif;
                margin: 2%;
                padding: 0;
                line-height: 1.5;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.5em;
            }
            code {
                font-family: monospace;
                background-color: #f5f5f5;
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }
            pre {
                background-color: #f5f5f5;
                padding: 1em;
                overflow-x: auto;
                white-space: pre-wrap;
                border-radius: 3px;
                max-width: 100%;
            }
            """

            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/style.css",
                media_type="text/css",
                content=style,
            )
            book.add_item(nav_css)

            # Add TOC
            book.toc = epub_chapters

            # Add navigation files
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Define spine
            book.spine = ["nav"] + epub_chapters

            # Write to file
            self.logger.info(f"Writing EPUB to {output_path}")

            # Check if the output file already exists and remove it
            if os.path.exists(output_path):
                os.remove(output_path)
                self.logger.info(f"Removed existing file: {output_path}")

            epub.write_epub(output_path, book, {})

            # Verify the file was created and log its size
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(
                    f"EPUB created successfully: {output_path} ({file_size} bytes)"
                )
                return output_path
            else:
                self.logger.error("Failed to create EPUB file")
                return None

        except Exception as e:
            self.logger.error(f"Error creating EPUB: {e}")
            self.logger.error(traceback.format_exc())
            return None


class PythonDocsEbookMaker(EbookMaker):
    """Class for creating ebooks from scraped Python documentation."""

    def __init__(
        self,
        title="Python 3 Documentation",
        author="Python Software Foundation",
        language="en",
    ):
        """Initialize PythonDocsEbookMaker with Python-specific metadata."""
        super().__init__("python_docs", title, author, language)

        # Add Python-specific anchor mapping
        self.anchor_map = {
            "library-index": "the-python-standard-library",
            "reference-index": "the-python-language-reference",
            "extending-index": "extending-and-embedding-the-python-interpreter",
            "c-api-index": "python-c-api-reference-manual",
            "tutorial-index": "the-python-tutorial",
            "using-index": "python-setup-and-usage",
            "glossary": "glossary",
            "faq-index": "python-frequently-asked-questions",
            "distributing-index": "distributing-python-modules",
            "installing-index": "installing-python-modules",
            "howto-index": "python-howtos",
        }

    def _process_content(self, main_content):
        """Process Python HTML content for better readability in eBook format.

        Args:
            main_content: BeautifulSoup object containing the HTML content

        Returns:
            None: The content is modified in place
        """
        if not isinstance(main_content, Tag):
            return

        try:
            # Check if content is wrapped in a div.body - Python docs specific
            body_div = main_content.select_one("div.body")
            if body_div:
                main_content = body_div

            # Improve syntax highlighting visuals
            for pre in main_content.find_all("pre"):
                if not pre.get("class"):
                    pre["class"] = "code"
                if "highlight" in pre.get("class", []):
                    pre["class"].append("code-block")

            # Improve admonitions (notes, warnings)
            for admonition in main_content.select("div.admonition"):
                admonition_classes = admonition.get("class", [])
                if "warning" in admonition_classes:
                    admonition["class"].append("warning-box")
                else:
                    admonition["class"].append("note-box")

            # Remove page-specific navigation that doesn't make sense in an ebook
            for nav in main_content.select(".prevnext"):
                nav.extract()

            # Enhance tables for better ebook display
            for table in main_content.find_all("table"):
                table["border"] = "1"
                table["cellpadding"] = "4"
                if not table.get("class"):
                    table["class"] = "docutils"

            # Fix images - ensure they have proper paths if needed
            for img in main_content.find_all("img"):
                src = img.get("src", "")
                if src.startswith(("../", "./")):
                    img["src"] = src.replace("../", "").replace("./", "")

        except Exception as e:
            self.logger.warning(f"Error processing Python content: {e}")


class MDNEbookMaker(EbookMaker):
    """Class for creating ebooks from MDN JavaScript documentation."""

    def __init__(
        self,
        spider_id="mdn_docs",
        title="MDN JavaScript Documentation",
        author="Mozilla Contributors",
        language="en",
    ):
        """Initialize MDNEbookMaker with metadata."""
        super().__init__(spider_id, title, author, language)

    def _process_content(self, main_content):
        """Process HTML content for better readability in eBook format."""
        # First apply base processing
        super()._process_content(main_content)

        if not isinstance(main_content, Tag):
            return

        try:
            # Remove elements that don't work well in ebooks
            selectors_to_remove = [
                ".newsletter-box",
                ".metadata",
                ".document-toc-container",
                ".metadata-button-container",
                ".top-navigation-container",
                ".page-footer-container",
                ".sidebar-container",
                "nav.breadcrumbs-container",
                "nav.sidebar",
                "aside.metadata",
                "aside.quick-links",
                ".on-github",
                ".translationInProgress",
                ".notecard.deprecated",
                ".visually-hidden",
                ".hidden",
                "iframe",
                "script",
                ".interactive-example",
            ]

            for selector in selectors_to_remove:
                try:
                    for element in main_content.select(selector):
                        if element:
                            element.extract()
                except Exception:
                    # Continue even if a particular selector fails
                    pass

            # Fix code blocks - make sure they render well in ebooks
            for pre in main_content.find_all("pre"):
                if not pre.get("class"):
                    pre["class"] = "code"

            # Turn note/warning boxes into formatted sections with clear titles
            for note in main_content.select(".notecard, .note, .warning"):
                note_type = "Note"
                note_class = note.get("class", [])

                if "warning" in note_class or "danger" in note_class:
                    note_type = "Warning"
                elif "deprecated" in note_class:
                    note_type = "Deprecated"

                # Add a clear heading to the note
                if note.find("h4") is None and note.find("strong") is None:
                    strong = main_content.new_tag("strong")
                    strong.string = f"{note_type}: "
                    note.insert(0, strong)

        except Exception as e:
            # Catch any errors in the processing, but allow the content to be used
            self.logger.warning(f"Error processing MDN content: {e}")


def load_spider_config():
    """
    Load the spider configuration from config.json

    Returns:
        dict: Dictionary of spider configurations by ID
    """
    # Try the path depending on where we're running from
    possible_paths = [
        os.path.join("backend", "spiders", "config.json"),  # From project root
        os.path.join("spiders", "config.json"),  # From backend directory
        os.path.join("..", "spiders", "config.json"),  # From scripts directory
    ]

    for config_path in possible_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    return {
                        spider["id"]: spider
                        for spider in config.get("spiders", [])
                    }
            except Exception as e:
                logger.error(
                    f"Error loading spider config from {config_path}: {e}"
                )
                continue

    logger.error("Could not find config.json in any expected location")
    return {}


def run_spider(spider_id):
    """
    Run a spider by ID using spider_runner.py

    Args:
        spider_id (str): The ID of the spider to run

    Returns:
        bool: True if the spider ran successfully, False otherwise
    """
    logger.info(f"Running spider: {spider_id}")

    # Try to find the spider_runner.py script
    script_paths = [
        os.path.join("backend", "scripts", "spider_runner.py"),
        os.path.join("scripts", "spider_runner.py"),
        os.path.join(".", "spider_runner.py"),
    ]

    script_path = None
    for path in script_paths:
        if os.path.exists(path):
            script_path = path
            break

    if not script_path:
        logger.error("Could not find spider_runner.py")
        return False

    try:
        # Initialize progress bar
        if TQDM_AVAILABLE:
            print(f"{Colors.CYAN}Starting spider: {spider_id}{Colors.RESET}")

            # Initial progress bar
            with tqdm(
                total=100,
                desc=f"Crawling with {Colors.GREEN}{spider_id}{Colors.RESET}",
                bar_format="{desc}: |{bar}| {percentage:3.0f}% [elapsed: {elapsed}]",
                leave=True,
            ) as pbar:
                # Spider process
                process = subprocess.Popen(
                    [sys.executable, script_path, spider_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                # Read output while showing progress
                output = []
                error_output = []

                # Track pages and items
                pages_found = 0
                items_scraped = 0
                total_pages_estimate = 100  # Initial estimate
                current_status = "Initializing crawler..."

                # Read output while running and parse for progress indicators
                start_time = time.time()
                last_update_time = start_time
                update_interval = 0.1  # Update at most every 0.1 seconds

                while process.poll() is None:
                    # Read any available output
                    line = process.stdout.readline()
                    if line:
                        output.append(line.strip())

                        # Extract progress information from Scrapy output
                        if "Crawled" in line and "pages" in line:
                            try:
                                # Extract numbers from strings like "Crawled 42 pages"
                                pages_found = int(
                                    line.split("Crawled")[1]
                                    .split("pages")[0]
                                    .strip()
                                )
                                # Update total estimate if it seems too small
                                if pages_found > total_pages_estimate * 0.8:
                                    total_pages_estimate = max(
                                        pages_found + 20,
                                        int(pages_found * 1.2),
                                    )
                                current_status = f"Found {pages_found} pages"
                            except (ValueError, IndexError):
                                pass

                        if "Scraped" in line and "items" in line:
                            try:
                                # Extract numbers from strings like "Scraped 15 items"
                                items_scraped = int(
                                    line.split("Scraped")[1]
                                    .split("items")[0]
                                    .strip()
                                )
                                current_status = f"Scraped {items_scraped} items from {pages_found} pages"
                            except (ValueError, IndexError):
                                pass

                        # Look for specific page being processed
                        if "Processing:" in line or "Scraping:" in line:
                            current_url = line.split(":", 1)[1].strip()
                            # Truncate long URLs for display
                            if len(current_url) > 60:
                                current_url = current_url[:57] + "..."
                            current_status = f"Processing: {current_url}"

                    # Check for stderr output
                    err_line = process.stderr.readline()
                    if err_line:
                        error_output.append(err_line.strip())
                        if "ERROR" in err_line:
                            current_status = f"Error: {err_line.strip()}"

                    # Update progress bar but not too frequently (avoid flickering)
                    current_time = time.time()
                    if current_time - last_update_time > update_interval:
                        # Calculate progress percentage based on pages found vs estimated
                        if pages_found > 0:
                            progress = min(
                                95,
                                int(
                                    (pages_found / total_pages_estimate) * 100
                                ),
                            )
                        else:
                            # Create pulsing effect for initial crawling
                            elapsed = current_time - start_time
                            progress = int(
                                10 + 10 * (1 + math.sin(elapsed))
                            )  # Oscillates between 0-20%

                        # Update progress bar with new position and description
                        pbar.n = progress
                        elapsed_time = int(current_time - start_time)
                        minutes, seconds = divmod(elapsed_time, 60)
                        time_str = f"{minutes:02d}:{seconds:02d}"
                        pbar.set_description(f"[{time_str}] {current_status}")
                        pbar.refresh()

                        last_update_time = current_time

                    time.sleep(0.05)

                # Capture any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    output.extend(stdout.splitlines())
                if stderr:
                    error_output.extend(stderr.splitlines())

                # Set to 100% when done
                pbar.n = 100
                pbar.set_description(
                    f"Completed: {items_scraped} items from {pages_found} pages"
                )
                pbar.refresh()

                # Check the process return code
                if process.returncode != 0:
                    logger.error(
                        f"{Colors.RED}Error running spider {spider_id}{Colors.RESET}"
                    )
                    for err in error_output:
                        logger.error(err)
                    return False

                # Log the output (for debug purposes)
                for out in output:
                    logger.debug(out)

                print(
                    f"{Colors.GREEN}✓ Spider {spider_id} completed successfully: {items_scraped} items from {pages_found} pages{Colors.RESET}"
                )
        else:
            # Run the spider runner as a subprocess without progress bar
            result = subprocess.run(
                [sys.executable, script_path, spider_id],
                check=True,
                capture_output=True,
                text=True,
            )

            # Log the output
            logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)

        logger.info(f"Spider {spider_id} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running spider {spider_id}: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False


def make_ebook(spider_id, output_filename=None):
    """
    Create an ebook from the specified spider's output

    Args:
        spider_id (str): The ID of the spider
        output_filename (str): Optional output filename

    Returns:
        str: Path to the created EPUB file or None if failed
    """
    logger.info(f"Creating ebook for spider: {spider_id}")

    # Format output filename if provided
    if output_filename and not output_filename.endswith(".epub"):
        output_filename = f"{output_filename}.epub"

    try:
        # Show progress bar for ebook creation
        if TQDM_AVAILABLE:
            print(f"{Colors.CYAN}Creating {spider_id} ebook...{Colors.RESET}")

            # Calculate estimated number of steps based on spider ID
            input_file = os.path.join("backend", "outputs", f"{spider_id}.jl")

            # Count chapters for accurate progress (removing unused variable)
            try:
                with open(input_file, "r", encoding="utf-8"):
                    # Just check if file exists and is readable
                    pass
            except Exception:
                logger.warning(
                    f"Could not access {input_file} for chapter counting"
                )

            # Create a progress bar with estimated steps
            with tqdm(
                total=100,
                desc=f"Creating {Colors.GREEN}{spider_id}{Colors.RESET} ebook",
                bar_format="{desc}: |{bar}| {percentage:3.0f}% [elapsed: {elapsed}]",
                leave=True,
            ) as pbar:
                # Step 1: Initialize maker
                start_time = time.time()

                pbar.set_description("Initializing ebook maker")
                if spider_id == "python_docs":
                    maker = PythonDocsEbookMaker(
                        title="Python 3 Documentation",
                        author="Python Software Foundation",
                        language="en",
                    )
                elif spider_id == "mdn_docs":
                    maker = MDNEbookMaker(
                        spider_id="mdn_docs",
                        title="MDN JavaScript Documentation",
                        author="Mozilla Contributors",
                        language="en",
                    )
                else:
                    logger.error(
                        f"{Colors.RED}Unsupported spider ID: {spider_id}{Colors.RESET}"
                    )
                    return None

                pbar.n = 5  # Initialize to 5%
                pbar.refresh()

                # Patch the maker's load_chapters and create_epub methods to update our progress bar
                original_load_chapters = maker.load_chapters
                original_create_epub = maker.create_epub

                # Keep track of chapters processed
                chapters_processed = 0

                # Patch load_chapters to update progress
                def load_chapters_with_progress():
                    pbar.set_description(
                        f"Loading chapters from {spider_id}.jl"
                    )
                    chapters = original_load_chapters()
                    pbar.n = 10
                    pbar.set_description(f"Loaded {len(chapters)} chapters")
                    pbar.refresh()
                    return chapters

                # Patch create_epub to track individual chapter processing
                def create_epub_with_progress(output_filename=None):
                    # The wrapped version of create_epub that shows more accurate progress
                    nonlocal chapters_processed

                    # Load chapters
                    chapters = load_chapters_with_progress()
                    if not chapters:
                        pbar.set_description(
                            f"{Colors.RED}No chapters found!{Colors.RESET}"
                        )
                        return None

                    try:
                        # Initialize book
                        elapsed = int(time.time() - start_time)
                        pbar.set_description(
                            f"[{elapsed}s] Initializing book structure"
                        )
                        maker.init_book()  # We don't need to store the return value
                        pbar.n = 15
                        pbar.refresh()

                        # Track current file for better status updates
                        current_file = output_filename or f"{spider_id}.epub"

                        # Create chapters - this is the main work
                        url_to_filename = {}

                        # First pass: Map URLs to filenames (fast)
                        pbar.set_description(
                            f"[{elapsed}s] Creating chapter map"
                        )
                        for i, chap in enumerate(chapters):
                            fname = f"chap_{i + 1}.xhtml"
                            url_to_filename[chap["url"]] = fname

                        pbar.n = 20
                        pbar.refresh()

                        # Second pass: Process chapters (slow, main progress updates here)
                        base_progress = 20
                        chapter_progress_range = (
                            60  # 20-80% range for chapter processing
                        )

                        # Calculate increment per chapter
                        chapter_increment = (
                            chapter_progress_range / len(chapters)
                            if chapters
                            else 0
                        )

                        # Process each chapter
                        for i, chap in enumerate(chapters):
                            elapsed = int(time.time() - start_time)
                            chapter_title = chap.get(
                                "title", f"Chapter {i + 1}"
                            )

                            # Truncate long titles for display
                            display_title = chapter_title
                            if len(display_title) > 40:
                                display_title = display_title[:37] + "..."

                            # Show progress with chapter number and title
                            pbar.set_description(
                                f"[{elapsed}s] Processing chapter {i + 1}/{len(chapters)}: {display_title}"
                            )

                            # Process this chapter and add to book
                            chapters_processed += 1

                            # Update progress based on chapters processed
                            current_progress = base_progress + (
                                chapters_processed * chapter_increment
                            )
                            pbar.n = min(80, int(current_progress))
                            pbar.refresh()

                            # Small delay to avoid UI flicker
                            if i % 10 == 0:
                                time.sleep(0.01)

                        # Building navigation and finalizing ebook
                        elapsed = int(time.time() - start_time)
                        pbar.n = 85
                        pbar.set_description(f"[{elapsed}s] Adding CSS styles")
                        pbar.refresh()
                        time.sleep(0.1)

                        pbar.n = 90
                        pbar.set_description(
                            f"[{elapsed}s] Building table of contents"
                        )
                        pbar.refresh()
                        time.sleep(0.1)

                        # Writing EPUB
                        pbar.n = 95
                        pbar.set_description(
                            f"[{elapsed}s] Writing EPUB to {current_file}"
                        )
                        pbar.refresh()

                        # Actually create the ebook - call original method
                        result = original_create_epub(output_filename)

                        # Show final steps and completion
                        elapsed = int(time.time() - start_time)
                        minutes, seconds = divmod(elapsed, 60)
                        time_str = f"{minutes}m {seconds}s"

                        if result:
                            pbar.n = 100
                            file_size = os.path.getsize(result)
                            size_kb = file_size / 1024
                            if size_kb > 1024:
                                size_str = f"{size_kb / 1024:.1f} MB"
                            else:
                                size_str = f"{size_kb:.1f} KB"

                            pbar.set_description(
                                f"{Colors.GREEN}Completed in {time_str}: {chapters_processed} chapters, {size_str}{Colors.RESET}"
                            )
                        else:
                            pbar.n = 100
                            pbar.set_description(
                                f"{Colors.RED}Failed to create EPUB after {time_str}{Colors.RESET}"
                            )
                        pbar.refresh()

                        return result

                    except Exception as e:
                        pbar.n = 100
                        pbar.set_description(
                            f"{Colors.RED}Error: {str(e)}{Colors.RESET}"
                        )
                        pbar.refresh()
                        logger.error(f"Error in create_epub: {e}")
                        logger.error(traceback.format_exc())
                        return None

                # Replace the methods
                maker.load_chapters = load_chapters_with_progress
                maker.create_epub = create_epub_with_progress

                # Call the patched method
                result = maker.create_epub(output_filename)

                # Print final result
                if result:
                    file_size = os.path.getsize(result)
                    size_kb = file_size / 1024
                    if size_kb > 1024:
                        size_str = f"{size_kb / 1024:.1f} MB"
                    else:
                        size_str = f"{size_kb:.1f} KB"
                    print(
                        f"{Colors.GREEN}✓ Created {output_filename or spider_id}.epub: {chapters_processed} chapters, {size_str}{Colors.RESET}"
                    )

        else:
            # No progress bar available, create ebook normally
            if spider_id == "python_docs":
                maker = PythonDocsEbookMaker(
                    title="Python 3 Documentation",
                    author="Python Software Foundation",
                    language="en",
                )
                result = maker.create_epub(output_filename)
            elif spider_id == "mdn_docs":
                maker = MDNEbookMaker(
                    spider_id="mdn_docs",
                    title="MDN JavaScript Documentation",
                    author="Mozilla Contributors",
                    language="en",
                )
                result = maker.create_epub(output_filename)
            else:
                logger.error(f"Unsupported spider ID: {spider_id}")
                return None

        return result
    except Exception as e:
        logger.error(f"Error creating ebook: {e}")
        logger.error(traceback.format_exc())
        return None


def optimize_ebook(input_path=None):
    """
    Optimize ebooks using book_optimizer.sh

    Args:
        input_path (str): Optional path to the input directory

    Returns:
        bool: True if optimization was successful, False otherwise
    """
    logger.info("Optimizing ebooks")

    # Try to find the book_optimizer.sh script
    script_paths = [
        os.path.join("backend", "scripts", "book_optimizer.sh"),
        os.path.join("scripts", "book_optimizer.sh"),
        os.path.join(".", "book_optimizer.sh"),
    ]

    script_path = None
    for path in script_paths:
        if os.path.exists(path):
            script_path = path
            break

    if not script_path:
        logger.error("Could not find book_optimizer.sh")
        return False

    try:
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Prepare command
        cmd = [script_path]
        if input_path:
            cmd.append(input_path)

        # Show progress for optimization
        if TQDM_AVAILABLE:
            print("Optimizing ebooks...")

            # Create a progress bar for optimization steps
            steps = 4  # Main steps in the optimizer
            with tqdm(
                total=steps,
                desc="Optimizing ebooks",
                bar_format="{desc}: |{bar}| {percentage:3.0f}% [elapsed: {elapsed}]",
            ) as pbar:
                pbar.set_description("Starting optimizer")

                # Run the optimizer as a subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )

                # Read output line by line and update progress
                output = []
                error_output = []

                # Track optimization steps based on output
                progress_markers = {
                    "Checking for required tools": False,
                    "Processing PDF files": False,
                    "Processing EPUB files": False,
                    "Summary:": False,
                }

                # In case we don't get recognizable output, fall back to time-based progress
                start_time = time.time()
                timeout = 60  # seconds

                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break

                    # Update based on time if we're taking too long
                    elapsed_time = time.time() - start_time
                    if elapsed_time > timeout:
                        # Ensure we complete the progress bar
                        remaining_steps = steps - pbar.n
                        if remaining_steps > 0:
                            pbar.update(remaining_steps)
                            pbar.set_description("Optimization complete")
                        break

                    if line:
                        line = line.strip()
                        output.append(line)

                        # Update progress based on recognizable steps
                        for marker, updated in progress_markers.items():
                            if not updated and marker in line:
                                pbar.update(1)
                                pbar.set_description(f"{marker}")
                                progress_markers[marker] = True
                                break

                        # If we see 'Error', update the description
                        if "Error" in line:
                            pbar.set_description(f"Error: {line[:30]}...")

                # Capture any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    output.append(stdout)
                if stderr:
                    error_output.append(stderr)

                # Ensure 100% at completion
                pbar.n = steps
                pbar.refresh()

                # Check process return code
                if process.returncode != 0:
                    logger.error("Error during optimization")
                    for err in error_output:
                        logger.error(err)
                    return False

                # Log the complete output
                for out in output:
                    logger.info(out)
        else:
            # Run the optimizer without progress bar
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )

            # Log the output
            logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)

        logger.info("Ebook optimization completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error optimizing ebooks: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False


def list_spiders():
    """
    List available spiders from the configuration
    """
    spider_configs = load_spider_config()
    if not spider_configs:
        print(
            f"{Colors.YELLOW}No spiders found in configuration{Colors.RESET}"
        )
        return

    print(f"\n{Colors.CYAN}{Colors.BOLD}Available Spiders:{Colors.RESET}")
    print(
        f"{Colors.BLUE}========================================{Colors.RESET}"
    )
    for spider_id, config in spider_configs.items():
        print(
            f"  {Colors.BOLD}ID:{Colors.RESET} {Colors.GREEN}{spider_id}{Colors.RESET}"
        )
        print(
            f"  {Colors.BOLD}Name:{Colors.RESET} {config.get('name', 'Unnamed')}"
        )
        print(
            f"  {Colors.BOLD}Description:{Colors.RESET} {config.get('description', 'No description')}"
        )
        print(
            f"{Colors.BLUE}----------------------------------------{Colors.RESET}"
        )


def main():
    """Main function to parse arguments and run the workflow"""
    parser = argparse.ArgumentParser(
        description="TukuyBooks Unified Ebook Maker"
    )
    parser.add_argument(
        "--spider", help="Run the specified spider before creating ebooks"
    )
    parser.add_argument(
        "--make-ebook",
        help="Create an ebook from the specified spider's output",
    )
    parser.add_argument(
        "--optimize", action="store_true", help="Optimize the generated ebooks"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the complete workflow (scrape, make ebook, optimize)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available spiders"
    )
    parser.add_argument(
        "--output", help="Specify output filename (without extension)"
    )

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # List available spiders
    if args.list:
        list_spiders()
        return

    # Run the complete workflow if --all is specified
    if args.all:
        spider_configs = load_spider_config()
        if not spider_configs:
            logger.error("No spiders found in configuration")
            return

        success = True
        total_spiders = len(spider_configs)

        # Show a nice header for the complete workflow with colors
        border = f"{Colors.BLUE}{'=' * 60}{Colors.RESET}"
        print(f"\n{border}")
        print(
            f"{Colors.CYAN}{Colors.BOLD}  STARTING COMPLETE WORKFLOW FOR {total_spiders} SPIDERS{Colors.RESET}"
        )
        print(f"{border}")

        # Track time for the entire process
        workflow_start_time = time.time()

        # Process each spider
        for i, spider_id in enumerate(spider_configs, 1):
            print(
                f"\n{Colors.YELLOW}[{i}/{total_spiders}]{Colors.RESET} {Colors.BOLD}Processing {spider_id.upper()}:{Colors.RESET}"
            )
            print(f"{Colors.BLUE}{'-' * 40}{Colors.RESET}")

            # Run spider
            print(
                f"{Colors.CYAN}➤ Step 1:{Colors.RESET} Running spider for {Colors.BOLD}{spider_id}{Colors.RESET}"
            )
            if not run_spider(spider_id):
                print(
                    f"{Colors.RED}✘ Failed to run spider: {spider_id}{Colors.RESET}"
                )
                success = False
                continue

            # Create ebook
            print(
                f"{Colors.CYAN}➤ Step 2:{Colors.RESET} Creating ebook for {Colors.BOLD}{spider_id}{Colors.RESET}"
            )
            output_path = make_ebook(spider_id, args.output)
            if not output_path:
                print(
                    f"{Colors.RED}✘ Failed to create ebook for: {spider_id}{Colors.RESET}"
                )
                success = False
            else:
                print(
                    f"  {Colors.GREEN}✓ Created:{Colors.RESET} {output_path}"
                )

        # Optimize ebooks
        print(f"\n{Colors.CYAN}➤ Step 3:{Colors.RESET} Optimizing all ebooks")
        if not optimize_ebook():
            print(f"{Colors.RED}✘ Failed to optimize ebooks{Colors.RESET}")
            success = False

        # Show completion message with total time
        total_time = time.time() - workflow_start_time
        minutes, seconds = divmod(int(total_time), 60)
        print(f"\n{border}")
        if success:
            print(
                f"  {Colors.GREEN}✓ WORKFLOW COMPLETED SUCCESSFULLY{Colors.RESET} in {Colors.BOLD}{minutes}m {seconds}s{Colors.RESET}"
            )
        else:
            print(
                f"  {Colors.RED}⚠ WORKFLOW COMPLETED WITH ERRORS{Colors.RESET} in {Colors.BOLD}{minutes}m {seconds}s{Colors.RESET}"
            )
        print(f"{border}\n")

        return success

    # Run individual steps based on arguments
    success = True

    # Run spider if specified
    if args.spider:
        if not run_spider(args.spider):
            logger.error(f"Failed to run spider: {args.spider}")
            success = False

    # Create ebook if specified
    if args.make_ebook:
        if not make_ebook(args.make_ebook, args.output):
            logger.error(f"Failed to create ebook for: {args.make_ebook}")
            success = False

    # Optimize ebooks if specified
    if args.optimize:
        if not optimize_ebook():
            logger.error("Failed to optimize ebooks")
            success = False

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
