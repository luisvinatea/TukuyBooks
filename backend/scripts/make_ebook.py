"""make_ebook.py
This module provides functionality for converting scraped documentation
into EPUB and PDF formats.
"""

import json
import os
import logging
import sys
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag


class EbookMaker:
    """Class for creating ebooks from scraped documentation."""

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

    def create_items(self, chapters, book):
        """Create EpubHtml items, map URLs to filenames, and add to book.

        Args:
            chapters (list): List of chapter dictionaries.
            book (epub.EpubBook): Book object to add items to.

        Returns:
            tuple: URL to filename mapping and list of epub chapters.
        """
        url_to_filename = {}
        epub_chapters = []
        for i, chap in enumerate(chapters):
            fname = f"chap_{i + 1}.xhtml"
            url_to_filename[chap["url"]] = fname

            # Create a basic HTML structure for the content
            initial_content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>{chap["title"]}</title>
  </head>
  <body>
    <h1>{chap["title"]}</h1>
    <p>Chapter content will be replaced during processing.</p>
  </body>
</html>"""

            # Create the item with initial content
            item = epub.EpubHtml(
                title=chap["title"],
                file_name=fname,
                lang=self.language,
                content=initial_content,
            )
            epub_chapters.append(item)
            book.add_item(item)
            self.logger.debug(
                f"Created item for chapter {i + 1}: {chap['title']}"
            )

        return url_to_filename, epub_chapters

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

    def fix_internal_links(self, chapters, epub_chapters, url_to_filename):
        """Update internal links in each chapter content.

        Args:
            chapters (list): List of chapter dictionaries.
            epub_chapters (list): List of EpubHtml objects.
            url_to_filename (dict): Mapping of URLs to filenames.
        """
        for idx, chap in enumerate(chapters):
            soup = BeautifulSoup(chap["content"], "html.parser")

            # First process internal references
            for element in soup.find_all("a", class_="reference internal"):
                if not isinstance(element, Tag):
                    continue
                raw_href = element.attrs.get("href", "")
                new_href = self.rewrite_href(
                    raw_href,
                    url_to_filename,
                    chapters,
                    chap.get("internal_links", {}),
                )
                if new_href:
                    element["href"] = new_href

            # Process any other links that might be internal
            for element in soup.find_all("a", href=True):
                if (
                    "class" in element.attrs
                    and "reference internal" in element["class"]
                ):
                    continue  # Already processed

                raw_href = element.attrs.get("href", "")
                new_href = self.rewrite_href(
                    raw_href,
                    url_to_filename,
                    chapters,
                    chap.get("internal_links", {}),
                )
                if new_href:
                    element["href"] = new_href

            # Apply custom content processing if needed
            self._process_content(soup)

            # Make sure we're setting valid XHTML content for the epub
            content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>{chap["title"]}</title>
  </head>
  <body>
    {str(soup)}
  </body>
</html>"""

            # Set the properly formatted content to the epub chapter
            epub_chapters[idx].content = content

    def add_toc(self, book, epub_chapters, chapters):
        """Add table of contents to the book.

        Args:
            book (epub.EpubBook): Book object to add TOC to.
            epub_chapters (list): List of EpubHtml objects.
            chapters (list): List of chapter dictionaries.
        """
        # Create a simple flat TOC - more reliable across different datasets
        toc = []
        for epub_chap in epub_chapters:
            toc.append(epub_chap)

        book.toc = toc

        # Add default NCX and Navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define CSS
        style = """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.5;
            margin: 2em;
        }
        h1, h2, h3, h4 {
            color: #333;
            margin-top: 1.5em;
        }
        pre, code {
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 0.2em;
            font-family: monospace;
        }
        pre {
            padding: 0.5em;
            overflow-x: auto;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        """

        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style,
        )
        book.add_item(nav_css)

        # Create spine
        book.spine = ["nav"] + epub_chapters

        self.logger.info(
            f"Created TOC with {len(toc)} entries, added NCX and Nav files"
        )

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

            self.logger.info("Creating items")
            url_to_filename, epub_chapters = self.create_items(chapters, book)

            # Log the initial state of the first chapter
            self.logger.info(f"First chapter title: {epub_chapters[0].title}")
            self.logger.info(
                f"First chapter content length: {len(epub_chapters[0].content) if epub_chapters[0].content else 0} bytes"
            )
            self.logger.info(
                f"First chapter filename: {epub_chapters[0].file_name}"
            )

            self.logger.info("Fixing internal links")
            self.fix_internal_links(chapters, epub_chapters, url_to_filename)

            # Log the content length after fixing links
            self.logger.info(
                f"First chapter content length after fixing: {len(epub_chapters[0].content) if epub_chapters[0].content else 0} bytes"
            )

            # Check if content is properly set in all chapters
            empty_chapters = sum(1 for ch in epub_chapters if not ch.content)
            if empty_chapters:
                self.logger.warning(
                    f"{empty_chapters} chapters have no content!"
                )

            self.logger.info("Building table of contents")
            self.add_toc(book, epub_chapters, chapters)

            # Write the EPUB file
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
                    f"EPUB created at {output_path} ({file_size} bytes)"
                )
            else:
                self.logger.error(
                    f"EPUB file was not created at {output_path}"
                )

            return output_path
        except Exception as e:
            self.logger.error(f"Error creating EPUB: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return None


class PythonDocsEbookMaker(EbookMaker):
    """Class for creating ebooks from scraped Python documentation."""

    def __init__(
        self,
        title="Python 3 Documentation",
        author="Python Software Foundation",
    ):
        """Initialize PythonDocsEbookMaker with Python-specific metadata.

        Args:
            title (str): Title of the ebook.
            author (str): Author of the ebook.
        """
        super().__init__("python_docs", title, author)

        # Add Python-specific anchor mapping
        self.anchor_map = {
            "library-index": "the-python-standard-library",
            "reference-index": "the-python-language-reference",
            "extending-index": "extending-and-embedding-the-python-interpreter",
            "c-api-index": "python-c-api-reference-manual",
        }


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
            ".notecard.warning",
            ".visually-hidden",
            ".hidden",
            "iframe",
            "script",
            ".interactive-example",
        ]

        for selector in selectors_to_remove:
            for element in main_content.select(selector):
                if element:
                    element.extract()

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


# Add a CLI to run the ebook maker
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python make_ebook.py <spider_id> [output_filename]")
        sys.exit(1)

    spider_id = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None

    # Check if the spider ID is valid
    if spider_id == "python_docs":
        maker = PythonDocsEbookMaker()
        maker.create_epub(output_filename)
    elif spider_id == "mdn_docs":
        # Create the MDN ebook maker directly instead of importing
        # This avoids import issues in containerized environments
        maker = MDNEbookMaker(
            spider_id="mdn_docs",
            title="MDN JavaScript Documentation",
            author="Mozilla Contributors",
        )
        maker.create_epub(output_filename)
    else:
        print(f"Unknown spider ID: {spider_id}")
        print("Supported IDs: python_docs, mdn_docs")
        sys.exit(1)
