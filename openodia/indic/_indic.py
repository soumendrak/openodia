"""Brahmic-block offset transliteration.

The Indic Unicode blocks (Devanagari, Bengali, Gurmukhi, Gujarati, Odia,
Tamil, Telugu, Kannada, Malayalam) share a parallel layout: characters
at the same offset within their block represent the same phonetic value.
Transliterating between two scripts is therefore a single offset
addition per codepoint that falls inside the source block. Characters
outside the source block (Latin letters, digits, whitespace,
punctuation, characters in other Indic blocks) pass through unchanged.

Tamil caveat: Tamil's encoding has only one consonant per articulation
group (no aspirated / voiced contrasts). Devanagari ``ख`` (U+0916,
offset 0x16) maps to U+0B96 in the Tamil block — which is unassigned.
That codepoint still appears in the output and most renderers will show
a placeholder box; we surface this rather than guessing a collapse.
"""

from __future__ import annotations

from typing import Literal

Script = Literal[
    "devanagari",
    "bengali",
    "assamese",
    "gurmukhi",
    "gujarati",
    "odia",
    "tamil",
    "telugu",
    "kannada",
    "malayalam",
]

#: Block start offset per supported script.
_SCRIPT_OFFSETS: dict[Script, int] = {
    "devanagari": 0x0900,
    "bengali": 0x0980,
    "assamese": 0x0980,  # Assamese shares the Bengali block.
    "gurmukhi": 0x0A00,
    "gujarati": 0x0A80,
    "odia": 0x0B00,
    "tamil": 0x0B80,
    "telugu": 0x0C00,
    "kannada": 0x0C80,
    "malayalam": 0x0D00,
}

_BLOCK_SIZE = 0x80  # Each Indic block spans 128 codepoints.

#: Public list of supported script names.
SCRIPTS: tuple[Script, ...] = tuple(_SCRIPT_OFFSETS.keys())


def transliterate(text: str, from_script: Script, to_script: Script) -> str:
    """Transliterate ``text`` from one Indic script to another.

    Only the codepoints belonging to ``from_script`` are translated;
    everything else (whitespace, Latin letters, digits, punctuation,
    characters in other Indic blocks) is preserved verbatim.

    Args:
        text: Source string.
        from_script: Name of the source script.
        to_script: Name of the destination script.

    Returns:
        The transliterated string. Same length as ``text``.

    Raises:
        ValueError: If either script name is unknown.
    """
    if from_script not in _SCRIPT_OFFSETS:
        raise ValueError(f"unknown from_script {from_script!r}; supported: {tuple(_SCRIPT_OFFSETS)}")
    if to_script not in _SCRIPT_OFFSETS:
        raise ValueError(f"unknown to_script {to_script!r}; supported: {tuple(_SCRIPT_OFFSETS)}")

    src_offset = _SCRIPT_OFFSETS[from_script]
    dst_offset = _SCRIPT_OFFSETS[to_script]
    if src_offset == dst_offset:
        # No-op: same block (or aliased — e.g. Assamese ↔ Bengali).
        return text

    delta = dst_offset - src_offset
    out: list[str] = []
    upper = src_offset + _BLOCK_SIZE
    for ch in text:
        cp = ord(ch)
        if src_offset <= cp < upper:
            out.append(chr(cp + delta))
        else:
            out.append(ch)
    return "".join(out)
