"""
License: MIT
Author: Soumendra Kumar Sahoo
Tests the _translate module
"""

from unittest import mock

import pytest

from openodia import (
    other_lang_to_odia,
    odia_to_other_lang,
    universal_translation,
    _translate,
)


def mock_get_dictionary():
    return {"watch": "ଦେଖନ୍ତୁ"}


class TestTranslate:
    @pytest.mark.parametrize(
        "source, text, output",
        [
            ("en", "hello! feeling good?", "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?"),
            ("en", "watch", "ଦେଖନ୍ତୁ"),
            (
                "hi",
                "शेयर बाज़ार एक ऐसा बाज़ार है जहाँ कंपनियों के शेयर खरीदे-बेचे जा सकते हैं।",
                "ଷ୍ଟକ୍ ମାର୍କେଟ୍ ହେଉଛି ଏକ ବଜାର ଯେଉଁଠାରେ କମ୍ପାନୀର ସେୟାରଗୁଡିକ କିଣାଯାଇ ବିକ୍ରି ହୋଇପାରିବ |",
            ),
        ],
    )
    @mock.patch.object(_translate, "get_dictionary", mock_get_dictionary)
    def test_other_lang_to_odia(self, source, text, output):
        """Test the other language to Odia Translation"""
        assert other_lang_to_odia(text, source_language_code=source) == output

    @pytest.mark.parametrize(
        "text, dest, output",
        [
            ("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?", "en", "Hello! Sounds good?"),
            ("କଣ", "en", "What"),
            ("କଣ", "hi", "क्या"),
        ],
    )
    def test_odia_to_other_lang(self, text, dest, output):
        """Test Odia to other language translation"""
        assert odia_to_other_lang(text, dest) == output

    @pytest.mark.parametrize(
        "text, output, src, dest",
        [
            ("hello! feeling good?", "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?", "en", "or"),
            ("क्यों", "କାହିଁକି", "hi", "or"),
            ("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?", "Hello! Sounds good?", "or", "en"),
            ("କାହିଁକି", "Why", "or", "en"),
            ("କାହିଁକି", "क्यों", "or", "hi"),
        ],
    )
    def test_universal_translation(self, text, output: str, src: str, dest: str):
        """Test the universal translation feature"""
        assert universal_translation(text, source_language_code=src, dest_language_code=dest) == output
