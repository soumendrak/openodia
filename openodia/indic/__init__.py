"""Script-only transliteration between Indic Brahmic scripts.

Examples:
    >>> from openodia import indic
    >>> indic.transliterate("ଓଡ଼ିଆ", from_script="odia", to_script="devanagari")
    'ओड़िआ'
    >>> indic.transliterate("भारत", from_script="devanagari", to_script="odia")
    'ଭାରତ'
"""

from openodia.indic._indic import SCRIPTS, Script, transliterate

__all__ = ["SCRIPTS", "Script", "transliterate"]
