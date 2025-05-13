"""base_spider.py
This module defines a base spider class that can be extended to create
specific spiders for different documentation websites.
It provides common functionality and utility methods that can be reused.
"""

import json
import os
import hashlib
from urllib.parse import urljoin
from abc import ABC, abstractmethod

import scrapy
from scrapy.http.response import Response
from bs4 import Tag


class BaseDocSpider(scrapy.Spider, ABC):
    """Base class for documentation spiders.

    This abstract class provides common functionality for scraping documentation
    websites. Subclasses need to implement specific parsing logic.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapters = []
        self.visited_urls = {}
        # Set up output file path
        self.output_file = os.path.join(
            "backend", "outputs", f"{self.name}.jl"
        )

        # Load existing URLs for deduplication
        self._load_existing_urls()

    def _load_existing_urls(self):
        """Load existing URLs from output file to avoid duplicates."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    for line in f:
                        item = json.loads(line)
                        content_hash = hashlib.md5(
                            item["content"].encode("utf-8")
                        ).hexdigest()
                        self.visited_urls[item["url"]] = content_hash
                self.logger.info(
                    f"Loaded {len(self.visited_urls)} existing URLs"
                )
            except Exception as e:
                self.logger.error(f"Error loading existing URLs: {e}")

    @abstractmethod
    def parse(self, response: Response):
        """Parse the initial response and extract links to documentation pages.
        Args:
            response (Response): The response object from the initial request.
        Yields:
            scrapy.Request: A request to the next page to be scraped.
        """
        pass

    @abstractmethod
    def parse_content(self, response: Response):
        """Parse document content.
        Args:
            response (Response): The response object from a document request.
        Returns:
            dict: A dictionary containing chapter information.
        """
        pass

    def _process_content(self, main_content):
        """Process HTML content for better readability in eBook format.
        This method can be overridden by subclasses to implement
        site-specific content processing.

        Args:
            main_content (bs4.element.Tag): BeautifulSoup Tag containing content
        """
        # Add heading IDs for internal linking if not present
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for heading in main_content.find_all(tag_name):
                if isinstance(heading, Tag) and "id" not in heading.attrs:
                    text = heading.get_text(strip=True)
                    heading_id = text.lower().replace(" ", "-")
                    heading["id"] = heading_id

    def make_full_url(self, base_url, relative_url):
        """Create a full URL from a base and relative URL.

        Args:
            base_url (str): The base URL.
            relative_url (str): The relative URL.

        Returns:
            str: The full URL.
        """
        return urljoin(base_url, relative_url)

    @abstractmethod
    def _is_valid_link(self, url):
        """Check if a URL is valid for scraping.

        Args:
            url (str): URL to check.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        pass
