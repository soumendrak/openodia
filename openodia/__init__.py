"""Open Odia language tools
"""
__version__ = "0.0.13"

from .letters import Letters as alphabet
from .odianames import Names as name
from .understandData import UnderstandData as UD

__all__ = ["alphabet", "name", "UD"]
