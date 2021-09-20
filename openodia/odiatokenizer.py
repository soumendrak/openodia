import re
from typing import List, Union

from openodia.constants import STOPWORDS


class UnderstandData:
    """Tokenizer implementation"""

    @classmethod
    def word_tokenizer(cls, text):
        """Split the text into words"""
        # TODO: Do not remove the punctuation characters
        token_list = [
            token
            for token in re.split(
                r"[!\"#$%&\'()*+,-./:;<=>?@[\\\]\^\_`{|}~୲—\s+]", text, flags=re.UNICODE
            )
            if token
        ]
        return token_list

    @classmethod
    def sentence_tokenizer(cls, text):
        """Split the text into sentences"""
        raise NotImplementedError("Not implemented yet. Will be implemented soon!")

    @classmethod
    def remove_stopwords(cls, text: str, get_str: bool = False) -> Union[List[str], str]:
        """Remove frequently used words from the text"""
        token_list : List[str] = cls.word_tokenizer(text)
        cleaned_tokens = [token for token in token_list if token not in STOPWORDS]
        return " ".join(cleaned_tokens) if get_str else cleaned_tokens
