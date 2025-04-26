"""items.py
Define here the models for your scraped items.
See documentation in:
https://docs.scrapy.org/en/latest/topics/items.html
"""

import scrapy


class TukuybooksItem(scrapy.Item):
    """Define the fields for your item here."""
    title = scrapy.Field()
    author = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    publication_date = scrapy.Field()
    # define the fields for your item here like:
    # name = scrapy.Field()
