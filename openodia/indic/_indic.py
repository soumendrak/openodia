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

Two formal Unicode names are corrected before matching, because they are
known mistakes: Tamil U+0B83 is aytham, not visarga, and Kannada U+0CDE is
LLLA, not FA. An anusvara aimed at Gurmukhi is written as tippi or bindi
according to the vowel it follows.
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
    dst_chars = _chars_by_name(to_script)
    upper = src_offset + _BLOCK_SIZE
    # Recompose canonically decomposed vowel signs (Bengali ে + ৗ → ৌ) and
    # Gurmukhi nukta consonants (ਸ + ਼ → ਸ਼). Not NFC: that would decompose
    # excluded nukta letters such as ଡ଼ and rewrite text outside this script.
    for decomposed, composed in _recompositions(src_offset).items():
        text = text.replace(decomposed, composed)
    return "".join(_transliterate_char(text, i, src_offset, upper, src_names, dst_chars, to_script) for i in range(len(text)))


def _transliterate_char(
    text: str,
    index: int,
    src_offset: int,
    upper: int,
    src_names: dict[str, str],
    dst_chars: dict[str, str],
    to_script: Script,
) -> str:
    ch = text[index]
    if not src_offset <= ord(ch) < upper or ch not in src_names:
        return ch
    name = src_names[ch]
    if name == "ADDAK" and "ADDAK" not in dst_chars:
        return _geminate(text[index + 1 : index + 2], src_names, dst_chars) or ch
    if to_script == "gurmukhi" and name == "SIGN ANUSVARA":
        return _gurmukhi_nasal(text, index, src_names, dst_chars)
    if name == "SIGN YAKASH":
        return _subjoined_ya(dst_chars)
    return _map_char(ch, src_names, dst_chars)


def _subjoined_ya(dst_chars: dict[str, str]) -> str:
    """Gurmukhi yakash is a subjoined YA, encoded as virama + YA."""
    return dst_chars["SIGN VIRAMA"] + dst_chars["LETTER YA"]


def _geminate(nxt: str, src_names: dict[str, str], dst_chars: dict[str, str]) -> str:
    """Gurmukhi addak doubles the next consonant: emit it + virama."""
    if not nxt or not src_names.get(nxt, "").startswith("LETTER "):
        return ""
    virama = dst_chars.get("SIGN VIRAMA")
    base = _map_char(nxt, src_names, dst_chars)
    return base + virama if virama and base != nxt else ""


# Bindi goes with dependent and independent aa, ii, ee, ai, oo, and au, and
# with independent u and uu. Tippi is every other context (inherent a,
# dependent i/u/uu, independent a/i). Names are the northern ones already
# produced by _block_entries, so the long e/o are E/O, not EE/OO.
_BINDI_VOWELS = frozenset(
    {
        "LETTER AA",
        "VOWEL SIGN AA",
        "LETTER II",
        "VOWEL SIGN II",
        "LETTER E",
        "VOWEL SIGN E",
        "LETTER AI",
        "VOWEL SIGN AI",
        "LETTER O",
        "VOWEL SIGN O",
        "LETTER AU",
        "VOWEL SIGN AU",
        "LETTER U",
        "LETTER UU",
    }
)


def _gurmukhi_nasal(text: str, index: int, src_names: dict[str, str], dst_chars: dict[str, str]) -> str:
    """Choose Gurmukhi bindi or tippi from the vowel the anusvara follows."""
    bindi = dst_chars["SIGN ANUSVARA"]
    tippi = dst_chars["TIPPI"]
    for j in range(index - 1, -1, -1):
        name = src_names.get(text[j])
        if name is None or name != "SIGN NUKTA":
            return bindi if name in _BINDI_VOWELS else tippi
    return tippi


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
            # Tamil/Telugu/Kannada/Malayalam have short and long e/o and
            # call them E/EE, O/OO. Northern scripts' E/O are the long
            # vowels, and Devanagari names its short ones SHORT E/O. Use
            # the northern naming throughout.
            if start in _SHORT_LONG_EO_BLOCKS:
                name = _SOUTH_EO.get(name, name)
            name = _BLOCK_RENAMES.get(start, {}).get(name, name)
            entries.append((chr(cp), name))
    return entries


_FLAP_RRA_BLOCKS = frozenset({0x0980, 0x0A00, 0x0B00})
_SHORT_LONG_EO_BLOCKS = frozenset({0x0B80, 0x0C00, 0x0C80, 0x0D00})
_SOUTH_EO = {
    f"{kind} {south}": f"{kind} {north}"
    for kind in ("LETTER", "VOWEL SIGN")
    for south, north in (("E", "SHORT E"), ("EE", "E"), ("O", "SHORT O"), ("OO", "O"))
}

