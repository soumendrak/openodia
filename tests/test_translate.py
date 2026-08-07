"""
License: MIT
Author: Soumendra Kumar Sahoo
Tests the _translate module
"""

from unittest import mock

import pytest

from openodia import (
    cache,
    other_lang_to_odia,
    odia_to_other_lang,
    universal_translation,
    _translate,
)

# Canned replies from the translation service, keyed by (text, source, target).
# The real endpoint rate-limits CI runners and may change its wording for a given
# phrase at any time, so the tests below never talk to it.
FAKE_TRANSLATIONS: dict[tuple[str, str, str], str] = {
    # to Odia
    ("hello! feeling good?", "en", "or"): "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?",
    (
        "शेयर बाज़ार एक ऐसा बाज़ार है जहाँ कंपनियों के शेयर खरीदे-बेचे जा सकते हैं।",
        "hi",
        "or",
    ): "ଷ୍ଟକ୍ ମାର୍କେଟ୍ ହେଉଛି ଏକ ବଜାର ଯେଉଁଠାରେ କମ୍ପାନୀର ସେୟାରଗୁଡିକ କିଣାଯାଇ ବିକ୍ରି ହୋଇପାରିବ |",
    ("क्यों", "hi", "or"): "କାହିଁକି",
    # Odia to English
    ("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?", "or", "en"): "Hello! Sounds good?",
    ("କଣ", "or", "en"): "What",
    ("କାହିଁକି", "or", "en"): "Why",
    # Odia to Hindi
    ("କଣ", "or", "hi"): "क्या",
    ("କାହିଁକି", "or", "hi"): "क्यों",
}


def mock_get_dictionary():
    return {"watch": "ଦେଖନ୍ତୁ"}


@pytest.fixture(autouse=True)
def translation_calls():
    """Stand in for the live service and start each test with an empty cache.

    Yields the list of ``(text, source, target)`` requests the code under test
    made, so a test can assert how often the service was consulted.
    """
    cache.clear()
    calls: list[tuple[str, str, str]] = []

    class FakeGoogleTranslator:
        def __init__(self, source: str, target: str) -> None:
            self._source = source
            self._target = target

        def translate(self, text: str) -> str:
            calls.append((text, self._source, self._target))
            try:
                return FAKE_TRANSLATIONS[(text, self._source, self._target)]
            except KeyError:
                raise AssertionError(
                    f"No canned translation for {text!r} ({self._source} -> {self._target}). "
                    "Add one to FAKE_TRANSLATIONS rather than letting the suite call the live service."
                ) from None

    with mock.patch.object(_translate, "GoogleTranslator", FakeGoogleTranslator):
        yield calls

    cache.clear()


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

    @mock.patch.object(_translate, "get_dictionary", mock_get_dictionary)
    def test_offline_dictionary_hit_skips_the_service(self, translation_calls):
        """A word the offline dictionary knows is never sent to Google."""
        assert other_lang_to_odia("watch") == "ଦେଖନ୍ତୁ"
        assert translation_calls == []

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

    def test_repeated_request_is_served_from_the_cache(self, translation_calls):
        """The service is consulted once per phrase; the repeat hits the cache."""
        assert odia_to_other_lang("କଣ", "en") == "What"
        assert odia_to_other_lang("କଣ", "en") == "What"

        assert translation_calls == [("କଣ", "or", "en")]
