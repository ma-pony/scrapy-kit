from spider_brew_kit.contants import ENCODINGS


def fix_encode(garbled_text: str, decoding='utf-8') -> (str, str):
    """
    修复乱码
    :param garbled_text: 乱码文本
    :param decoding: 解码方式
    :return: 正常文本, 编码
    """
    for encoding in ENCODINGS:
        try:
            res = garbled_text.encode(encoding).decode(decoding)
            return res, encoding
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
