"""Customizable stopword lists for Odia text.

The package's bundled list is exposed as :data:`openodia.STOPWORDS`
(a :class:`frozenset`). For pipelines that need to extend / shrink /
swap the list per call, use :class:`Stopwords`.

Examples:
    >>> from openodia import Stopwords
    >>> sw = Stopwords.default()
    >>> "ଓ" in sw
    True
    >>> sw.add("ପ୍ରାୟ").remove("ଓ")
    >>> "ଓ" in sw
    False
"""

from openodia.stopwords._stopwords import Stopwords

__all__ = ["Stopwords"]
