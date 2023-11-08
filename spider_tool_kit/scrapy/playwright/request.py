from playwright.async_api import Request


def is_image_request(request: Request):
    """
    判断是否是图片请求

    :param request:
    :return:
    """
    return request.resource_type == "image"


def is_media_request(request: Request):
    """
    判断是否是视频请求

    :param request:
    :return:
    """
    return request.resource_type == "media"


def is_image_or_media_request(request: Request):
    """
    判断是否是图片或者视频请求

    :param request:
    :return:
    """
    return request.resource_type in ["image", "media"]
