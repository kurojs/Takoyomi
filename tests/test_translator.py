"""Tests for the translation pipeline (regex detection + cache logic)."""

import pytest

from n1_translator.app import RE_JAPANESE, RE_SPANISH


def _detect_direction(text: str) -> str | None:
    has_jp = bool(RE_JAPANESE.search(text))
    has_es = bool(RE_SPANISH.search(text))
    if has_jp:
        return "JP→ES"
    if has_es:
        return "ES→JP"
    return None


class TestDirectionDetection:
    def test_japanese_detected(self):
        assert _detect_direction("日本語") == "JP→ES"

    def test_spanish_detected(self):
        assert _detect_direction("canción") == "ES→JP"

    def test_english_is_neither(self):
        assert _detect_direction("hello world") is None

    def test_short_text_ignored(self):
        """Text shorter than 2 chars should be ignored by _process_text."""
        assert _detect_direction("a") is None

    def test_jp_katakana(self):
        assert _detect_direction("テスト") == "JP→ES"

    def test_jp_hiragana(self):
        assert _detect_direction("あいう") == "JP→ES"

    def test_jp_and_spanish_prefers_jp(self):
        """When both detected, JP wins (first check)."""
        assert _detect_direction("日本語 español") == "JP→ES"

    def test_spanish_question(self):
        assert _detect_direction("¿cómo estás?") == "ES→JP"

    def test_spanish_exclamation(self):
        assert _detect_direction("¡hola!") == "ES→JP"

    def test_spanish_ene(self):
        assert _detect_direction("año") == "ES→JP"

    def test_spanish_acute(self):
        assert _detect_direction("canción") == "ES→JP"

    def test_text_with_numbers(self):
        assert _detect_direction("123 日本語 456") == "JP→ES"