#: Per-block renames onto the shared identity used for lookup.
# Tamil U+0B83 is aytham, not visarga, and Kannada U+0CDE's formal name
# LETTER FA is a mistake for LLLA (Unicode Standard, ch. 12).
_BLOCK_RENAMES: dict[int, dict[str, str]] = {
    0x0A00: {  # Gurmukhi has only the long e/o, named EE/OO.
        "LETTER EE": "LETTER E",
        "VOWEL SIGN EE": "VOWEL SIGN E",
        "LETTER OO": "LETTER O",
        "VOWEL SIGN OO": "VOWEL SIGN O",
        "SIGN BINDI": "SIGN ANUSVARA",
        "SIGN ADAK BINDI": "SIGN CANDRABINDU",
    },
    0x0A80: {  # Gujarati calls its independent candra vowels VOWEL.
        "VOWEL CANDRA E": "LETTER CANDRA E",
        "VOWEL CANDRA O": "LETTER CANDRA O",
    },
    0x0B80: {"SIGN VISARGA": "SIGN AYTHAM"},
    0x0C80: {"LETTER FA": "LETTER LLLA"},
}

#: Fallbacks for letters that only some scripts encode separately.
_NAME_FALLBACKS = {
    "LETTER WA": "LETTER VA",  # Odia ୱ → व / ವ / …
    "LETTER RA WITH MIDDLE DIAGONAL": "LETTER RA",  # Assamese ৰ
    "LETTER RA WITH LOWER DIAGONAL": "LETTER VA",  # Assamese ৱ
    "TIPPI": "SIGN ANUSVARA",  # Gurmukhi ੰ (nasal, like bindi)
}
#: Assamese writes RA and VA/WA with its own letters in the Bengali block.
_ASSAMESE_TARGET = {"LETTER RA": "\u09f0", "LETTER VA": "\u09f1", "LETTER WA": "\u09f1"}
#: Bengali has no separate VA/WA; BA serves for both (বিশ্বাস).
_BENGALI_TARGET = {"LETTER VA": "\u09ac", "LETTER WA": "\u09ac"}
#: Source-only aliases: modern Malayalam writes /au/ with the AU length
#: mark alone (പൗ), so read it as the vowel sign. Not applied to the target
#: table, which keeps the precomposed ൌ for VOWEL SIGN AU.
_SOURCE_ALIASES: dict[int, dict[str, str]] = {0x0D00: {"AU LENGTH MARK": "VOWEL SIGN AU"}}
#: Dead-consonant letters that expand to base letter + virama.
_DEAD_CONSONANTS = {
    "LETTER KHANDA TA": "LETTER TA",  # Bengali ৎ
    "LETTER DOT REPH": "LETTER RA",  # Malayalam ൎ
}


@cache
def _names(start: int) -> dict[str, str]:
    aliases = _SOURCE_ALIASES.get(start, {})
    return {ch: aliases.get(name, name) for ch, name in _block_entries(start)}


@cache
def _recompositions(start: int) -> dict[str, str]:
    """``decomposed → precomposed`` for vowel signs and Gurmukhi nukta consonants.

    Gurmukhi SHA, LLA, and the pairin-bindi letters are composition
    exclusions, so NFC leaves SA + nukta decomposed and the name-based
    mapper would then emit SA instead of SHA. Other blocks keep that
    decomposed nukta spelling: Odia DDA + nukta is not the flap ଡ଼.
    """
    out = {}
    for ch, name in _block_entries(start):
        parts = unicodedata.normalize("NFD", ch)
        nukta_consonant = start == 0x0A00 and _contains_nukta(parts)
        if len(parts) > 1 and (name.startswith("VOWEL SIGN") or nukta_consonant):
            out[parts] = ch
    return out


def _contains_nukta(parts: str) -> bool:
    return any(unicodedata.name(part, "").endswith("SIGN NUKTA") for part in parts)


@cache
def _chars_by_name(script: Script) -> dict[str, str]:
    table = {name: ch for ch, name in _block_entries(_SCRIPT_OFFSETS[script])}
    if script == "assamese":
        table.update(_ASSAMESE_TARGET)
    elif script == "bengali":
        table.update(_BENGALI_TARGET)
    return table


def _map_char(ch: str, src_names: dict[str, str], dst_chars: dict[str, str]) -> str:
    name = src_names[ch]
    if name in dst_chars:
        return dst_chars[name]
    fallback = _NAME_FALLBACKS.get(name)
    if fallback in dst_chars:
        return dst_chars[fallback]
    base_name = _DEAD_CONSONANTS.get(name)
    if base_name is None and name.startswith("LETTER CHILLU "):
        # Chillu = consonant without inherent vowel: base letter + virama.
        base_name = "LETTER " + name[len("LETTER CHILLU ") :] + "A"
        # Unicode names U+0D7C "CHILLU RR", but it is the chillu of RA.
        if base_name == "LETTER RRA":
            base_name = "LETTER RA"
    if base_name is not None:
        base = dst_chars.get(base_name)
        virama = dst_chars.get("SIGN VIRAMA")
        if base and virama:
            return base + virama
    # Precomposed letters (e.g. क़ = क + nukta) map part by part, when every
    # part has a counterpart in the target script.
    parts = unicodedata.normalize("NFD", ch)
    if len(parts) > 1 and all(p in src_names for p in parts):
        mapped = [_map_char(p, src_names, dst_chars) for p in parts]
        if all(m != p for m, p in zip(mapped, parts)):
            return "".join(mapped)
    return ch
