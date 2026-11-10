"""Masking is not anonymisation.

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
