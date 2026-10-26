"""Replace detected PII with placeholders."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from openodia.pii._detect import detect
from openodia.pii._entity import PIIEntity


def _tag(entity: PIIEntity) -> str:
    return f"<{entity.type}>"


def mask(
    text: str,
    types: Iterable[str] | None = None,
    min_confidence: float = 0.0,
    placeholder: Callable[[PIIEntity], str] = _tag,
) -> str:
    """Replace every detected span with ``placeholder(entity)``, ``<TYPE>`` by default.

    The default tags match no detector, so masking already-masked text changes nothing.
    A custom ``placeholder`` can break that guarantee.
    """
    pieces: list[str] = []
    cursor = 0
    for entity in detect(text, types, min_confidence):
        pieces.append(text[cursor : entity.start])
        pieces.append(placeholder(entity))
        cursor = entity.end
    pieces.append(text[cursor:])
    return "".join(pieces)
