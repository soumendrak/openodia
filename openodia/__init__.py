"""Open Odia language tools"""

__version__ = "0.1.12"

from .common.constants import STOPWORDS
from ._letters import Letters as alphabet
from ._odianames import Names as name
from ._summarization import WordFrequency
from ._translate import odia_to_other_lang, other_lang_to_odia, universal_translation
from ._understandData import UnderstandData as ud
from .stats import FreqDist, collocations, cooccurrence, ngrams
from .stopwords import Stopwords
from .text import clean, normalize

__all__ = [
    "alphabet",
    "clean",
    "collocations",
    "cooccurrence",
    "FreqDist",
    "name",
    "ngrams",
    "normalize",
    "odia_to_other_lang",
    "other_lang_to_odia",
    "STOPWORDS",
    "Stopwords",
    "ud",
    "universal_translation",
    "WordFrequency",
]
