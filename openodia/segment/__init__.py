"""Sentence segmentation for Odia text.

Examples:
    >>> from openodia import sentences
    >>> sentences("ଆଜି ୨.୫ କୋଟି ଟଙ୍କା। ଆଗକୁ କଣ?")
    ['ଆଜି ୨.୫ କୋଟି ଟଙ୍କା।', 'ଆଗକୁ କଣ?']
"""

from openodia.segment._segment import ABBREVIATIONS, SegmenterMode, sentences

__all__ = ["ABBREVIATIONS", "SegmenterMode", "sentences"]
