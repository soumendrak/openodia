"""Open Odia language tools
"""
__version__ = "0.0.14"

from ._letters import Letters as alphabet
from ._odianames import Names as name
from ._understandData import UnderstandData as UD
from ._translate import odia_to_other_lang, other_lang_to_odia, universal_translation

__all__ = ["alphabet", "name", "UD", "other_lang_to_odia", "odia_to_other_lang", "universal_translation"]
