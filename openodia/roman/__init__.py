"""Romanisation (Odia ↔ Latin script).

Examples:
    >>> from openodia import roman
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="ISO15919")
    'ōṛiā'
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="Hunterian")
    'oria'
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="ITRANS")
    'o.DiA'
    >>> roman.type_odia("namaskara")
    'ନମସ୍କାର'
"""

from openodia.roman._roman import SCHEMES, Scheme, from_roman, to_roman
from openodia.roman._typing import type_odia

__all__ = ["SCHEMES", "Scheme", "from_roman", "to_roman", "type_odia"]
