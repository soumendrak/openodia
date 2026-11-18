"""Find, mask, and pseudonymize Indian PII in Odia or Latin text.

``detect`` and ``mask`` find phone numbers, emails, URLs, Aadhaar numbers, PAN,
PIN codes, dates, currency amounts, dictionary names, and a low-confidence
address span. ``KeyStore`` records each value as ``<TYPE:n>``. ``pseudonymize``
writes those tokens and ``restore`` puts the values back. ``restore`` also
rewrites a ``<TYPE:n>`` already in the text when that token is in the store, so
a round-trip does not preserve it.

Masking is not anonymisation.

Examples:
    >>> from openodia import pii
    >>> pii.mask("ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ।")
    'ମୋ ଫୋନ <PHONE> ।'
"""

from openodia.pii._detect import detect
from openodia.pii._entity import PII_TYPES, PIIEntity, PIIType
from openodia.pii._mask import KeyStore, mask, pseudonymize, restore

__all__ = [
    "KeyStore",
    "PII_TYPES",
    "PIIEntity",
    "PIIType",
    "detect",
    "mask",
    "pseudonymize",
    "restore",
]
