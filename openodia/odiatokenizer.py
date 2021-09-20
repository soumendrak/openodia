import re


class Tokenizer:
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
