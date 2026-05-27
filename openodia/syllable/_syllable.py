"""Akshara segmentation state machine.

An *akshara* is the Odia orthographic syllable: one or more consonants
joined by halant (``୍``), optionally followed by a vowel sign and final
modifiers. The independent vowels (``ଅ``, ``ଆ``, …) form their own
aksharas.

The categoriser below covers the Odia Unicode block (U+0B00–U+0B7F).
Anything outside that block (Latin letters, digits, punctuation,
whitespace) is emitted as its own unit so callers can decide what to do
with it.
"""

from __future__ import annotations

# ----- Codepoint categories ------------------------------------------------

_INDEPENDENT_VOWELS: frozenset[str] = frozenset(
    "ଅଆଇଈଉଊଋଌଏଐଓଔ"  # U+0B05..U+0B14
    "ୠୡ"  # U+0B60..U+0B61 (vocalic R̄ / L̄)
)

_CONSONANTS: frozenset[str] = frozenset(
    "କଖଗଘଙ"  # gutturals
    "ଚଛଜଝଞ"  # palatals
    "ଟଠଡଢଣ"  # retroflex
    "ତଥଦଧନ"  # dentals
    "ପଫବଭମ"  # labials
    "ଯରଲଳଵଶଷସହ"  # semivowels + sibilants + ha
) | frozenset(
    # Pre-composed nukta consonants. Spelled via chr() so the source file
    # cannot silently decompose them via the editor's NFC normalization
    # and leak a stray U+0B3C nukta into the consonant set.
    [
        chr(0x0B5C),  # ଡ଼
        chr(0x0B5D),  # ଢ଼
        chr(0x0B5F),  # ୟ
    ]
)

_MATRAS: frozenset[str] = frozenset(
    "ାିୀୁୂୃୄେୈୋୌୖୗୢୣ"  # vowel signs (dependent vowels)
)

_HALANT: str = "୍"  # U+0B4D, the virama
_NUKTA: str = "଼"  # U+0B3C
_MODIFIERS: frozenset[str] = frozenset("ଁଂଃ")  # chandrabindu, anusvara, visarga


def _is_continuation(ch: str) -> bool:
    """Characters that always attach to the running akshara."""
    return ch in _MATRAS or ch in _MODIFIERS or ch == _NUKTA


# ----- Public API ---------------------------------------------------------


def split(word: str) -> list[str]:
    """Split a word into aksharas.

    Args:
        word: A single Odia word. Whitespace and non-Odia characters are
            emitted as their own units (one entry per character / run of
            whitespace).

    Returns:
        A list of aksharas in source order. Empty input returns ``[]``.

    Examples:
        >>> split("ନମସ୍କାର")
        ['ନ', 'ମ', 'ସ୍କା', 'ର']
        >>> split("ଓଡ଼ିଆ")
        ['ଓ', 'ଡ଼ି', 'ଆ']
    """
    if not word:
        return []

    aksharas: list[str] = []
    current: list[str] = []
    expecting_consonant = False  # set after a halant

    def flush() -> None:
        if current:
            aksharas.append("".join(current))
            current.clear()

    for ch in word:
        if ch in _CONSONANTS:
            if expecting_consonant or not current:
                current.append(ch)
            else:
                flush()
                current.append(ch)
            expecting_consonant = False

        elif ch in _INDEPENDENT_VOWELS:
            flush()
            current.append(ch)
            expecting_consonant = False

        elif ch == _HALANT:
            current.append(ch)
            expecting_consonant = True

        elif _is_continuation(ch):
            current.append(ch)
            expecting_consonant = False

        else:
            # Out-of-block character (digit, punctuation, whitespace, Latin
            # letter). Emit it as its own unit.
            flush()
            aksharas.append(ch)
            expecting_consonant = False

    flush()
    return aksharas


def count(word: str) -> int:
    """Number of Odia aksharas in ``word``.

    Non-Odia characters (whitespace, punctuation, digits, Latin letters)
    are *not* counted.
    """
    return sum(1 for unit in split(word) if any(ch in _INDEPENDENT_VOWELS or ch in _CONSONANTS for ch in unit))


def hyphenate(word: str, separator: str = "-") -> str:
    """Join aksharas with ``separator``.

    Whitespace runs in the input become natural breaks: each word is
    hyphenated independently and the original whitespace is preserved
    between them.

    Args:
        word: Odia text (one or more words).
        separator: String inserted between consecutive aksharas of the
            same word. Defaults to ``"-"``.

    Returns:
        The hyphenated string.

    Examples:
        >>> hyphenate("ବିଦ୍ୟାଳୟ")
        'ବି-ଦ୍ୟା-ଳ-ୟ'
        >>> hyphenate("ନମସ୍କାର ଓଡ଼ିଆ")
        'ନ-ମ-ସ୍କା-ର ଓ-ଡ଼ି-ଆ'
    """
    if not word:
        return ""

    out: list[str] = []
    buffer: list[str] = []  # aksharas for the current word

    def flush_word() -> None:
        if buffer:
            out.append(separator.join(buffer))
            buffer.clear()

    for token in split(word):
        if token.isspace() or (len(token) == 1 and not _is_odia(token)):
            flush_word()
            out.append(token)
        else:
            buffer.append(token)

    flush_word()
    return "".join(out)


def _is_odia(ch: str) -> bool:
    return ch in _INDEPENDENT_VOWELS or ch in _CONSONANTS or ch in _MATRAS or ch in _MODIFIERS or ch == _HALANT or ch == _NUKTA
