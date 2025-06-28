"""Simple rule-based stemmer for Odia language."""

from typing import Iterable, List

from ._understandData import UnderstandData as ud

# Common Odia suffixes that can be stripped to obtain a crude stem
_SUFFIXES = [
    "ମାନେ",
    "ମାନଙ୍କର",
    "ମାନଙ୍କ",
    "ମାନ",
    "ଗୁଡ଼ିକ",
    "ଗୁଡିକ",
    "ଗୁଡ଼ିକର",
    "ଗୁଡିକର",
    "ଇବା",
    "ଇଲା",
    "ଇଲେ",
    "ଲା",
    "ଲେ",
    "ନ୍ତି",
    "ନ୍ତୁ",
    "ଟି",
    "ଟୀ",
    "କୁ",
    "ରୁ",
    "ରେ",
    "ର",
]


def stem_word(word: str) -> str:
    """Return a crude stem for a single word.

    The algorithm naively strips a set of known suffixes. If none of the
    suffixes match the input word, it is returned unchanged.
    """
    for suf in sorted(_SUFFIXES, key=len, reverse=True):
        if word.endswith(suf) and len(word) > len(suf):
            return word[: -len(suf)]
    return word


def stem_words(words: Iterable[str]) -> List[str]:
    """Stem each token from an iterable of words."""
    return [stem_word(w) for w in words]


def stem_text(text: str) -> str:
    """Stem all words in a string and return a whitespace joined string."""
    tokens = ud.word_tokenizer(text)
    stemmed = stem_words(tokens)
    return " ".join(stemmed)
