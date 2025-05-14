#!/usr/bin/env python3
"""make_ebook_pydocs.py
This module provides specialized functionality for converting Python documentation
into EPUB and PDF formats.
"""

import json
import os
import logging
import sys
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag


class PythonDocsEbookMaker:
    """Class for creating ebooks from scraped Python documentation."""

    def __init__(
        self,
        title="Python 3 Documentation",
        author="Python Software Foundation",
        language="en",
    ):
        """Initialize PythonDocsEbookMaker with Python-specific metadata.

        Args:
            title (str): Title of the ebook.
            author (str): Author of the ebook.
            language (str): Language of the ebook.
        """
        self.spider_id = "python_docs"
        self.title = title
        self.author = author
        self.language = language
        self.input_file = os.path.join(
            "backend", "outputs", f"{self.spider_id}.jl"
        )
        self.logger = logging.getLogger(__name__)

        # Python-specific anchor mapping
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

            # Sort by priority first, then by level, then by title for better organization
            chapters.sort(
                key=lambda x: (
                    x.get("priority", 999),
                    x.get("level", 1),
                    x.get("title", ""),
                )
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

        # Python documentation specific: handle module references
        if href.startswith("../") or href.startswith("./"):
            # Convert relative paths to absolute paths
            href = href.replace("../", "").replace("./", "")

        # Handle fragments in URLs
        base, fragment = (href.split("#", 1) + [""])[:2]
        fragment = "#" + fragment if fragment else ""

        # Map known anchors
        if fragment[1:] in self.anchor_map:
            fragment = "#" + self.anchor_map[fragment[1:]]

        # Python-specific: convert module references
        if base.endswith(".html") or base == "":
            # Direct URL mapping - check for exact or partial matches
            match = None
            for url in url_to_filename:
                if base in url or url.endswith(base):
                    match = url
                    break

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
            BeautifulSoup: Cleaned HTML content as BeautifulSoup object
        """
        try:
            # Parse the HTML content
            soup = BeautifulSoup(html_content, "html.parser")

            # Check if content is wrapped in a div.body - this is Python docs specific
            main_content = soup.select_one("div.body")
            if main_content:
                soup = main_content

            # Process the content
            self._process_content(soup)

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
            # Remove elements that don't work well in ebooks
            selectors_to_remove = [
                "div.sphinxsidebar",
                "div.sphinxsidebarwrapper",
                "div.related",
                "div.footer",
                "div#searchbox",
                ".headerlink",
                "div.clearer",
                "form.inline-search",
                "form#search",
                ".searchformwrapper",
                "div[role='navigation']",
                "nav.contents",
                "div.banner",
                "script",
                "iframe",
            ]

            for selector in selectors_to_remove:
                try:
                    for element in main_content.select(selector):
                        if element:
                            element.extract()
                except Exception as e:
                    self.logger.debug(f"Error removing {selector}: {e}")
                    # Continue even if a particular selector fails
                    pass

            # Improve syntax highlighting visuals
            for pre in main_content.find_all("pre"):
                if not pre.get("class"):
                    pre["class"] = "code"
                # Ensure code examples are properly displayed
                for code in pre.find_all("span", class_="pre"):
                    code["style"] = "font-family: monospace;"

            # Improve admonitions (notes, warnings)
            for admonition in main_content.select("div.admonition"):
                title_elem = admonition.select_one("p.admonition-title")

                # Ensure admonitions have clear styling
                if title_elem:
                    title_elem["style"] = "font-weight: bold; color: #333;"

            # Remove page-specific navigation that doesn't make sense in an ebook
            for nav in main_content.select(".prevnext"):
                nav.extract()

            # Enhance tables for better ebook display
            for table in main_content.find_all("table"):
                table["style"] = (
                    "width: 100%; border-collapse: collapse; margin: 1em 0;"
                )
                for tr in table.find_all("tr"):
                    for td in tr.find_all(["td", "th"]):
                        td["style"] = "border: 1px solid #ddd; padding: 8px;"

            # Fix images - ensure they have proper paths if needed
            for img in main_content.find_all("img"):
                if img.get("src"):
                    # Handle if we were to include images
                    pass

        except Exception as e:
            self.logger.warning(f"Error processing Python content: {e}")

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
                f"Initializing Python documentation book with {len(chapters)} chapters"
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

            # Define CSS specific for Python documentation
            style = """
            body {
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                margin: 2%;
                padding: 0;
                line-height: 1.5;
                color: #333;
            }
            h1, h2, h3, h4 {
                color: #265F8B;
                font-weight: normal;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
            }
            h1 {
                font-size: 2em;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.5em;
            }
            h2 {
                font-size: 1.5em;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.3em;
            }
            a {
                color: #0072aa;
                text-decoration: none;
            }
            code, pre {
                font-family: 'Consolas', 'Menlo', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', monospace;
                background-color: #f8f8f8;
                color: #333;
            }
            code {
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-size: 0.9em;
            }
            pre {
                padding: 1em;
                overflow-x: auto;
                white-space: pre-wrap;
                border-radius: 3px;
                max-width: 100%;
                margin: 1em 0;
                border: 1px solid #e1e4e5;
                line-height: 1.4;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #e1e4e5;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f8f8f8;
            }
            .admonition {
                padding: 12px;
                margin-bottom: 12px;
                border: 1px solid #e1e4e5;
                border-radius: 3px;
            }
            .admonition-title {
                margin: -12px -12px 12px;
                padding: 6px 12px;
                font-weight: bold;
                background-color: #e1e4e5;
            }
            .note .admonition-title {
                background-color: #9ED5FF;
            }
            .warning .admonition-title {
                background-color: #FFCBC8;
            }
            """

            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/style.css",
                media_type="text/css",
                content=style,
            )
            book.add_item(nav_css)

            # Simply add all chapters to TOC for now
            book.toc = epub_chapters

            # Add navigation files
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Define spine
            book.spine = ["nav"] + epub_chapters

            # Write to file
            self.logger.info(
                f"Writing Python documentation EPUB to {output_path}"
            )

            # Check if the output file already exists and remove it
            if os.path.exists(output_path):
                os.remove(output_path)
                self.logger.info(f"Removed existing file: {output_path}")

            epub.write_epub(output_path, book, {})

            # Verify the file was created and log its size
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(
                    f"Python documentation EPUB created successfully: {output_path} ({file_size} bytes)"
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


# Command-line interface for the Python documentation ebook maker
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse command line arguments
    output_filename = None
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]

    # Create and run the Python docs ebook maker
    maker = PythonDocsEbookMaker(
        title="Python 3 Documentation",
        author="Python Software Foundation",
        language="en",
    )

    result = maker.create_epub(output_filename)

    if result:
        print(f"Successfully created Python documentation ebook at: {result}")
        sys.exit(0)
    else:
        print("Failed to create Python documentation ebook")
        sys.exit(1)
