"""Akshara (orthographic syllable) segmentation for Odia text.

Examples:
    >>> from openodia import syllable
    >>> syllable.split("ନମସ୍କାର")
    ['ନ', 'ମ', 'ସ୍କା', 'ର']
    >>> syllable.count("ବିଦ୍ୟାଳୟ")
    4
    >>> syllable.hyphenate("ବିଦ୍ୟାଳୟ")
    'ବି-ଦ୍ୟା-ଳ-ୟ'
"""

from openodia.syllable._syllable import count, hyphenate, split

__all__ = ["count", "hyphenate", "split"]
