"""Open Odia language tools
"""
__version__ = "0.0.12"

from .letters import Letters as alphabet
from .odianames import Names as name
from .odiatokenizer import Tokenizer as tokenizer

__all__ = ["alphabet", "name", "tokenizer"]
