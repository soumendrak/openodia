"""The PII entity type and the supported type names."""

from __future__ import annotations

from dataclasses import dataclass

PII_TYPES: tuple[str, ...] = ("PHONE", "EMAIL", "URL", "AADHAAR", "PAN", "PINCODE")


@dataclass(frozen=True)
class PIIEntity:
    """One detected span; ``start`` and ``end`` are character offsets into the original input."""

    type: str
    text: str
    start: int
    end: int
    confidence: float
