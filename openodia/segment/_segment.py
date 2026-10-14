"""Robust sentence segmenter for Odia text.

The algorithm:

1. Mask out tokens that *look* like sentence boundaries but aren't:
   decimals (``୨.୫`` / ``2.5``) and a small set of common abbreviations.
2. Split the masked string on a run of terminators (``।``, ``॥``, ``.``,
   ``?``, ``!``, ``…``) followed by whitespace or end-of-string.
3. Restore masked tokens in the resulting sentences.

The mask uses a NUL byte sentinel which is extraordinarily rare in natural
language. Inputs that contain literal NUL bytes will round-trip
correctly because the mask placeholder is ``\\x00<n>\\x00`` not a bare
NUL.
"""

from __future__ import annotations

import re
from typing import Literal

SegmenterMode = Literal["default", "strict"]

#: Tokens whose period (``.``) must not be treated as a sentence boundary.
#: Add to this set for project-specific vocabulary.
ABBREVIATIONS: tuple[str, ...] = (
    # Odia honorifics & abbreviations
    "ଡଃ",
    "ଶ୍ରୀ",
    "ଶ୍ରୀମତୀ",
    "ସା.କଃ.",
    # Common Latin abbreviations that appear in mixed Odia/English text
    "Mr.",
    "Mrs.",
    "Ms.",
    "Dr.",
    "Prof.",
    "Sr.",
    "Jr.",
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
)

_TERMINATORS_DEFAULT = "।॥.?!…"
_TERMINATORS_STRICT = "।॥"

# A run of one or more terminator chars, optionally followed by whitespace.
# ``re.split`` with a *capturing* group yields ``[text, sep, text, sep, ...]``.
_SPLIT_RE_DEFAULT = re.compile(rf"([{re.escape(_TERMINATORS_DEFAULT)}]+)\s*")
_SPLIT_RE_STRICT = re.compile(rf"([{re.escape(_TERMINATORS_STRICT)}]+)\s*")

# Decimal numbers in either ASCII or Odia digits, with a period in the middle.
_DECIMAL_RE = re.compile(r"[0-9୦-୯]+\.[0-9୦-୯]+")


def _mask(text: str) -> tuple[str, list[str]]:
    """Replace decimals and abbreviations with ``\\x00<idx>\\x00`` placeholders."""
    masks: list[str] = []

    def take(match: re.Match[str]) -> str:
        masks.append(match.group(0))
        return f"\x00{len(masks) - 1}\x00"

    out = _DECIMAL_RE.sub(take, text)

    # Longest-first so "ଶ୍ରୀମତୀ" masks before any prefix like "ଶ୍ରୀ" would.
    if ABBREVIATIONS:
        abbr_pattern = re.compile("|".join(re.escape(a) for a in sorted(ABBREVIATIONS, key=len, reverse=True)))
        out = abbr_pattern.sub(take, out)

    return out, masks


_RESTORE_RE = re.compile(r"\x00(\d+)\x00")


def _restore(text: str, masks: list[str]) -> str:
    """Inverse of :func:`_mask`."""
    if not masks:
        return text
    return _RESTORE_RE.sub(lambda m: masks[int(m.group(1))], text)


def sentences(
    text: str,
    *,
    mode: SegmenterMode = "default",
    keep_terminators: bool = True,
) -> list[str]:
    """Split ``text`` into sentences.

    Args:
        text: Input string. May be Odia, mixed Odia/Latin, or empty.
        mode: ``"default"`` (recommended) treats ``।``, ``॥``, ``.``, ``?``,
            ``!``, ``…`` as terminators. ``"strict"`` only treats Odia
            terminators (``।``, ``॥``) as boundaries — useful for classical
            Odia text that uses Latin periods inside content.
        keep_terminators: When ``True`` (default), each returned sentence
            includes its trailing punctuation. Set to ``False`` to strip
            the terminator.

    Returns:
        List of sentences in source order. Empty input returns an empty
        list.

    Raises:
        ValueError: If ``mode`` is not recognised.

    Examples:
        >>> sentences("ଆଜି ୨.୫ କୋଟି। ଆଗକୁ କଣ? ଭଲ ଦିନ!")
        ['ଆଜି ୨.୫ କୋଟି।', 'ଆଗକୁ କଣ?', 'ଭଲ ଦିନ!']
        >>> sentences("ଡଃ ସୁନୀତା ଆସିଲେ। ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।")
        ['ଡଃ ସୁନୀତା ଆସିଲେ।', 'ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।']
    """
    if mode == "default":
        split_re = _SPLIT_RE_DEFAULT
    elif mode == "strict":
        split_re = _SPLIT_RE_STRICT
    else:
        raise ValueError(f"unknown mode {mode!r}; supported: 'default', 'strict'")

    if not text or not text.strip():
        return []

    masked, masks = _mask(text)
    parts = split_re.split(masked)

    out: list[str] = []
    for i in range(0, len(parts), 2):
        body = parts[i].strip()
        terminator = parts[i + 1] if i + 1 < len(parts) else ""
        if not body:
            continue
        sentence = body + terminator if keep_terminators else body
        out.append(_restore(sentence, masks))

    return out
