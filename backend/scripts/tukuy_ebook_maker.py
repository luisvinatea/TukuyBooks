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
    --convert            Convert an EPUB to PDF using book_converter.sh
    --all                 Run the complete workflow (scrape, make ebook, convert)
    --list                List available spiders
    --output OUTPUT       Specify output filename (without extension)
    --help                Show this help message and exit
"""

import sys
import os
import logging
import json
import traceback
import platform
import argparse
import subprocess
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag
import importlib.util

# Import spider_runner from the same directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import spider_runner  # noqa: E402

# Determine project root (two levels up from this script)
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

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


# Check for tqdm availability using importlib.util.find_spec instead of direct import
TQDM_AVAILABLE = importlib.util.find_spec("tqdm") is not None
if TQDM_AVAILABLE:
    from tqdm import tqdm
else:
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
        # Always resolve input/output relative to project root
        self.input_file = os.path.join(
            PROJECT_ROOT, "backend", "outputs", f"{spider_id}.jl"
        )
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

        # Always resolve output path relative to project root
        output_path = os.path.join(
            PROJECT_ROOT, "backend", "outputs", output_filename
        )

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        chapters = self.load_chapters()
        if not chapters:
            self.logger.error("No chapters found!")
            print(f"{Colors.RED}No chapters found!{Colors.RESET}")
            return None

        try:
            self.logger.info(
                f"Initializing book with {len(chapters)} chapters"
            )
            print(
                f"{Colors.BLUE}Initializing book with {len(chapters)} chapters{Colors.RESET}"
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
            iterator = (
                tqdm(
                    enumerate(chapters),
                    total=len(chapters),
                    desc="Processing chapters",
                )
                if TQDM_AVAILABLE
                else enumerate(chapters)
            )
            for i, chap in iterator:
                chapter_title = chap.get("title", f"Chapter {i + 1}")
                soup = self.clean_html_content(
                    chap["content"], chapter_title, i
                )

                try:
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

                    self._process_content(soup)
                    content = str(soup)
                except Exception as e:
                    self.logger.warning(
                        f"Error processing links for chapter {i + 1} '{chapter_title}': {e}"
                    )
                    print(
                        f"{Colors.YELLOW}Warning: Error processing links for chapter {i + 1} '{chapter_title}': {e}{Colors.RESET}"
                    )
                    content = str(soup)

                c = epub.EpubHtml(
                    title=chapter_title,
                    file_name=url_to_filename[chap["url"]],
                    lang=self.language,
                    content=content,
                )

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
            print(f"{Colors.BLUE}Writing EPUB to {output_path}{Colors.RESET}")

            if os.path.exists(output_path):
                os.remove(output_path)
                self.logger.info(f"Removed existing file: {output_path}")
                print(
                    f"{Colors.YELLOW}Removed existing file: {output_path}{Colors.RESET}"
                )

            epub.write_epub(output_path, book, {})

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(
                    f"EPUB created successfully: {output_path} ({file_size} bytes)"
                )
                print(
                    f"{Colors.GREEN}EPUB created successfully: {output_path} ({file_size} bytes){Colors.RESET}"
                )
                return output_path
            else:
                self.logger.error("Failed to create EPUB file")
                print(f"{Colors.RED}Failed to create EPUB file{Colors.RESET}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating EPUB: {e}")
            self.logger.error(traceback.format_exc())
            print(f"{Colors.RED}Error creating EPUB: {e}{Colors.RESET}")
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


class ReactEbookMaker(EbookMaker):
    """Class for creating ebooks from React documentation."""

    def __init__(
        self,
        spider_id="react_docs",
        title="React Documentation",
        author="React Team and Contributors",
        language="en",
    ):
        """Initialize ReactEbookMaker with metadata."""
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
                "nav",
                "header",
                "footer",
                ".theme-toggle",
                ".edit-page-link",
                ".search",
                "script",
                "iframe",
                ".logo",
                ".social-links",
                ".feedback",
                ".sidebar",
            ]

            for selector in selectors_to_remove:
                try:
                    for element in main_content.select(selector):
                        if element:
                            element.extract()
                except Exception:
                    # Continue even if a particular selector fails
                    pass

            # Fix code blocks for better ebook rendering
            for pre in main_content.find_all("pre"):
                if not pre.get("class"):
                    pre["class"] = "code"

            # Process React-specific callout styles
            for note in main_content.select(
                ".admonition, .note, .warning, .pitfall, .caution, .info"
            ):
                note_type = "Note"
                note_class = note.get("class", [])

                if (
                    "warning" in note_class
                    or "caution" in note_class
                    or "pitfall" in note_class
                ):
                    note_type = "Warning"
                elif "info" in note_class:
                    note_type = "Info"
                elif "note" in note_class:
                    note_type = "Note"

                # Add a clear heading if not present
                if note.find("h4") is None and note.find("strong") is None:
                    strong = main_content.new_tag("strong")
                    strong.string = f"{note_type}: "
                    note.insert(0, strong)

        except Exception as e:
            # Catch any errors in the processing, but allow the content to be used
            self.logger.warning(f"Error processing React content: {e}")


def load_spider_config():
    """
    Load the spider configuration from config.json

    Returns:
        dict: Spider configuration including available spiders and their settings
    """
    # Always resolve path relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "spiders", "config.json")
    config_path = os.path.normpath(config_path)
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}")
        return {"spiders": {}}
    except json.JSONDecodeError:
        logger.error(f"Error parsing config file at {config_path}")
        return {"spiders": {}}


def main():
    parser = argparse.ArgumentParser(
        description="TukuyBooks Unified Ebook Maker",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--spider",
        type=str,
        help="Run the specified spider before creating ebooks",
    )
    parser.add_argument(
        "--make-ebook",
        type=str,
        help="Create an ebook from the specified spider's output",
    )
    parser.add_argument(
        "--convert",  # <-- changed from --optimize
        action="store_true",
        help="Convert an EPUB to PDF using book_converter.sh",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the complete workflow (scrape, make ebook, convert)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available spiders"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Specify output filename (without extension)",
    )
    args = parser.parse_args()

    if args.list:
        config = load_spider_config()
        spiders = config.get("spiders", {})
        if isinstance(spiders, dict) and spiders:
            print(f"{Colors.BOLD}Available spiders:{Colors.RESET}")
            for spider_id, spider_info in spiders.items():
                desc = spider_info.get("description", "")
                print(f"  {Colors.CYAN}{spider_id}{Colors.RESET} - {desc}")
        elif isinstance(spiders, list) and spiders:
            print(f"{Colors.BOLD}Available spiders:{Colors.RESET}")
            for spider in spiders:
                if isinstance(spider, dict):
                    spider_id = spider.get("id", "(unknown)")
                    desc = spider.get("description", "")
                    print(f"  {Colors.CYAN}{spider_id}{Colors.RESET} - {desc}")
                else:
                    print(f"  {Colors.CYAN}{spider}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}No spiders found in config.{Colors.RESET}")
        return

    if args.spider:
        spider_id = args.spider
        print(f"{Colors.BLUE}Running spider: {spider_id}{Colors.RESET}")
        success = spider_runner.run_spider(spider_id)
        if success:
            print(
                f"{Colors.GREEN}Spider '{spider_id}' completed successfully.{Colors.RESET}"
            )
        else:
            print(
                f"{Colors.RED}Spider '{spider_id}' failed or not found.{Colors.RESET}"
            )
        return

    if args.make_ebook:
        spider_id = args.make_ebook
        output_filename = args.output if args.output else None

        # Select the correct EbookMaker class
        if spider_id == "python_docs":
            maker = PythonDocsEbookMaker()
        elif spider_id == "mdn_docs":
            maker = MDNEbookMaker()
        elif spider_id == "react_docs":
            maker = ReactEbookMaker()
        else:
            print(f"{Colors.RED}Unknown spider ID: {spider_id}{Colors.RESET}")
            return

        result = maker.create_epub(output_filename)
        if result:
            print(f"{Colors.GREEN}EPUB created: {result}{Colors.RESET}")
        else:
            print(
                f"{Colors.RED}Failed to create EPUB for spider '{spider_id}'{Colors.RESET}"
            )
        return

    if args.convert:
        # Always resolve converter script relative to this script
        converter_script = os.path.join(SCRIPT_DIR, "book_converter.sh")
        if not os.path.isfile(converter_script):
            print(
                f"{Colors.RED}Converter script not found: {converter_script}{Colors.RESET}"
            )
            return
        print(f"{Colors.BLUE}Running book converter...{Colors.RESET}")

        # Ensure unbuffered output for tqdm compatibility
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Use subprocess with unbuffered output, forwarding stdout/stderr live
        process = subprocess.Popen(
            ["bash", converter_script],
            cwd=SCRIPT_DIR,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
            bufsize=1,
        )
        process.wait()
        if process.returncode == 0:
            print(
                f"{Colors.GREEN}Book conversion completed successfully.{Colors.RESET}"
            )
        else:
            print(
                f"{Colors.RED}Book conversion failed with exit code {process.returncode}.{Colors.RESET}"
            )
        return

    # ...other CLI logic can be added here...


if __name__ == "__main__":
    main()
