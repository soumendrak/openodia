"""
License: MIT
Author: Soumendra Kumar Sahoo
Google wrapper for odia language
"""

from deep_translator import GoogleTranslator

from openodia.cache import get_cache
from openodia.corpus.dictionary import get_dictionary


def _search_offline_dictionary(text: str) -> str:
    """Search the text from offline dictionary"""
    offline_dict = get_dictionary()
    translated_odia_text = offline_dict.get(text.lower())
    return translated_odia_text


def _hit_google_api(text: str, source_lang_code: str, destination_lang_code: str) -> str:
    """Translate text using Google Translate.

    Results are routed through :mod:`openodia.cache` so callers can resize,
    persist, or inspect the cache.
    """
    key = (text, source_lang_code, destination_lang_code)
    cache = get_cache()
    cached = cache.get(key)
    if cached is not None:
        return cached

    translator = GoogleTranslator(source=source_lang_code, target=destination_lang_code)
    result = translator.translate(text)
    cache.set(key, result)
    return result


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


def universal_translation(text: str, source_language_code: str = "en", dest_language_code: str = "or") -> str:
    """Translate from any language to any
    By default it works for English to Odia.
    Based on the source and destination language provided, it can work for any languages supported.
    """
    return _hit_google_api(text, source_language_code, dest_language_code)
