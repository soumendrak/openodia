import re
from typing import Any, Dict, List, Union

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
        token_list: List[str] = cls.word_tokenizer(text)
        cleaned_tokens = [token for token in token_list if token not in STOPWORDS]
        return " ".join(cleaned_tokens) if get_str else cleaned_tokens

    @classmethod
    def detect_language(cls, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """Detect language if it is Odia or non-Odia
        :param text: text to detect language
        :param threshold: confidence score which if crossed will be determined as Odia
        """
        if len(text) == 0:
            print("No text detected")
            return {}
        space_removed_text = text.replace(" ", "")
        odia_text = "".join(
            [letter for letter in space_removed_text if ord(letter) in range(2817, 2931)]
        )
        score = len(odia_text) / len(space_removed_text)
        language = "odia" if score > threshold else "non-odia"
        confidence_score = score if language == "odia" else 1 - score
        return {"language": language, "confidence_score": confidence_score}
