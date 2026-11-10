"""Sandhi and compound splitting for Odia.

Examples:
    >>> from openodia import sandhi
    >>> sandhi.split("ବିଦ୍ୟାଳୟ")
    ['ବିଦ୍ୟା', 'ଆଳୟ']
    >>> sandhi.split("ସୂର୍ଯ୍ୟୋଦୟ")
    ['ସୂର୍ଯ୍ୟ', 'ଉଦୟ']
    >>> sandhi.split("ରାଜ୍ୟପାଳ")
    ['ରାଜ୍ୟ', 'ପାଳ']
    >>> sandhi.join(["ବିଦ୍ୟା", "ଆଳୟ"])
    'ବିଦ୍ୟାଳୟ'
"""

from openodia.sandhi._sandhi import join, split

__all__ = ["join", "split"]
