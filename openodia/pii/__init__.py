"""Detect and mask Indian PII in Odia text: phone, email, URL, Aadhaar, PAN, PIN code and date.

Rule-based and offline: patterns, the Verhoeff checksum for Aadhaar and a calendar check for dates.
Person names, street addresses and amounts are not detected, so masking is not anonymisation.

Examples:
    >>> from openodia import pii
    >>> pii.mask("ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ।")
    'ମୋ ଫୋନ <PHONE> ।'
"""

from openodia.pii._detect import detect
from openodia.pii._entity import PII_TYPES, PIIEntity, PIIType
from openodia.pii._mask import mask

__all__ = ["PII_TYPES", "PIIEntity", "PIIType", "detect", "mask"]
