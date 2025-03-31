# Scrapy settings for PythonDocs project

BOT_NAME = "PythonDocs"

SPIDER_MODULES = ["PythonDocs.spiders"]
NEWSPIDER_MODULE = "PythonDocs.spiders"

# Crawl responsibly by identifying yourself on the user-agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

# Obey robots.txt rules (set to False for docs.python.org)
ROBOTSTXT_OBEY = False

# Output to JSON Lines format
FEEDS = {
    "outputs/python_docs.jl": {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": True,  # Overwrite to ensure fresh data each run
    }
}

# Ensure file storage is used
FEED_STORAGES = {
    "file": "scrapy.extensions.feedexport.FileFeedStorage",
}

# Store crawl state
JOBDIR = "outputs/job_state"

# Limit crawl depth (optional, adjust as needed)
DEPTH_LIMIT = 10

# Configure maximum concurrent requests (reduced for politeness)
CONCURRENT_REQUESTS = 5

# Add a delay between requests
DOWNLOAD_DELAY = 1

# Set settings for modern Scrapy compatibility
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"