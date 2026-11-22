"""Read legacy 8-bit Odia font bytes.

``decode`` turns the bytes of text typed in an 8-bit Odia font into a string of
keystroke characters. Each defined byte uses cp1252. The five bytes that codec
leaves undefined, 0x81, 0x8D, 0x8F, 0x90 and 0x9D, stay as those code points.

Examples:
    >>> from openodia import legacy
    >>> legacy.decode(b"JX\\xcf\\x85")
    'JXÏ…'
    >>> legacy.decode(b"\\x8d")
    '\\x8d'
"""

from openodia.legacy._decode import decode

__all__ = ["decode"]
