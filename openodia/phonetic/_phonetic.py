"""Soundex / Metaphone for Odia consonants.

The Soundex variant maps consonants to a single-digit place-of-articulation
code (1..8); vowels, matras, and halant are dropped from the body of the
key. The Metaphone variant collapses aspirated / voiced / voiceless
contrasts inside each articulation group to a single base consonant —
useful for spelling-variant matching that tolerates fewer collisions
than Soundex.
"""

from __future__ import annotations

# ----- Soundex codes -------------------------------------------------------

# Place of articulation → single digit.
_SOUNDEX_CODES: dict[str, str] = {
    # Gutturals
    "କ": "2",
    "ଖ": "2",
    "ଗ": "2",
    "ଘ": "2",
    "ଙ": "2",
    # Palatals
    "ଚ": "3",
    "ଛ": "3",
    "ଜ": "3",
    "ଝ": "3",
    "ଞ": "3",
    # Retroflex
    "ଟ": "4",
    "ଠ": "4",
    "ଡ": "4",
    "ଢ": "4",
    "ଣ": "4",
    chr(0x0B5C): "4",  # ଡ଼
    chr(0x0B5D): "4",  # ଢ଼
    # Dentals
    "ତ": "5",
    "ଥ": "5",
    "ଦ": "5",
    "ଧ": "5",
    "ନ": "5",
    # Labials
    "ପ": "6",
    "ଫ": "6",
    "ବ": "6",
    "ଭ": "6",
    "ମ": "6",
    # Semivowels (incl. retroflex semivowel ୟ)
    "ଯ": "7",
    "ର": "7",
    "ଲ": "7",
    "ଳ": "7",
    "ଵ": "7",
    "ୱ": "7",
    chr(0x0B5F): "7",  # ୟ
    # Sibilants + ha
    "ଶ": "8",
    "ଷ": "8",
    "ସ": "8",
    "ହ": "8",
}

# ----- Metaphone base consonants -------------------------------------------

# Each articulation group collapses to a single representative consonant.
_METAPHONE_BASE: dict[str, str] = {
    # Gutturals → କ
    "ଖ": "କ",
    "ଗ": "କ",
    "ଘ": "କ",
    "ଙ": "କ",
    # Palatals → ଚ
    "ଛ": "ଚ",
    "ଜ": "ଚ",
    "ଝ": "ଚ",
    "ଞ": "ଚ",
    # Retroflex → ଟ
    "ଠ": "ଟ",
    "ଡ": "ଟ",
    "ଢ": "ଟ",
    "ଣ": "ଟ",
    chr(0x0B5C): "ଟ",
    chr(0x0B5D): "ଟ",
    # Dentals → ତ
    "ଥ": "ତ",
    "ଦ": "ତ",
    "ଧ": "ତ",
    "ନ": "ତ",
    # Labials → ପ
    "ଫ": "ପ",
    "ବ": "ପ",
    "ଭ": "ପ",
    "ମ": "ପ",
    # Semivowels → ର
    "ଯ": "ର",
    "ଲ": "ର",
    "ଳ": "ର",
    "ଵ": "ର",
    "ୱ": "ର",
    chr(0x0B5F): "ର",
    # Sibilants → ସ
    "ଶ": "ସ",
    "ଷ": "ସ",
    "ହ": "ସ",
}


def _is_consonant(ch: str) -> bool:
    return ch in _SOUNDEX_CODES


# ----- Public API ----------------------------------------------------------


def soundex(word: str) -> str:
    """Return the 4-character Odia Soundex code for ``word``.

    The first consonant is kept verbatim. Subsequent consonants are
    replaced by their place-of-articulation digit (``2``–``8``); adjacent
    duplicates collapse. Vowels, matras, halant, nukta, and the modifiers
    are dropped. The output is right-padded with ``0`` to exactly 4
    characters and truncated if longer.

    Returns an empty string for an input that contains no consonant.

    Examples:
        >>> soundex("ସୋମେନ୍ଦ୍ର")
        'ସ೫೫೭'
    """
    if not word:
        return ""

    out: list[str] = []
    last: str = ""
    for ch in word:
        if _is_consonant(ch):
            if not out:
                # First consonant: keep verbatim.
                out.append(ch)
                last = _SOUNDEX_CODES[ch]
            else:
                code = _SOUNDEX_CODES[ch]
                if code != last:
                    out.append(code)
                    last = code
        else:
            # Vowel/matra/halant breaks the duplicate-suppression chain
            # without emitting anything.
            last = ""
        if len(out) >= 4:
            break

    if not out:
        return ""

    while len(out) < 4:
        out.append("0")
    return "".join(out[:4])


def metaphone(word: str) -> str:
    """Return the Odia Metaphone code for ``word``.

    Each consonant collapses to its articulation-group base
    (e.g. ``ଖ`` / ``ଗ`` / ``ଘ`` → ``କ``). Adjacent duplicates collapse.
    Vowels, matras, halant, and nukta are dropped.

    The output length varies with the input — there is no padding or
    truncation. Empty input yields an empty string.

    Examples:
        >>> metaphone("ସୋମେନ୍ଦ୍ର")
        'ସପତର'
    """
    if not word:
        return ""

    out: list[str] = []
    last: str | None = None
    for ch in word:
        if not _is_consonant(ch):
            continue
        base = _METAPHONE_BASE.get(ch, ch)
        if base != last:
            out.append(base)
            last = base
    return "".join(out)


def similarity(a: str, b: str) -> float:
    """Symmetric phonetic similarity in ``[0.0, 1.0]``.

    Combines Soundex (recall) with Metaphone (precision):

    * 0.5 weight on whether the two Soundex codes are equal.
    * 0.5 weight on a normalised edit-distance between Metaphone codes.

    Returns ``1.0`` when both encoders produce identical output, ``0.0``
    when both inputs are empty or contain no consonant.

    Examples:
        >>> similarity("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର") > 0.9
        True
    """
    sa, sb = soundex(a), soundex(b)
    ma, mb = metaphone(a), metaphone(b)

    if not sa and not sb and not ma and not mb:
        return 0.0

    soundex_score = 1.0 if sa and sa == sb else 0.0
    metaphone_score = _normalised_edit_similarity(ma, mb)
    return 0.5 * soundex_score + 0.5 * metaphone_score


def _normalised_edit_similarity(a: str, b: str) -> float:
    """``1 - edit_distance(a, b) / max(len(a), len(b))``.

    ``0.0`` when one is empty, ``1.0`` when both are empty.
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    distance = _levenshtein(a, b)
    return 1.0 - distance / max(len(a), len(b))


def _levenshtein(a: str, b: str) -> int:
    """Iterative Wagner-Fischer; ``O(len(a) * len(b))`` time, ``O(len(b))`` space."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            substitute = previous[j - 1] + (ca != cb)
            current.append(min(insert, delete, substitute))
        previous = current
    return previous[-1]
