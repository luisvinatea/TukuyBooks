"""epub_checker.py
This module provides functionality for checking EPUB files for broken links
and other issues.
"""

import os
import logging
from datetime import datetime
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4


class EpubChecker:
    """Class for checking EPUB files."""

    def __init__(self, epub_file_path):
        """Initialize EpubChecker.

        Args:
            epub_file_path (str): Path to the EPUB file.
        """
        self.epub_file_path = epub_file_path
        self.log_file = self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.num_broken_links = 0
        self.num_missing_files = 0
        self.num_missing_anchors = 0
        self.num_valid_links = 0

    def _setup_logging(self):
        """Set up logging configuration.

        Returns:
            str: Path to the log file.
        """
        # Create a log file in the same directory as the EPUB file
        log_dir = os.path.dirname(self.epub_file_path) or "."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"epub_link_check_{timestamp}.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        return log_file

    def load_epub(self):
        """Load an EPUB file.

        Returns:
            epub.EpubBook: Loaded EPUB book object or None if loading fails.
        """
        if not os.path.exists(self.epub_file_path):
            self.logger.error(
                f"Error: EPUB file not found at {self.epub_file_path}"
            )
            return None

        try:
            return epub.read_epub(self.epub_file_path)
        except (FileNotFoundError, epub.EpubException, RuntimeError) as e:
            self.logger.error(f"Error loading EPUB: {e}")
            return None

    def extract_valid_files_and_anchors(self, book):
        """Extract valid files and anchors from an EPUB book.

        Args:
            book (epub.EpubBook): EPUB book object.

        Returns:
            tuple: A set of valid files and a dictionary of file anchors.
        """
        valid_files = set()
        file_anchors = {}

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            filename = item.file_name.split("/")[-1]
            valid_files.add(filename)

            soup = BeautifulSoup(item.content, "html.parser")
            anchors = set(
                tag.get("id")
                for tag in soup.find_all(True, id=True)
                if isinstance(tag, bs4.element.Tag) and tag.get("id")
            )

            file_anchors[filename] = anchors

        return valid_files, file_anchors

    def parse_href(self, href, current_file):
        """Parse href into target_file and anchor, skip external or invalid links.

        Args:
            href (str): The href attribute value.
            current_file (str): The current file being processed.

        Returns:
            tuple: Target file and anchor, or None if href is external/invalid.
        """
        if not href:
            return None

        if isinstance(href, (list, tuple)):
            href = href[0]

        if not isinstance(href, str):
            return None

        if href.startswith(("http://", "https://", "mailto:")):
            return None

        if href.startswith("#"):
            target = current_file
            anchor = href[1:] if href != "#" else None
        else:
            parts = href.split("#", 1)
            target = parts[0].split("/")[-1]
            anchor = parts[1] if len(parts) == 2 else None

        return target, anchor

    def classify_broken_link(
        self, target_file, anchor, valid_files, file_anchors
    ):
        """Classify the type of broken link.

        Args:
            target_file (str): Target file.
            anchor (str): Anchor in the file.
            valid_files (set): Set of valid files.
            file_anchors (dict): Dictionary mapping files to sets of anchors.

        Returns:
            str: Classification of the broken link.
        """
        if target_file not in valid_files:
            return "MISSING_FILE"

        if anchor and anchor not in file_anchors.get(target_file, set()):
            return "MISSING_ANCHOR"

        return "VALID"

    def check_links(self):
        """Check all links in the EPUB file for broken links.

        Returns:
            dict: Statistics about the broken links.
        """
        book = self.load_epub()
        if not book:
            return {"success": False, "error": "Failed to load EPUB"}

        valid_files, file_anchors = self.extract_valid_files_and_anchors(book)
        self.logger.info(f"Found {len(valid_files)} valid files in EPUB")

        broken_links = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            current_file = item.file_name.split("/")[-1]
            soup = BeautifulSoup(item.content, "html.parser")

            for link in soup.find_all("a"):
                if not isinstance(link, bs4.element.Tag):
                    continue

                href = link.get("href")
                parsed_href = self.parse_href(href, current_file)

                if not parsed_href:
                    continue

                target_file, anchor = parsed_href
                status = self.classify_broken_link(
                    target_file, anchor, valid_files, file_anchors
                )

                if status == "MISSING_FILE":
                    self.num_missing_files += 1
                    broken_links.append(
                        {
                            "source": current_file,
                            "href": href,
                            "target": target_file,
                            "anchor": anchor,
                            "status": status,
                            "link_text": link.get_text(strip=True),
                        }
                    )
                elif status == "MISSING_ANCHOR":
                    self.num_missing_anchors += 1
                    broken_links.append(
                        {
                            "source": current_file,
                            "href": href,
                            "target": target_file,
                            "anchor": anchor,
                            "status": status,
                            "link_text": link.get_text(strip=True),
                        }
                    )
                else:
                    self.num_valid_links += 1

        self.num_broken_links = len(broken_links)

        # Log and return results
        self._log_results(broken_links)

        return {
            "success": True,
            "epub_file": self.epub_file_path,
            "log_file": self.log_file,
            "total_links": self.num_valid_links + self.num_broken_links,
            "valid_links": self.num_valid_links,
            "broken_links": self.num_broken_links,
            "missing_files": self.num_missing_files,
            "missing_anchors": self.num_missing_anchors,
        }

    def _log_results(self, broken_links):
        """Log the results of the link check.

        Args:
            broken_links (list): List of broken links.
        """
        self.logger.info(f"EPUB Link Check Results for {self.epub_file_path}")
        self.logger.info("=" * 80)
        self.logger.info(
            f"Total links checked: {self.num_valid_links + self.num_broken_links}"
        )
        self.logger.info(f"Valid links: {self.num_valid_links}")
        self.logger.info(f"Broken links: {self.num_broken_links}")
        self.logger.info(f"  - Missing files: {self.num_missing_files}")
        self.logger.info(f"  - Missing anchors: {self.num_missing_anchors}")
        self.logger.info("=" * 80)

        if broken_links:
            self.logger.info("\nDetailed Broken Links:")
            self.logger.info("-" * 80)

            for link in broken_links:
                self.logger.info(f"Source: {link['source']}")
                self.logger.info(f"Target: {link['href']}")
                self.logger.info(f"Link text: {link['link_text']}")
                self.logger.info(f"Issue: {link['status']}")
                self.logger.info("-" * 80)

        self.logger.info(f"\nResults saved to: {self.log_file}")
