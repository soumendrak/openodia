"""
License: MIT
Author: Soumendra Kumar Sahoo
Google wrapper for odia language
"""
from functools import lru_cache

from googletrans import Translator

from openodia.corpus.dictionary import get_dictionary


@lru_cache(maxsize=1000)
def other_lang_to_odia(text: str, source_language_code: str = "en") -> str:
    """Translate from English to Odia language"""
    if source_language_code == "en":
        offline_dict = get_dictionary()
        translated_odia_text = offline_dict.get(text.lower())
        if translated_odia_text:
            return translated_odia_text
    # switch to online google translate mode if not found in offline corpus
    translator = Translator()
    return translator.translate(text, src=source_language_code, dest="or").text


@lru_cache(maxsize=1000)
def odia_to_other_lang(text: str, dest_language_code: str = "en") -> str:
    """Translate from Odia to other language"""
    translator = Translator()
    return translator.translate(text, src="or", dest=dest_language_code).text


@lru_cache(maxsize=1000)
def universal_translation(
    text: str, source_language_code: str = "en", dest_language_code: str = "or"
) -> str:
    """Translate from any language to any
    By default it works for English to Odia.
    Based on the source and destination language provided, it can work for any languages supported.
    """
    translator = Translator()
    return translator.translate(text, src=source_language_code, dest=dest_language_code).text
