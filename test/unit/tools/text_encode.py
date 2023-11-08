from spider_tool_kit.tools import fix_encode


class TestTextEncode:
    def test_fix_encode(self):
        garbled_text = "äº¿å…ƒ"
        expected_text = "亿元"
        expected_encoding = "cp1252"
        result = fix_encode(garbled_text)
        assert result == (expected_text, expected_encoding)