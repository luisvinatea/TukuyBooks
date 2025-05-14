"""mdn_ebook_maker.py
This module extends the EbookMaker class to provide specific processing
for MDN JavaScript documentation.
"""

from .make_ebook import EbookMaker
from bs4 import Tag


class MDNEbookMaker(EbookMaker):
    """Class for creating ebooks from MDN JavaScript documentation."""

    def __init__(
        self,
        spider_id="mdn_docs",
        title="MDN JavaScript Documentation",
        author="Mozilla Contributors",
        language="en",
    ):
        """Initialize MDNEbookMaker with metadata.

        Args:
            spider_id (str): ID of the spider used to scrape the data.
            title (str): Title of the ebook.
            author (str): Author of the ebook.
            language (str): Language of the ebook.
        """
        super().__init__(spider_id, title, author, language)

    def _process_content(self, main_content):
        """Process HTML content for better readability in eBook format.

        This method applies custom processing for MDN content,
        removing elements that don't work well in ebooks and
        improving the formatting for better readability.

        Args:
            main_content (bs4.element.Tag): BeautifulSoup Tag containing content
        """
        # First apply base processing
        super()._process_content(main_content)

        if not isinstance(main_content, Tag):
            return

        # Remove elements that don't work well in ebooks
        selectors_to_remove = [
            ".newsletter-box",
            ".metadata",
            ".document-toc-container",  # Table of contents (we'll generate our own)
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
                element.extract()

        # Fix code blocks - make sure they render well in ebooks
        for pre in main_content.find_all("pre"):
            if not pre.get("class"):
                pre["class"] = "code"

        # Fix syntax highlighting classes to be more compatible with ebook readers
        for code in main_content.find_all(["pre", "code"]):
            if code.get("class"):
                new_classes = []
                for cls in code.get("class"):
                    if cls.startswith("language-") or cls.startswith("brush:"):
                        new_classes.append(cls)
                    else:
                        new_classes.append("code")
                code["class"] = new_classes

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

        # Make sure images have descriptive alt text if missing
        for img in main_content.find_all("img"):
            if not img.get("alt"):
                img["alt"] = img.get("title", "Image from MDN documentation")

        # Make sure all links to code samples are inline
        for sample_link in main_content.select("a.jsExampleLink"):
            if sample_link.get("href"):
                sample_link.replace_with(
                    "[Code example available on MDN website]"
                )

        # Ensure all headings have IDs for internal linking
        for level in range(1, 7):
            for heading in main_content.find_all(f"h{level}"):
                if not heading.get("id") and heading.string:
                    heading["id"] = (
                        heading.get_text(strip=True).lower().replace(" ", "-")
                    )

        # Add a meaningful prefix to raw fragment IDs
        for a in main_content.find_all("a"):
            if a.get("href") and a["href"].startswith("#"):
                a["href"] = f"#{a['href'][1:]}"
