import random
import re
import string
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import pytest

from openodia import roman
from openodia.corpus.dictionary import get_dictionary
from openodia.syllable import count as akshara_count

_ODIA_RUN = re.compile(r"[\u0b00-\u0b7f]+")
_LATIN_RUN = re.compile(r"[A-Za-z]+")
_HOMOPHONES = ("ଜାଲ", "ବକ୍ସ", "ପାତ୍ର", "ବର୍ଷା", "କୁକୁଡ଼ା")


def test_issue_examples() -> None:
    assert roman.type_odia("namaskara") == "ନମସ୍କାର"
    assert roman.type_odia("odisha bhasha") == "ଓଡ଼ିଶା ଭାଷା"
    assert roman.type_odia("ki bhabare achanti") == "କି ଭାବରେ ଅଛନ୍ତି"
    assert "\u0b3c" in roman.type_odia("odisha")


def test_fuzzy_spellings_share_a_word() -> None:
    assert roman.type_odia("achanti") == roman.type_odia("achhanti") == "ଅଛନ୍ତି"
    assert roman.type_odia("kichi") == roman.type_odia("kichhi") == "କିଛି"
    assert roman.type_odia("orisha") == "ଓଡ଼ିଶା"
    assert roman.type_odia("kukuda") == "କୁକୁଡ଼ା"
    assert roman.type_odia("kukura") == "କୁକୁର"
    assert roman.type_odia("Namaskara") == "ନମସ୍କାର"
    ya = ["ଯାଅ", "ୟା", "ଯ", "ୟ"]
    assert roman.type_odia("ya", candidates=True) == ya
    assert roman.type_odia("yaa", candidates=True) == ya


def test_candidates_are_full_strings_best_first() -> None:
    assert roman.type_odia("namaskara", candidates=True) == ["ନମସ୍କାର"]
    assert roman.type_odia("ki", candidates=True) == ["କି", "କୀ"]
    assert roman.type_odia("odisha", candidates=True) == ["ଓଡ଼ିଶା", "ଓଡିଶା"]
    assert roman.type_odia("ki jala", candidates=True) == [
        "କି ଜଳ",
        "କୀ ଜଳ",
        "କି ଜାଲ",
        "କୀ ଜାଲ",
        "କି ଜାଳ",
        "କୀ ଜାଳ",
    ]
    assert roman.type_odia("ki") == roman.type_odia("ki", candidates=True)[0]


def test_whitespace_and_punctuation_are_preserved() -> None:
    text = "  ki,  bhabare!\n"
    assert roman.type_odia(text) == "  କି,  ଭାବରେ!\n"
    assert roman.type_odia(text, candidates=True) == [
        "  କି,  ଭାବରେ!\n",
        "  କୀ,  ଭାବରେ!\n",
    ]
    assert roman.type_odia("ନମସ୍କାର namaskara") == "ନମସ୍କାର ନମସ୍କାର"
    assert roman.type_odia("") == ""
    assert roman.type_odia("", candidates=True) == []
    assert roman.type_odia("  \n", candidates=True) == ["  \n"]


def test_unknown_word_uses_hunterian() -> None:
    assert roman.type_odia("hello") == "ହେଲ୍ଲୋ"
    assert roman.type_odia("Hello") == "ହେଲ୍ଲୋ"
    assert roman.type_odia("hello!") == "ହେଲ୍ଲୋ!"


def test_every_ascii_letter_becomes_odia() -> None:
    words = ["coffee", "Zebra", "box", "quiz", "pizza", "taxi", "zoo"]
    typed = [roman.type_odia(word) for word in words]
    assert typed == ["କୋଫ୍ଫେଏ", "ଜେବ୍ର", "ବୋକ୍ସ୍", "କୁଇଜ୍", "ପିଜ୍ଜ", "ତକ୍ସି", "ଜୋଓ"]
    assert all(_LATIN_RUN.search(item) is None for item in typed)


def test_missing_word_matches_lowercased_hunterian() -> None:
    for word in ("chhuin", "chhaila", "hello"):
        assert roman.type_odia(word) == roman.from_roman(word.lower(), "Hunterian")
    assert roman.type_odia("chhuin") == "ଛୁଇନ୍"
    assert roman.type_odia("chq") == roman.from_roman("chk", "Hunterian")


def test_candidates_are_well_formed_syllables() -> None:
    ana = roman.type_odia("ana", candidates=True)
    assert "ାନ" not in ana
    assert all(_well_formed_odia(item) for item in ana)
    assert _well_formed_odia(roman.type_odia("bhashai"))
    assert roman.type_odia("bhashai") != "ଭାଷାୀ"
    assert _well_formed_odia(roman.type_odia("eyamaena"))
    assert roman.type_odia("eyamaena") != "େଯମାେନ"
    from openodia.roman._typing import _lexicon

    for rows in _lexicon().values():
        for word, _count in rows:
            assert _well_formed_odia(word), word


def test_fold_and_flap_rules_are_visible() -> None:
    assert roman.type_odia("dadha") == "ଦାଢ଼ା"
    assert roman.type_odia("kii") == "କି"
    assert roman.type_odia("bahuuta") == "ବହୁତ"
    assert roman.type_odia("aaaa") == "ଆ"
    assert "ସାଇଟୋୋକାଇନ୍ସିସ୍" not in roman.type_odia("saitookainsis", candidates=True)
    assert roman.type_odia("sidirigudika") == "ସିଡ଼ିଡ଼ିଗୁଡ଼ିକ"
    assert "ୱିଂ" not in roman.type_odia("win", candidates=True)
    ranked = roman.type_odia("besi chipsakripsed pharmatariddhi glokal", candidates=True)
    assert ranked[1] == "ବେସି ଚିପ୍ସକ୍ରିପ୍ସେଡ୍ ଫର୍ମାଟରିଦ୍ଧୀ ଗ୍ଲୋକାଲ୍"
    assert ranked[2] == "ବେସୀ ଚିପ୍ସକ୍ରିପ୍ସେଡ୍ ଫର୍ମାଟରିଦ୍ଧୀ ଗ୍ଲୋକଲ୍"


