"""python_docs_spider.py
This module defines a Scrapy spider to scrape Python documentation.
It extracts chapter information, including titles, URLs, and content,
and saves it in a structured format.
The spider starts from the main Python documentation page and follows
links to various sections, including the table of contents (TOC).
It uses BeautifulSoup to parse HTML content and extract relevant
information.
The spider also handles deduplication of URLs and content.
"""

import json
from urllib.parse import urljoin
import os
import hashlib
import scrapy
from scrapy.http.response import Response
from bs4 import BeautifulSoup, Tag


class PythonDocsSpider(scrapy.Spider):
    """Scrapy spider to scrape Python documentation.

    Returns:
        None: This spider does not return any values.

    Yields:
        dict: A dictionary containing chapter information.
    """

    name = "python_docs"
    allowed_domains = ["docs.python.org"]
    start_urls = ["https://docs.python.org/3/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapters = []
        self.visited_urls = {}
        # Change path to use backend structure
        outputs_path = os.path.join("backend", "outputs", "python_docs.jl")
        if os.path.exists(outputs_path):
            with open(outputs_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    content_hash = hashlib.md5(
                        item["content"].encode("utf-8")
                    ).hexdigest()
                    self.visited_urls[item["url"]] = content_hash
            self.logger.info(f"Loaded {len(self.visited_urls)} existing URLs")

    def parse(self, response: Response):
        """Parse the initial response and extract links to documentation pages.
        Args:
            response (Response): The response object from the initial request.
        Yields:
            scrapy.Request: A request to the next page to be scraped.
        """
        self.logger.info(f"Parsing: {response.url}")

        all_links = (
            response.css("div.sphinxsidebarwrapper a[href]")
            + response.css("table.contentstable a[href]")
            + response.css("div[role='main'] a[href]")
            + response.css("div.body a[href]")
            + response.css("nav a[href]")
        )

        for link in all_links:
            title = link.css("::text").get(default="Untitled").strip()
            relative_url = link.css("::attr(href)").get()
            if relative_url is not None and self._is_valid_link(relative_url):
                full_url = urljoin(response.url, relative_url)
                if full_url not in self.visited_urls:
                    priority = self.get_priority(title)
                    self.chapters.append(
                        {
                            "title": title,
                            "url": full_url,
                            "priority": priority,
                            "parent": None,
                        }
                    )
                    self.visited_urls[full_url] = None
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_content,
                        meta={"title": title, "priority": priority},
                    )

        toc_link = response.css("a[href='contents.html']::attr(href)").get()
        if toc_link:
            full_toc_url = urljoin(response.url, toc_link)
            if full_toc_url not in self.visited_urls:
                yield scrapy.Request(full_toc_url, callback=self.parse_toc)

    def parse_toc(self, response: Response):
        """Parse the table of contents (TOC) and extract links to chapters.
        Args:
            response (Response): The response object from the TOC request.
        Yields:
            scrapy.Request: A request to the next chapter to be scraped.
        """
        self.logger.info(f"Parsing TOC: {response.url}")
        toc_items = response.css("div.toctree-wrapper li[class^='toctree-l']")
        for item in toc_items:
            link = item.css("a")
            if not link:
                continue
            title = link.css("::text").get(default="Untitled").strip()
            rel_url = link.css("::attr(href)").get()
            if rel_url is None or not self._is_valid_link(rel_url):
                continue
            level = (
                int(item.attrib.get("class", "toctree-l1")[10:])
                if item.attrib.get("class", "").startswith("toctree-l")
                else 1
            )
            full_url = urljoin(response.url, rel_url)
            if full_url not in self.visited_urls:
                metadata = {
                    "title": title,
                    "level": level,
                    # Higher-level TOC entries get higher priority
                    "priority": 100
                    if level == 1
                    else (75 if level == 2 else 50),
                }
                self.chapters.append(
                    {
                        "title": title,
                        "url": full_url,
                        "priority": metadata["priority"],
                        "parent": None,
                        "level": level,
                    }
                )
                self.visited_urls[full_url] = None
                yield scrapy.Request(
                    url=full_url, callback=self.parse_content, meta=metadata
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
        main_content = soup.select_one("div.body") or soup.select_one(
            "div[role='main']"
        )
        if not main_content:
            self.logger.warning(f"No main content found in {response.url}")
            return None
        # Extract and store internal links
        internal_links = {}
        for link in main_content.find_all("a", class_="reference internal"):
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
            "level": response.meta.get("level", 1),
            "priority": response.meta.get("priority", 500),
            "internal_links": internal_links,
        }
        return item

    def _process_content(self, main_content):
        """Process content for better readability in eBook format.
        Args:
            main_content (bs4.element.Tag): BeautifulSoup Tag containing content
        """
        # Remove interactive elements that won't work in an eBook
        for element in main_content.select(
            ".viewcode-link, .headerlink, "
            "a.copybtn, div.footer, div.admonition-youtube"
        ):
            element.decompose()
        # Fix code blocks
        for pre in main_content.find_all("pre"):
            if isinstance(pre, Tag):
                pre.attrs["style"] = "white-space: pre-wrap;"
        # Optimize tables
        for table in main_content.find_all("table"):
            if isinstance(table, Tag):
                table.attrs["style"] = "width:100%; max-width:100%;"
        # Add heading IDs for internal linking
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for heading in main_content.find_all(tag_name):
                if isinstance(heading, Tag) and "id" not in heading.attrs:
                    text = heading.get_text(strip=True)
                    heading_id = text.lower().replace(" ", "-")
                    heading["id"] = heading_id

    def _is_valid_link(self, url):
        """Check if a URL is valid for scraping.
        Args:
            url (str): URL to check.
        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        if url.startswith(("mailto:", "javascript:", "#")):
            return False
        return not any(
            x in url
            for x in ["genindex", "search", "whatsnew", "_sources", "_static"]
        )

    def get_priority(self, title):
        """Assign priority based on the title.
        Args:
            title (str): Title to assign priority to.
        Returns:
            int: Priority value (lower is higher priority).
        """
        title = title.lower()
        # Front matter gets highest priority
        if any(
            x in title
            for x in [
                "preface",
                "about",
                "introduction",
                "foreword",
                "overview",
            ]
        ):
            return 10
        # Important concepts get high priority
        elif any(
            x in title
            for x in [
                "tutorial",
                "guide",
                "getting started",
                "install",
                "setup",
            ]
        ):
            return 20
        # Core language features
        elif any(
            x in title
            for x in [
                "syntax",
                "statement",
                "expression",
                "grammar",
                "type",
                "keyword",
                "variable",
                "class",
                "function",
                "object",
                "exception",
            ]
        ):
            return 30
        # Standard library
        elif "library" in title:
            return 40
        # Reference material
        elif "reference" in title:
            return 50
        # Low priority items
        elif any(
            x in title
            for x in ["glossary", "faq", "appendix", "copyright", "license"]
        ):
            return 900
        # Default priority
        return 100
