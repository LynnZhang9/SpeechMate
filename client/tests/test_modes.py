# client/tests/test_modes.py
"""Tests for language detection."""

import pytest
from client.modes import detect_language, get_target_lang, WorkMode


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detect_chinese_text(self):
        """纯中文文本应返回 'zh'"""
        assert detect_language("你好世界") == "zh"
        assert detect_language("这是一个测试") == "zh"

    def test_detect_english_text(self):
        """纯英文文本应返回 'en'"""
        assert detect_language("Hello World") == "en"
        assert detect_language("This is a test") == "en"

    def test_detect_mixed_text_chinese_dominant(self):
        """中文占比超过30%应返回 'zh'"""
        # 4个中文字符 / 10总字符 = 40%
        assert detect_language("你好世界Test") == "zh"

    def test_detect_mixed_text_english_dominant(self):
        """中文占比不超过30%应返回 'en'"""
        # 2个中文字符 / 10总字符 = 20%
        assert detect_language("Hi你好World") == "en"

    def test_detect_empty_text(self):
        """空文本应返回 'zh'（默认）"""
        assert detect_language("") == "zh"

    def test_detect_numbers_only(self):
        """纯数字应返回 'en'"""
        assert detect_language("123456") == "en"


class TestGetTargetLang:
    """Tests for get_target_lang function."""

    def test_chinese_to_english(self):
        """中文文本目标语言应为 'en'"""
        assert get_target_lang("你好世界") == "en"

    def test_english_to_chinese(self):
        """英文文本目标语言应为 'zh'"""
        assert get_target_lang("Hello World") == "zh"


class TestWorkMode:
    """Tests for WorkMode enum."""

    def test_work_mode_values(self):
        """验证枚举值"""
        assert WorkMode.TRANSCRIBE.value == "transcribe"
        assert WorkMode.TRANSLATE.value == "translate"
