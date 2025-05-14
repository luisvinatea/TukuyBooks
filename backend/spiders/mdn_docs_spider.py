"""mdn_docs_spider.py
This module defines a Scrapy spider to scrape MDN Web Docs for JavaScript.
It extracts chapter information, including titles, URLs, and content,
and saves it in a structured format for conversion into ebooks.
"""

import hashlib
import scrapy
from scrapy.http.response import Response
from bs4 import BeautifulSoup, Tag
from .base_spider import BaseDocSpider


class MDNDocsSpider(BaseDocSpider):
    """Scrapy spider to scrape MDN Web Documentation for JavaScript.

    This spider crawls the MDN Web Docs JavaScript documentation,
    extracting content for conversion to ebook formats.
    """

    name = "mdn_docs"
    allowed_domains = ["developer.mozilla.org"]
    start_urls = [
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, response: Response):
        """Parse the initial response and extract links to documentation pages.

        Args:
            response (Response): The response object from the initial request.

        Yields:
            scrapy.Request: A request to the next page to be scraped.
        """
        self.logger.info(f"Parsing: {response.url}")

        # Select links from the sidebar navigation and main content
        all_links = (
            response.css("nav.sidebar a[href]")
            + response.css("article.main-page-content a[href]")
            + response.css("article#content a[href]")
            + response.css("div.article a[href]")
            + response.css("main#content a[href]")
        )

        for link in all_links:
            title = link.css("::text").get(default="").strip()
            if not title:
                title = link.xpath(".//text()").get(default="Untitled").strip()

            relative_url = link.css("::attr(href)").get()

            if relative_url is not None and self._is_valid_link(relative_url):
                full_url = self.make_full_url(response.url, relative_url)

                # Skip URLs we've already processed
                if full_url not in self.visited_urls:
                    # Determine priority based on URL path segments
                    priority = self._get_priority(full_url, title)

                    self.visited_urls[full_url] = None
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_content,
                        meta={
                            "title": title,
                            "priority": priority,
                            "parent": response.url,
                        },
                    )

    def parse_content(self, response: Response):
        """Parse document content.

        Args:
            response (Response): The response object from a document request.

        Returns:
            dict: A dictionary containing chapter information.
        """
        self.logger.info(f"Parsing content: {response.url}")

        title = (
            response.meta.get("title")
            or response.css("h1::text").get(default="Untitled").strip()
        )

        # Create soup from response body
        soup = BeautifulSoup(response.body, "html.parser")

        # Main content selectors - try different ones used in MDN
        main_content = (
            soup.select_one("article.main-page-content")
            or soup.select_one("article#content")
            or soup.select_one("div.article")
            or soup.select_one("main#content")
        )

        if not main_content:
            self.logger.warning(f"No main content found in {response.url}")
            return None

        # Extract and store internal links for cross-referencing
        internal_links = {}
        for link in main_content.find_all("a"):
            if isinstance(link, Tag) and "href" in link.attrs:
                href = link.attrs["href"]
                text = link.get_text(strip=True)
                if text and href:
                    internal_links[href] = text

        # Process content for better readability
        self._process_content(main_content)
        content = str(main_content)

        # Check if we've already seen this content
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        if (
            response.url in self.visited_urls
            and self.visited_urls[response.url] == content_hash
        ):
            self.logger.info(f"Skipping duplicate content at {response.url}")
            return None

        self.visited_urls[response.url] = content_hash

        # Create item with chapter details
        item = {
            "title": title,
            "url": response.url,
            "content": content,
            "parent": response.meta.get("parent"),
            "level": self._determine_level(response.url),
            "priority": response.meta.get("priority", 500),
            "internal_links": internal_links,
        }

        return item

    def _is_valid_link(self, url):
        """Check if a URL is valid for scraping.

        Args:
            url (str): URL to check.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        # Skip fragment-only URLs
        if url.startswith("#"):
            return False

        # Skip external URLs
        if url.startswith(("http://", "https://")):
            if not any(domain in url for domain in self.allowed_domains):
                return False

        # Only process JavaScript documentation
        if "/docs/Web/JavaScript/" not in url:
            return False

        # Skip edit, revision history, and contributor pages
        if any(
            x in url
            for x in [
                "$edit",
                "$history",
                "contributors.txt",
                "/tag/",
                "/docs/MDN/",
                "/docs/Learn/",
            ]
        ):
            return False

        return True

    def _get_priority(self, url, title):
        """Determine priority based on URL structure and title.

        Args:
            url (str): URL of the page.
            title (str): Title of the page.

        Returns:
            int: Priority value (lower is higher priority).
        """
        # Main guide pages get highest priority
        if "/Guide/" in url:
            return 100

        # Reference pages come next
        if "/Reference/" in url:
            return 200

        # Built-in objects are important
        if "/Global_Objects/" in url:
            return 300

        # Default priority
        return 500

    def _determine_level(self, url):
        """Determine chapter level based on URL depth.

        Args:
            url (str): URL of the page.

        Returns:
            int: Level value (1 is top level, higher numbers are deeper nesting).
        """
        # Check URL depth to determine nesting level
        path = (
            url.split("/docs/Web/JavaScript/")[1]
            if "/docs/Web/JavaScript/" in url
            else ""
        )
        segments = [s for s in path.split("/") if s.strip()]

        if len(segments) <= 1:
            return 1
        elif len(segments) == 2:
            return 2
        else:
            return 3
