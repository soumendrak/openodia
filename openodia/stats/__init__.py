"""Corpus statistics utilities.

Examples:
    >>> from openodia import FreqDist, ngrams, collocations, cooccurrence
    >>> tokens = ["ରାମ", "ସୀତା", "ରାମ", "ଲକ୍ଷ୍ମଣ"]
    >>> FreqDist(tokens).most_common(2)
    [('ରାମ', 2), ('ସୀତା', 1)]
    >>> list(ngrams(tokens, 2))
    [('ରାମ', 'ସୀତା'), ('ସୀତା', 'ରାମ'), ('ରାମ', 'ଲକ୍ଷ୍ମଣ')]
"""

from openodia.stats._stats import (
    FreqDist,
    collocations,
    cooccurrence,
    ngrams,
)

__all__ = ["FreqDist", "collocations", "cooccurrence", "ngrams"]
