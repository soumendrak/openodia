"""Convert legacy 8-bit Odia fonts to Unicode Odia.

Decode the font bytes with ``decode``. Output is NFC. ଡ଼ and ଢ଼ stay
consonant plus nukta, which is the NFC spelling of those letters.

After the glyph table, each syllable is rebuilt in Unicode order: reph (when
the base is a consonant), the base letter, its subjoined forms in the order typed, the vowel sign, then the
nasal or visarga. A left matra is typed before the consonant in these fonts
and joins its right half wherever that half is typed in the syllable.
An ORTT nukta (Ï) or a Unicode nukta joins the consonant typed last before it
in the same syllable, right after that consonant and ahead of any halant or
zero-width joiner, also across a vowel sign, nasal, visarga or reph typed in
between. An AkrutiOriSarala ÿ typed after a vowel sign or nasal stays as typed.

Examples:
    >>> from openodia import legacy
    >>> legacy.to_unicode("IWÿò@û", font="AkrutiOriSarala")
    'ଓଡ଼ିଆ'
    >>> legacy.to_unicode("JXÏÞA", font="ORTTSarala")
    'ଓଡ଼ିଆ'
"""

from openodia.legacy._convert import SUPPORTED_FONTS, decode, detect_font, to_unicode, to_unicode_auto

__all__ = ["SUPPORTED_FONTS", "decode", "detect_font", "to_unicode", "to_unicode_auto"]
