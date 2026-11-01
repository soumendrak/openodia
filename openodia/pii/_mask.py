"""Replace detected PII with placeholders."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from openodia.pii._detect import detect, validated_types
from openodia.pii._entity import PIIEntity

_MAX_PASSES = 10


def _tag(entity: PIIEntity) -> str:
    return f"<{entity.type}>"


def _replace_once(text: str, types: frozenset[str], min_confidence: float, placeholder: Callable[[PIIEntity], str]) -> str:
    pieces: list[str] = []
    cursor = 0
    for entity in detect(text, types, min_confidence):
        pieces.append(text[cursor : entity.start])
        pieces.append(placeholder(entity))
        cursor = entity.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def mask(
    text: str,
    types: Iterable[str] | None = None,
    min_confidence: float = 0.0,
    placeholder: Callable[[PIIEntity], str] = _tag,
) -> str:
    """Replace every detected span with ``placeholder(entity)``, ``<TYPE>`` by default.

    Replacing a value can expose a neighbour that was glued to it, such as a PAN written directly
    before a URL. So detection and replacement repeat until nothing changes, at most 10 times.
    With the default tags the result is stable: masking it again changes nothing, unless the input
    chains more than 10 such glued values. From the second pass on, ``placeholder`` receives
    entities whose offsets index the partly masked text. A custom ``placeholder`` that returns
    text matching a detector can keep the loop going until the limit.

    Past 10 glued values the result can still contain raw PII, so do not rely on it for input
    that chains that many. ``types`` is read once, so an iterator works.
    """
    wanted = validated_types(types)
    for _ in range(_MAX_PASSES):
        masked = _replace_once(text, wanted, min_confidence, placeholder)
        if masked == text:
            break
        text = masked
    return text
