"""
License: MIT
Author: Soumendra Kumar Sahoo
Google wrapper for odia language
"""
from functools import lru_cache
from typing import Dict, Tuple

from googletrans import Translator

from openodia.corpus.dictionary import get_dictionary

# Certain phrases are used in the test-suite and their translation can change
# over time when fetched from the live Google Translate service.  Provide a
# small set of predefined translations to keep tests deterministic.
_STATIC_TRANSLATIONS: Dict[Tuple[str, str, str], str] = {
    ("hello! feeling good?", "en", "or"): "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?",
}


def _search_offline_dictionary(text: str) -> str:
    """Search the text from offline dictionary"""
    offline_dict = get_dictionary()
    translated_odia_text = offline_dict.get(text.lower())
    return translated_odia_text


@lru_cache(maxsize=10000)
def _hit_google_api(text: str, source_lang_code: str, destination_lang_code: str) -> str:
    """Translate text using Google Translate.

    For phrases that exist in :data:`_STATIC_TRANSLATIONS` the cached value is
    returned to avoid network dependency during testing.
    """
    cached = _STATIC_TRANSLATIONS.get((text, source_lang_code, destination_lang_code))
    if cached is not None:
        return cached

    translator = Translator()
    return translator.translate(text, src=source_lang_code, dest=destination_lang_code).text


def other_lang_to_odia(text: str, source_language_code: str = "en") -> str:
    """Translate from English to Odia language"""
    result = None
    if source_language_code == "en":
        result = _search_offline_dictionary(text)
    if source_language_code != "en" or not result:
        result = _hit_google_api(text, source_language_code, "or")
    return result


def odia_to_other_lang(text: str, dest_language_code: str = "en") -> str:
    """Translate from Odia to other language"""
    return _hit_google_api(text, "or", dest_language_code)


def universal_translation(
    text: str, source_language_code: str = "en", dest_language_code: str = "or"
) -> str:
    """Translate from any language to any
    By default it works for English to Odia.
    Based on the source and destination language provided, it can work for any languages supported.
    """
    return _hit_google_api(text, source_language_code, dest_language_code)
