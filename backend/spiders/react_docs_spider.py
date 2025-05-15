"""react_docs_spider.py
This module defines a Scrapy spider to scrape React documentation.
It extracts chapter information, including titles, URLs, and content,
and saves it in a structured format for conversion into ebooks.
"""

import hashlib
import scrapy
from scrapy.http.response import Response
from bs4 import BeautifulSoup, Tag
from .base_spider import BaseDocSpider


class ReactDocsSpider(BaseDocSpider):
    """Scrapy spider to scrape React Documentation.

    This spider crawls the React documentation,
    extracting content for conversion to ebook formats.
    """

    name = "react_docs"
    allowed_domains = ["react.dev"]
    start_urls = [
        "https://react.dev/learn",
        "https://react.dev/reference/react",
        "https://react.dev/reference/react-dom",
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
            response.css("nav a[href]")
            + response.css("article a[href]")
            + response.css("main a[href]")
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

        Yields:
            dict: A dictionary containing chapter information.
        """
        self.logger.info(f"Parsing content: {response.url}")

        title = (
            response.meta.get("title")
            or response.css("h1::text").get(default="Untitled").strip()
        )

        # Create soup from response body
        soup = BeautifulSoup(response.body, "html.parser")

        # Main content selectors for React docs
        main_content = (
            soup.select_one("article")
            or soup.select_one("main div.prose")
            or soup.select_one("main[id='content']")
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

        # Yield the item so Scrapy can save it
        yield item

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

        # Only process React documentation
        if not any(path in url for path in ["/learn/", "/reference/"]):
            return False

        # Skip edit pages, blog entries, and other non-documentation pages
        if any(
            x in url
            for x in [
                "/blog/",
                "/community/",
                "github.com",
                "/docs/error-",
                "/playground",
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
        # Main learn pages get highest priority
        if "/learn/" in url:
            if "quick-start" in url or "tutorial" in url:
                return 50
            return 100

        # Core reference pages come next
        if "/reference/react" in url and "/reference/react-dom" not in url:
            return 200

        # React DOM reference pages
        if "/reference/react-dom" in url:
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
        # Remove domain part and split by slashes
        path = url.replace("https://react.dev", "")
        segments = [s for s in path.split("/") if s.strip()]

        # Calculate level based on path depth
        if len(segments) <= 1:
            return 1
        elif len(segments) == 2:
            return 2
        else:
            return 3
