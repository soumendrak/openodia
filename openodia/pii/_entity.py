"""The PII entity type and the supported type names."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

PIIType = Literal["PHONE", "EMAIL", "URL", "AADHAAR", "PAN", "PINCODE"]
PII_TYPES: tuple[PIIType, ...] = get_args(PIIType)


@dataclass(frozen=True)
class PIIEntity:
    """One detected span; ``start`` and ``end`` are character offsets into the original input."""

    type: PIIType
    text: str
    start: int
    end: int
    confidence: float
