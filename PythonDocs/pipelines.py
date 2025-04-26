"""pipelines.py"""
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

class TukuybooksPipeline:
    """pipelines.py
    This file contains the pipeline for processing items
    scraped from Python documentation.
    It defines the TukuybooksPipeline class,
     which processes and stores the scraped data.
    """
    def __init__(self):
        """Initialize pipeline."""
        self.spider = None

    def process_item(self, item, _spider):
        """process_item
        This method processes each item scraped by the spider.
        It can be used to clean, validate, or store the item.
        """
        return item

    def open_spider(self, spider):
        """Called when the spider is opened.
        Stub to satisfy public method count."""
        self.spider = spider
