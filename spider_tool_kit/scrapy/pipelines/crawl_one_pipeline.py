import hashlib
import json
import logging

from scrapy import Spider, signals
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.settings import Settings
from scrapy.statscollectors import StatsCollector
from w3lib.url import canonicalize_url
logger = logging.getLogger(__name__)

from redis.client import Redis


class RedisCuckooFilter:
    def __init__(
            self,
            host: str,
            port: int,
            db: int,
            password: str,
            filter_key: str,
            capacity: int = 10_000,
    ):
        """
        基于redis的布谷鸟过滤器
        :param host:
        :param port:
        :param db:
        :param password:
        :param filter_key:  过滤器key
        :param capacity:  过滤器容量
        """
        self.redis_client = Redis(host=host, port=port, db=db, password=password)
        self.filter_key = filter_key
        self.capacity = capacity
        self.cuckoo_filter = self.redis_client.cf()

    def open(self):
        """
        测试连接并创建过滤器
        :return:
        """
        self.redis_client.ping()
        self.create(self.capacity)

    def close(self):
        """
        关闭连接
        :return:
        """
        self.redis_client.close()

    def create(
            self,
            capacity: int,
            expansion: int = None,
            bucket_size: int = None,
            max_iterations: int = None,
    ) -> int:
        """
        创建布谷鸟过滤器
        :param capacity:  容量
        过滤器的估计容量。容量四舍五入到下一个2^n数字。
        过滤器可能不会填满其容量的 100%。如果您想避免扩展，请确保预留额外的容量。
        :param expansion:  扩容
        创建新过滤器时，其大小为当前过滤器的大小乘以expansion，指定为非负整数。
        扩展四舍五入到下一个2^n数字。默认值为1。
        :param bucket_size:  桶大小
        每个桶中的物品数量。较高的存储桶大小值可提高填充率，
        但也会导致较高的错误率和稍慢的性能。默认值为 2。
        :param max_iterations:  最大迭代次数
        在声明过滤器已满并创建附加过滤器之前尝试在存储桶之间交换项目的次数。
        值越低，性能越好；数值越高，过滤器填充率越好。默认值为 20。
        :return:
        """
        if not self.redis_client.exists(self.filter_key):
            return self.cuckoo_filter.create(
                self.filter_key,
                capacity,
                expansion=expansion,
                bucket_size=bucket_size,
                max_iterations=max_iterations,
            )

    def insert(self, value: str) -> int:
        """
        插入数据
        :param value:
        :return:
        """
        return self.cuckoo_filter.addnx(self.filter_key, value)

    def exists(self, value: str) -> bool:
        """
        判断数据是否存在
        :param value:
        :return:
        """
        return self.cuckoo_filter.exists(self.filter_key, value)

    def delete(self, value: str) -> int:
        """
        删除数据
        :param value:
        :return:
        """
        return self.cuckoo_filter.delete(self.filter_key, value)

    def clear(self) -> int:
        """
        清空数据
        :return:
        """
        return self.redis_client.delete(self.filter_key)


