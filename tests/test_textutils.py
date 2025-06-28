import pytest

from openodia import normalize_text, phonetic_odia


class TestTextUtils:
    def test_normalize_simple(self):
        assert normalize_text("Hello, World!") == "hello world"

    def test_normalize_odia_punctuation(self):
        assert normalize_text("ନମସ୍କାର!") == "ନମସ୍କାର"

    def test_normalize_none(self):
        assert normalize_text(None) == ""

    def test_phonetic_basic(self):
        assert phonetic_odia("ନମସ୍କାର") == "namaskaara"

    def test_phonetic_with_halant(self):
        assert phonetic_odia("ଜଗନ୍ନାଥ") == "jagannaatha"

    def test_phonetic_empty(self):
        assert phonetic_odia("") == ""

    def test_phonetic_none(self):
        assert phonetic_odia(None) == ""
