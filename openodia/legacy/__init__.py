"""Convert legacy 8-bit Odia fonts to Unicode Odia.

Output is NFC. ଡ଼ and ଢ଼ stay consonant plus nukta, which is the
NFC spelling of those letters.

A left matra is typed before the consonant in these fonts and is moved to the
end of that conjunct.

Examples:
    >>> from openodia import legacy
    >>> legacy.to_unicode("IWÿò@û", font="AkrutiOriSarala")
    'ଓଡ଼ିଆ'
    >>> legacy.to_unicode("JXÏÞA", font="ORTTSarala")
    'ଓଡ଼ିଆ'
"""

from openodia.legacy._convert import SUPPORTED_FONTS, detect_font, to_unicode, to_unicode_auto

__all__ = ["SUPPORTED_FONTS", "detect_font", "to_unicode", "to_unicode_auto"]
