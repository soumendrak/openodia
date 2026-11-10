from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from openodia.pii._detect import detect, validated_types
from openodia.pii._entity import PII_TYPES, PIIEntity

_MAX_PASSES = 10
_TOKEN = re.compile(rf"<({'|'.join(PII_TYPES)}):[1-9][0-9]*>")


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


class KeyStore:
    def __init__(self) -> None:
        self._token: dict[tuple[str, str], str] = {}
        self._original: dict[str, str] = {}
        self._counts: dict[str, int] = {}

    def token_for(self, entity: PIIEntity) -> str:
        key = (entity.type, entity.text)
        token = self._token.get(key)
        if token is not None:
            return token
        count = self._counts.get(entity.type, 0) + 1
        self._counts[entity.type] = count
        token = f"<{entity.type}:{count}>"
        self._token[key] = token
        self._original[token] = entity.text
        return token

    def original(self, token: str) -> str | None:
        return self._original.get(token)


def pseudonymize(
    text: str,
    store: KeyStore,
    types: Iterable[str] | None = None,
    min_confidence: float = 0.0,
) -> str:
    if not isinstance(store, KeyStore):
        raise TypeError(f"store must be KeyStore, got {type(store).__name__}")
    return mask(text, types, min_confidence, store.token_for)


def restore(text: str, store: KeyStore) -> str:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if not isinstance(store, KeyStore):
        raise TypeError(f"store must be KeyStore, got {type(store).__name__}")
    for _ in range(_MAX_PASSES):
        expanded = _expand_tokens(text, store)
        if expanded == text:
            return text
        text = expanded
    return text


def _expand_tokens(text: str, store: KeyStore) -> str:
    pieces: list[str] = []
    cursor = 0
    for match in _TOKEN.finditer(text):
        original = store.original(match.group(0))
        if original is None:
            continue
        pieces.append(text[cursor : match.start()])
        pieces.append(original)
        cursor = match.end()
    pieces.append(text[cursor:])
    return "".join(pieces)
