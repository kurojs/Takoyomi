import re

from n1_translator.app import RE_JAPANESE, RE_SPANISH


class TestJapaneseDetection:
    def test_hiragana(self):
        assert RE_JAPANESE.search("こんにちは")

    def test_katakana(self):
        assert RE_JAPANESE.search("コンピュータ")

    def test_kanji(self):
        assert RE_JAPANESE.search("勉強")

    def test_mixed_japanese(self):
        assert RE_JAPANESE.search("勉強しています")

    def test_english_only(self):
        assert not RE_JAPANESE.search("hello world")

    def test_spanish_only(self):
        assert not RE_JAPANESE.search("hola mundo")

    def test_empty(self):
        assert not RE_JAPANESE.search("")

    def test_numbers_only(self):
        assert not RE_JAPANESE.search("12345")


class TestSpanishDetection:
    def test_accent_e(self):
        assert RE_SPANISH.search("canción")

    def test_accent_a(self):
        assert RE_SPANISH.search("música")

    def test_ene(self):
        assert RE_SPANISH.search("mañana")

    def test_question_mark(self):
        assert RE_SPANISH.search("¿qué?")

    def test_exclamation(self):
        assert RE_SPANISH.search("¡hola!")

    def test_japanese_only(self):
        assert not RE_SPANISH.search("こんにちは")

    def test_english_only(self):
        assert not RE_SPANISH.search("hello world")

    def test_empty(self):
        assert not RE_SPANISH.search("")


class TestBidirectionalDetection:
    """Japanese and Spanish text should BOTH match their respective patterns."""

    def test_jp_and_es_combined(self):
        text = "日本語 español"
        assert RE_JAPANESE.search(text)
        assert RE_SPANISH.search(text)

    def test_jp_only_no_es(self):
        text = "元気ですか"
        assert RE_JAPANESE.search(text)
        assert not RE_SPANISH.search(text)

    def test_es_only_no_jp(self):
        text = "más o menos"
        assert not RE_JAPANESE.search(text)
        assert RE_SPANISH.search(text)
