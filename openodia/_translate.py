"""
License: MIT
Author: Soumendra Kumar Sahoo
Google wrapper for odia language
"""
from googletrans import Translator


def other_lang_to_odia(text: str, source_language_code: str = "en") -> str:
    """Translate from English to Odia language"""
    translator = Translator()
    return translator.translate(text, src=source_language_code, dest="or").text


def odia_to_other_lang(text: str, dest_language_code: str = "en") -> str:
    """Translate from Odia to other language"""
    translator = Translator()
    return translator.translate(text, src="or", dest=dest_language_code).text


def universal_translation(
    text: str, source_language_code: str = "en", dest_language_code: str = "or"
) -> str:
    """Translate from any language to any
    By default it works for English to Odia.
    Based on the source and destination language provided, it can work for any languages supported.
    """
    translator = Translator()
    return translator.translate(text, src=source_language_code, dest=dest_language_code).text
