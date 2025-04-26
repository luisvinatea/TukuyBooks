"""middlewares.py"""
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals


class TukuybooksSpiderMiddleware:
    """This is a sample spider middleware.
    You can find more info here:
    https://docs.scrapy.org/en/latest/topics/spider-middleware.html
    """
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        """This method is used by Scrapy to create your spiders.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, _response, _spider):
        """Called for each response that goes through the spider
        middleware and into the spider.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, _response, result, _spider):
        """Called with the results returned from the Spider, after
        it has processed the response.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """

        # Must return an iterable of Request, or item objects.
        yield from result

    def process_spider_exception(self, _response, _exception, _spider):
        """Called when a spider or process_spider_input() method
        (from other spider middleware) raises an exception.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """

        # Should return either None or an iterable of Request or item objects.
        return None

    def process_start_requests(self, start_requests, _spider):
        """Called with the start requests of the spider, and works
        similarly to the process_spider_output() method, except
        that it doesn’t have a response associated.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """

        # Must return only requests (not items).
        yield from start_requests

    def spider_opened(self, spider):
        """Called when the spider is opened.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """

        spider.logger.info(f"Spider opened: {spider.name}")


class TukuybooksDownloaderMiddleware:
    """This is a sample downloader middleware.
    You can find more info here:
    https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
    """
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        """This method is used by Scrapy to create your spiders.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
        """
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, _request, _spider):
        """Called for each request that goes through the downloader
        middleware.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
        """
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, _request, response, _spider):
        """Called with the response returned from the downloader.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
        """
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, _request, _exception, _spider):
        """Called when a download handler or a process_request()
        (from other downloader middleware) raises an exception.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
        """
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        return None

    def spider_opened(self, spider):
        """Called when the spider is opened.
        You can find more info here:
        https://docs.scrapy.org/en/latest/topics/spider-middleware.html
        """
        spider.logger.info(f"Spider opened: {spider.name}")
