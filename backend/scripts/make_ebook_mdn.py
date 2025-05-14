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

            for i, chap in enumerate(chapters):
                # Map the URL to filename
                fname = f"chap_{i + 1}.xhtml"
                url_to_filename[chap["url"]] = fname

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
                    file_name=fname,
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
                ".notecard.warning",
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
            # We don't need to modify main_content here as we're operating on it directly


# Add a CLI to run the ebook maker
if __name__ == "__main__":
    # Set up more verbose logging to debug our improvements
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

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
