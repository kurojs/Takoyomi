"""Tests for the translation pipeline (regex detection + cache logic)."""

import pytest

from takoyomi.app import RE_JAPANESE, RE_SPANISH


def _detect_has_jp(text: str) -> bool:
    return bool(RE_JAPANESE.search(text))


class TestDirectionDetection:
    def test_japanese_detected(self):
        assert _detect_has_jp("日本語") is True

    def test_spanish_not_jp(self):
        assert _detect_has_jp("canción") is False

    def test_english_not_jp(self):
        assert _detect_has_jp("hello world") is False

    def test_jp_katakana(self):
        assert _detect_has_jp("テスト") is True

    def test_jp_hiragana(self):
        assert _detect_has_jp("あいう") is True

    def test_empty(self):
        assert _detect_has_jp("") is False

    def test_numbers_only(self):
        assert _detect_has_jp("12345") is False

    def test_text_with_numbers_and_jp(self):
        assert _detect_has_jp("123 日本語 456") is True