class CrawlOnceMiddleware:
    """
    基于布谷鸟过滤器的去重中间件

    使用方法：
    1. 在项目的 settings.py 中启用中间件：

    SPIDER_MIDDLEWARES = {
        'spider_kit.middlewares.crawl_once_middleware.CrawlOnceMiddleware': 543,
    }

    DOWNLOADER_MIDDLEWARES = {
        'spider_kit.middlewares.crawl_once_middleware.CrawlOnceMiddleware': 543,
    }

    2. 在项目的 settings.py 配置：

    CRAWL_ONCE_ENABLED = True  # 是否启用去重中间件

    REDIS_HOST = localhost  # redis host

    REDIS_PORT = 6379  # redis port

    REDIS_PASSWORD = ''  # redis password

    REDIS_DB = '0'  # redis db

    REDIS_CUCKOO_FILTER_KEY_PREFIX = "cuckoo_filter"  # 布谷鸟过滤器key前缀

    REDIS_CUCKOO_FILTER_CAPACITY = 100_000_000  # 布谷鸟过滤器容量

    """

    def __init__(self, settings: Settings, stats: StatsCollector, spider: Spider):
        self.settings = settings
        self.stats = stats
        host = settings.get("REDIS_HOST", "localhost")
        port = settings.get("REDIS_PORT", "6379")
        db = settings.get("REDIS_DB", "0")
        password = settings.get("REDIS_PASSWORD", "")
        filter_key = (
            f"{settings.get('REDIS_CUCKOO_FILTER_KEY_PREFIX', 'cuckoo_filter')}"
            f":{spider.name}"
        )
        capacity = settings.getint("REDIS_CUCKOO_FILTER_CAPACITY", 100_000_000)

        self.cuckoo_filter = RedisCuckooFilter(
            host=host,
            port=port,
            db=db,
            password=password,
            filter_key=filter_key,
            capacity=capacity,
        )

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        if not settings.getbool("CRAWL_ONCE_ENABLED"):
            raise NotConfigured()
        middleware = cls(settings, crawler.stats, crawler.spider)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_spider_exception(self, response, exception, spider):
        """
        处理异常
        :param response:
        :param exception:
        :param spider:
        :return:
        """
        fingerprint = response.meta.get("fingerprint")
        # 如果抓取过程中发生异常，则删除过滤器中的数据，以便下次可以重新抓取
        if fingerprint and not isinstance(exception, IgnoreRequest):
            logger.info(f"Delete fingerprint: {fingerprint}")
            self.cuckoo_filter.delete(fingerprint)
        else:
            pass
        return None

    def spider_opened(self, spider):
        """
        爬虫启动时创建布谷鸟过滤器
        :param spider:
        :return:
        """
        self.cuckoo_filter.open()

    def spider_closed(self, spider):
        """
        爬虫关闭时关闭布谷鸟过滤器
        :param spider:
        :return:
        """
        self.cuckoo_filter.close()

    @staticmethod
    def request_fingerprint(request):
        """
        获取request的fingerprint
        :param request:
        :return:
        """

        def meta_fingerprint():
            """
            获取meta的fingerprint
            :return:
            """
            meta = request.meta or {}
            current_stage = meta.get("current_stage")
            return {
                "current_stage": current_stage,
            }

        def cb_kwargs_fingerprint():
            """
            获取cb_kwargs的fingerprint
            :return:
            """
            cb_kwargs = request.cb_kwargs or {}
            item = cb_kwargs.get("item", {})

            item_url = item.get("url")
            title = item.get("title")
            return {
                "item_url": canonicalize_url(item_url, keep_fragments=True)
                if item_url
                else "",
                "title": title,
            }

        fingerprint_data = {
            "url": canonicalize_url(request.url, keep_fragments=True),
            "method": request.method,
            "body": (request.body or b"").hex(),
            **meta_fingerprint(),
            **cb_kwargs_fingerprint(),
        }
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha1(fingerprint_json.encode()).hexdigest()

    def skip_filter(self, request, spider):
        """
        判断是否跳过过滤器
        :param request:
        :param spider:
        :return:
        """

        # 如果是重定向的请求，则跳过过滤器
        # 重定向请求的fingerprint与原始请求的fingerprint不同
        if request.meta.get("redirect_urls"):
            return True

        if request.meta.get("crawl_once"):
            return False

        return True

    def process_request(self, request, spider):
        if self.skip_filter(request, spider):
            return None

        fingerprint = self.request_fingerprint(request)

        # 设置request的fingerprint
        request.meta["fingerprint"] = fingerprint
        # 判断是否存在
        if self.cuckoo_filter.exists(fingerprint):
            self.stats.inc_value("crawled/filtered", spider=spider)
            logger.debug(
                f"Filtered duplicate request: {request} fingerprint: {fingerprint}"
            )
            raise IgnoreRequest(f"Filtered duplicate request: {request}")
        else:
            pass

    def process_response(self, request, response, spider):
        """
        处理响应
        :param request:
        :param response:
        :param spider:
        :return:
        """
        if self.skip_filter(request, spider):
            return response
        fingerprint = request.meta.get("fingerprint")
        # 如果抓取成功，则插入布谷鸟过滤器
        if fingerprint and 300 >= response.status >= 200:
            # 插入数据
            logger.info(f"Insert fingerprint: {fingerprint}")
            self.cuckoo_filter.insert(fingerprint)
        elif fingerprint and response.status >= 300:
            # 如果抓取失败，则删除布谷鸟过滤器中的数据，以便下次可以重新抓取
            logger.info(f"Delete fingerprint: {fingerprint}")
            self.cuckoo_filter.delete(fingerprint)
        else:
            pass
        return response

    def process_exception(self, request, exception, spider):
        fingerprint = request.meta.get("fingerprint")
        # 如果抓取过程中发生异常，则删除过滤器中的数据，以便下次可以重新抓取
        if fingerprint and not isinstance(exception, IgnoreRequest):
            logger.info(f"Delete fingerprint: {fingerprint}")
            self.cuckoo_filter.delete(fingerprint)
        else:
            pass
