"""Romanisation (Odia ↔ Latin script).

Examples:
    >>> from openodia import roman
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="ISO15919")
    'ōṛiā'
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="Hunterian")
    'oria'
    >>> roman.to_roman("ଓଡ଼ିଆ", scheme="ITRANS")
    'o.DiA'
"""

from openodia.roman._roman import SCHEMES, Scheme, from_roman, to_roman

__all__ = ["SCHEMES", "Scheme", "from_roman", "to_roman"]