def test_candidates_grow_linearly() -> None:
    roman.type_odia("ki")

    def elapsed(count: int) -> float:
        text = "ki " * count
        started = time.perf_counter()
        roman.type_odia(text, candidates=True)
        return time.perf_counter() - started

    small = min(elapsed(2000) for _ in range(3))
    large = min(elapsed(8000) for _ in range(3))
    assert large < small * 6


def test_roman_docs_name_the_release() -> None:
    sentence = "`openodia.roman` needs a release newer than 0.1.14"
    root = Path(__file__).resolve().parent.parent
    for path in ("docs/index.md", "docs/llms.txt"):
        assert sentence in (root / path).read_text(encoding="utf-8")


def test_typing_again_changes_nothing() -> None:
    typed = roman.type_odia("ki bhabare achanti!")
    assert roman.type_odia(typed) == typed


def test_type_errors() -> None:
    with pytest.raises(TypeError):
        roman.type_odia(None)
    with pytest.raises(TypeError):
        roman.type_odia("ki", candidates=1)


def test_candidate_list_stops_at_eight() -> None:
    alternatives = roman.type_odia("bada kala", candidates=True)
    assert len(alternatives) == 8
    assert len(set(alternatives)) == 8
    assert alternatives[0] == roman.type_odia("bada kala")


def test_avagraha_spelling_is_not_a_typing_key() -> None:
    from openodia.roman._typing import _keys

    assert _keys("କଽ") == ()


def test_exported_from_roman() -> None:
    assert "type_odia" in roman.__all__


def test_five_hundred_common_words() -> None:
    counts: dict[str, int] = {}
    for value in get_dictionary().values():
        for token in _ODIA_RUN.findall(unicodedata.normalize("NFC", value)):
            if akshara_count(token) >= 1:
                counts[token] = counts.get(token, 0) + 1
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:500]
    missed: list[str] = []
    for word, _count in top:
        spelling = roman.to_roman(word, "Hunterian")
        chosen = roman.type_odia(spelling)
        alternatives = roman.type_odia(spelling, candidates=True)
        assert alternatives[0] == chosen
        assert word in alternatives
        assert all(akshara_count(item) >= 1 and _ODIA_RUN.fullmatch(item) for item in alternatives)
        if chosen != word:
            missed.append(word)
            assert alternatives[1] == word
    assert missed == list(_HOMOPHONES)
    assert len(top) - len(missed) == 495


_VOWELS = set("ଅଆଇଈଉଊଋଌୠୡଏଐଓଔ")
_CONSONANTS = set("କଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵୱଶଷସହୟ")
_MATRAS = set("ାିୀୁୂୃୄେୈୋୌୖୗୢୣ")
_MODIFIERS = set("ଁଂଃ")


def _read_syllable(word: str, index: int) -> int:
    if word[index] in _VOWELS:
        index += 1
    elif word[index] in _CONSONANTS:
        index += 1
        if index < len(word) and word[index] == "଼":
            index += 1
        if index < len(word) and word[index] == "୍":
            return index + 1
        if index < len(word) and word[index] in _MATRAS:
            index += 1
            if index < len(word) and word[index] in _MATRAS:
                return -1
    else:
        return -1
    if index < len(word) and word[index] in _MODIFIERS:
        return index + 1
    return index


def _well_formed_odia(word: str) -> bool:
    if not word or unicodedata.normalize("NFC", word) != word:
        return False
    index = 0
    while index < len(word):
        nxt = _read_syllable(word, index)
        if nxt <= index:
            return False
        index = nxt
    return True


def test_typed_letters_are_odia() -> None:
    rng = random.Random(197)
    letters = string.ascii_letters
    marks = (" ", ", ", "!", ".\n")
    for _ in range(40):
        words = ["".join(rng.choice(letters) for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(1, 4))]
        text = "".join(word + rng.choice(marks) for word in words)
        typed = roman.type_odia(text)
        assert isinstance(typed, str)
        assert _LATIN_RUN.sub("", text) == _ODIA_RUN.sub("", typed)
        assert _LATIN_RUN.search(typed) is None
        for run in _ODIA_RUN.findall(typed):
            assert unicodedata.normalize("NFC", run) == run
        alternatives = roman.type_odia(text, candidates=True)
        assert alternatives
        assert alternatives[0] == typed
        assert roman.type_odia(typed) == typed


def test_glossary_loads_on_first_call() -> None:
    script = (
        "import openodia\n"
        "from openodia.corpus.dictionary import get_dictionary\n"
        "from openodia.roman._typing import _lexicon\n"
        "assert get_dictionary.cache_info().currsize == 0\n"
        "assert _lexicon.cache_info().currsize == 0\n"
        "assert openodia.roman.type_odia('namaskara') == 'ନମସ୍କାର'\n"
        "assert get_dictionary.cache_info().currsize == 1\n"
        "assert _lexicon.cache_info().currsize == 1\n"
        "openodia.roman.type_odia('bhasha')\n"
        "assert get_dictionary.cache_info().currsize == 1\n"
        "assert _lexicon.cache_info().currsize == 1\n"
    )
    subprocess.run([sys.executable, "-c", script], check=True)
