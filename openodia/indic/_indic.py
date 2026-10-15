"""Brahmic-script transliteration by Unicode character identity.

The Indic Unicode blocks (Devanagari, Bengali, Gurmukhi, Gujarati, Odia,
Tamil, Telugu, Kannada, Malayalam) mostly share a parallel layout, but
not completely: some scripts have letters the others lack (Malayalam
chillus, Odia WA), and shared marks such as the danda live only in the
Devanagari block. A blanket block offset would turn those into unrelated
or unassigned codepoints.

So each character is mapped by its Unicode name instead: ``DEVANAGARI
LETTER KA`` becomes ``ORIYA LETTER KA``. Malayalam chillus expand to the
base consonant plus virama (``ൻ`` → ``न्``). Characters with no
counterpart in the target script are kept unchanged. That includes
Latin, digits, punctuation, the shared danda, and e.g. Devanagari ``ख``
when targeting Tamil, which has no aspirated consonants.
"""

from __future__ import annotations

import unicodedata
from functools import cache
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
    "odia": 0x0B00,  # Unicode names this block "ORIYA".
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
        The transliterated string. Characters without a counterpart in
        ``to_script`` are kept as they are.

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

    src_names = _names(src_offset)
    dst_chars = _chars_by_name(dst_offset)
    upper = src_offset + _BLOCK_SIZE
    out: list[str] = []
    for ch in text:
        if not src_offset <= ord(ch) < upper or ch not in src_names:
            out.append(ch)
            continue
        out.append(_map_char(ch, src_names[ch], dst_chars))
    return "".join(out)


def _block_entries(start: int) -> list[tuple[str, str]]:
    """``(char, name without the script prefix)`` for assigned codepoints."""
    entries = []
    for cp in range(start, start + _BLOCK_SIZE):
        name = unicodedata.name(chr(cp), "")
        if name:
            name = name.split(" ", 1)[1]
            # Bengali/Gurmukhi/Odia "LETTER RRA" (ড়, ੜ, ଡ଼) is the flapped
            # retroflex that Devanagari calls DDDHA (ड़); Devanagari and the
            # southern scripts use "RRA" for the alveolar ऱ/ற/ఱ/റ instead.
            if start in _FLAP_RRA_BLOCKS and name == "LETTER RRA":
                name = "LETTER DDDHA"
            entries.append((chr(cp), name))
    return entries


_FLAP_RRA_BLOCKS = frozenset({0x0980, 0x0A00, 0x0B00})

#: Fallbacks for letters that only some scripts encode separately.
_NAME_FALLBACKS = {"LETTER WA": "LETTER VA"}  # Odia ୱ → व / ವ / …


@cache
def _names(start: int) -> dict[str, str]:
    return dict(_block_entries(start))


@cache
def _chars_by_name(start: int) -> dict[str, str]:
    return {name: ch for ch, name in _block_entries(start)}


def _map_char(ch: str, name: str, dst_chars: dict[str, str]) -> str:
    if name in dst_chars:
        return dst_chars[name]
    fallback = _NAME_FALLBACKS.get(name)
    if fallback in dst_chars:
        return dst_chars[fallback]
    if name.startswith("LETTER CHILLU "):
        # Chillu = consonant without inherent vowel: base letter + virama.
        base = dst_chars.get("LETTER " + name[len("LETTER CHILLU ") :] + "A")
        virama = dst_chars.get("SIGN VIRAMA")
        if base and virama:
            return base + virama
    return ch
