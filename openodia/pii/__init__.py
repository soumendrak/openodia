"""Detect and mask Indian PII in Odia text: phone, email, URL, Aadhaar, PAN and PIN code.

Rule-based and offline: patterns plus the Verhoeff checksum for Aadhaar. Person names, street
addresses, dates and amounts are not detected, so masking is not anonymisation.

Examples:
    >>> from openodia import pii
    >>> pii.mask("ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ।")
    'ମୋ ଫୋନ <PHONE> ।'
"""

from openodia.pii._detect import detect
from openodia.pii._entity import PII_TYPES, PIIEntity, PIIType
from openodia.pii._mask import mask

__all__ = ["PII_TYPES", "PIIEntity", "PIIType", "detect", "mask"]
