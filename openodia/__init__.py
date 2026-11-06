"""Open Odia language tools"""

__version__ = "0.1.14"

from . import cache
from .common.constants import STOPWORDS
from ._letters import Letters as alphabet
from ._odianames import Names as name
from ._summarization import WordFrequency
from ._translate import odia_to_other_lang, other_lang_to_odia, universal_translation
from ._translate_async import (
    odia_to_other_lang_async,
    other_lang_to_odia_async,
    translate_batch,
    universal_translation_async,
)
from ._understandData import UnderstandData as ud
from . import numbers
from . import syllable
from .segment import sentences
from .stats import FreqDist, collocations, cooccurrence, ngrams
from .stopwords import Stopwords
from .text import clean, normalize

__all__ = [
    "alphabet",
    "cache",
    "clean",
    "collocations",
    "cooccurrence",
    "FreqDist",
    "name",
    "ngrams",
    "normalize",
    "numbers",
    "odia_to_other_lang",
    "odia_to_other_lang_async",
    "other_lang_to_odia",
    "other_lang_to_odia_async",
    "sentences",
    "STOPWORDS",
    "Stopwords",
    "syllable",
    "translate_batch",
    "ud",
    "universal_translation",
    "universal_translation_async",
    "WordFrequency",
]
