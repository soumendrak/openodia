"""Convert text typed in legacy 8-bit Odia fonts to Unicode Odia.

``openodia.legacy`` needs a release newer than 0.2.0: ``import openodia.legacy``
fails on 0.2.0.

``decode`` turns the bytes of text typed in an 8-bit Odia font into a string of
keystroke characters. Each defined byte uses cp1252. The five bytes that codec
leaves undefined, 0x81, 0x8D, 0x8F, 0x90 and 0x9D, stay as those code points.

``to_unicode`` converts those keystrokes to NFC Unicode Odia. ``SUPPORTED_FONTS``
is ``("ORTTSarala",)``. Output is NFC, so ଡ଼ is consonant plus nukta.

After the glyph table, ``to_unicode`` rebuilds each syllable in Unicode order: reph,
base consonant, subjoined forms in the order typed, vowel sign, then nasal or visarga. A
reph, vowel sign, nasal or visarga typed before a subjoined form gives the same output
as typed after it (``ÒLÕÔÍ`` and ``ÒLÔÍÕ`` both give ``କ୍ୟ୍ରେଂ``). A reph typed in a
syllable with no base consonant stays where it was typed. The left matra ``Ò``, typed
before the consonant, joins its right half ``ß``, ``×`` or ``Ð`` into ୈ, ୌ or ୋ wherever
that half is typed in the syllable (``ÒLàÔß`` and ``ÒLÔßà`` both give ``ର୍କ୍ୟୈ``). A
nukta, ``Ï`` or a Unicode ``଼``, goes right after the consonant typed last before it in
the same syllable, ahead of any halant or zero-width joiner, also when a vowel sign,
nasal, visarga or reph is typed in between (``XÐÏ`` and ``XÏÐ`` both give ``ଡ଼ା``). In a
syllable with no consonant, a nukta goes ahead of the vowel signs. A run of numeric
separators all convert (``1Ð2Ð3`` gives ``୧|୨|୩``).

Examples:
    >>> from openodia import legacy
    >>> legacy.decode(b"JX\\xcf\\x85")
    'JXÏ…'
    >>> legacy.decode(b"\\x8d")
    '\\x8d'
    >>> legacy.to_unicode(legacy.decode(b"JX\\xcf\\xdeA"), font="ORTTSarala")
    'ଓଡ଼ିଆ'
"""

from openodia.legacy._convert import SUPPORTED_FONTS, to_unicode
from openodia.legacy._decode import decode

__all__ = ["SUPPORTED_FONTS", "decode", "to_unicode"]
