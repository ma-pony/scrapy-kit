class ProxyConnectionCloseMiddleware:
    """
    Proxy close connection multiplexing middleware

    Tunnel Proxy Dynamic Edition request found that the number of requests in the Personal Centre Tunnel Proxy Usage Statistics is very small, which is seriously inconsistent with the real number of requests.
    Moreover, there is no IP change when using Tunnel Broker Dynamic Edition.
    The reason for this is that the tunnel sends requests that reuse previously established connections.
    You need to add Connection: close to the header.

    How to use it:
    1. Add in settings.py:
    DOWNLOADER_MIDDLEWARES = {
        'scrapy_kit.middlewares.ProxyConnectionCloseMiddleware': 543,
    }

    """  # noqa E501

    def process_request(self, request, spider):
        if request.meta.get("proxy", ""):
            request.headers["Connection"] = "close"
