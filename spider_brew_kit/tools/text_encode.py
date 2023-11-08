from spider_brew_kit.contants import ENCODINGS


def fix_encode(garbled_text: str, decoding='utf-8', return_encoding=False):
    """
    修复乱码
    :param garbled_text: 乱码文本
    :param decoding: 解码方式
    :param return_encoding: 是否返回编码
    :return: 正常文本, 编码
    """
    for encoding in ENCODINGS:
        try:
            res = garbled_text.encode(encoding).decode(decoding)
            if return_encoding:
                return res, encoding
            else:
                return res
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
