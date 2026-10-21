"""Phonetic-similarity utilities for Odia.

Two encoders and one similarity score:

* :func:`soundex` — fixed-length 4-character code based on Odia
  place-of-articulation phoneme groups.
* :func:`metaphone` — variable-length consonant skeleton with
  aspirated/voiced pairs collapsed to their base.
* :func:`similarity` — symmetric ``[0.0, 1.0]`` score combining the two.

Examples:
    >>> from openodia import phonetic
    >>> phonetic.soundex("ସୋମେନ୍ଦ୍ର") == phonetic.soundex("ସୌମେନ୍ଦ୍ର")
    True
    >>> phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର") > 0.8
    True
"""

from openodia.phonetic._phonetic import metaphone, similarity, soundex

__all__ = ["metaphone", "similarity", "soundex"]
