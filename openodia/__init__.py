"""Open Odia language tools
"""
__version__ = "0.1.11"

from .common.constants import STOPWORDS
from ._letters import Letters as alphabet
from ._odianames import Names as name
from ._summarization import WordFrequency
from ._translate import odia_to_other_lang, other_lang_to_odia, universal_translation
from ._understandData import UnderstandData as ud

__all__ = [
    "alphabet",
    "name",
    "ud",
    "other_lang_to_odia",
    "odia_to_other_lang",
    "universal_translation",
    "WordFrequency",
]
