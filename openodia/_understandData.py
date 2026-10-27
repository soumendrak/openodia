import re
from collections.abc import Container
from typing import Any, Literal, overload

from openodia.common.constants import STOPWORDS
from openodia.common.utility import LOGGER

# Odia Unicode block range (U+0B01 to U+0B72)
ODIA_UNICODE_START = 0x0B01  # 2817
ODIA_UNICODE_END = 0x0B72  # 2930

_SENTENCE = re.compile(
    r"""(?: [^।॥?!]+ | [?!](?=[A-Za-z0-9=&%\#/_]) )*
        (?: [।॥?!]+ [)\]}>"'”’»›]* | \Z )""",
    re.VERBOSE,
)
_WORD = re.compile(r"[^\W_]")


class UnderstandData:
    """Tokenizer implementation"""

    @classmethod
    def word_tokenizer(cls, text: str) -> list[str]:
        """Split the text into words"""
        # TODO: Do not remove the punctuation characters
        token_list = [
            token for token in re.split(r"[!\"#$%&\'()*+,-./:;<=>?@[\\\]\^\_`{|}~୲—\s+]", text, flags=re.UNICODE) if token
        ]
        return token_list

    @classmethod
    def sentence_tokenizer(cls, text: str) -> list[str]:
        """Split the text into sentences at ।, ॥, ? and !, keeping each terminator."""
        sent_list: list[str] = []
        stray: list[str] = []
        for match in _SENTENCE.finditer(text):
            part = match.group().strip()
            if not _WORD.search(part):
                stray.append("".join(part.split()))
                continue
            if sent_list:
                sent_list[-1] += "".join(stray)
            elif stray:
                part = f"{''.join(stray)} {part}"
            sent_list.append(part)
            stray.clear()
        if sent_list:
            sent_list[-1] += "".join(stray)
        LOGGER.debug(f"{len(sent_list)} sentences have been formed.")
        return sent_list

    @overload
    @classmethod
    def remove_stopwords(
        cls,
        text: str | list[str],
        get_str: Literal[False] = False,
        stopwords: Container[str] | None = None,
    ) -> list[str]: ...

    @overload
    @classmethod
    def remove_stopwords(
        cls,
        text: str | list[str],
        get_str: Literal[True],
        stopwords: Container[str] | None = None,
    ) -> str: ...

    @overload
    @classmethod
    def remove_stopwords(
        cls,
        text: str | list[str],
        get_str: bool,
        stopwords: Container[str] | None = None,
    ) -> list[str] | str: ...

    @classmethod
    def remove_stopwords(
        cls,
        text: str | list[str],
        get_str: bool = False,
        stopwords: Container[str] | None = None,
    ) -> list[str] | str:
        """Remove frequently used words from the text.

        :param text: It can take both tokens and text string as input.
        :param get_str: Whether the output should be a single string instead
            of a list of tokens.
        :param stopwords: Optional custom container. Anything that supports
            ``token in stopwords`` works — :class:`openodia.Stopwords`,
            ``frozenset[str]``, ``set[str]``, ``list[str]``, etc. Defaults
            to the bundled :data:`openodia.STOPWORDS`.
        """
        if stopwords is None:
            stopwords = STOPWORDS
        token_list: list[str] = cls.word_tokenizer(text) if isinstance(text, str) else text
        cleaned_tokens = [token for token in token_list if token not in stopwords]
        return " ".join(cleaned_tokens) if get_str else cleaned_tokens

    @classmethod
    def detect_language(cls, text: str, threshold: float = 0.5) -> dict[str, Any]:
        """Detect language if it is Odia or non-Odia
        :param text: text to detect language
        :param threshold: confidence score which if crossed will be determined as Odia
        """
        if len(text) == 0:
            LOGGER.warning("No text detected")
            return {}
        space_removed_text = text.replace(" ", "")
        odia_text = "".join(letter for letter in space_removed_text if ODIA_UNICODE_START <= ord(letter) <= ODIA_UNICODE_END)
        score = len(odia_text) / len(space_removed_text)
        language = "odia" if score > threshold else "non-odia"
        confidence_score = score if language == "odia" else 1 - score
        return {"language": language, "confidence_score": round(confidence_score, 2)}
