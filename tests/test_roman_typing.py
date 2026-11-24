import ast
import random
import re
import string
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import pytest

from openodia import roman, syllable
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


_W_VOWEL_WORDS = {
    "wa": "ୱା",
    "waa": "ୱା",
    "Wa": "ୱା",
    "WAAAA": "ୱା",
    "wawa": "ୱାୱା",
    "waawaa": "ୱାୱା",
    "wii": "ୱି",
    "Wiii": "ୱି",
    "wuu": "ୱୁ",
    "WUUU": "ୱୁ",
    "wi": "ୱି",
    "wu": "ୱୁ",
}


@pytest.mark.parametrize(("typed", "word"), _W_VOWEL_WORDS.items())
def test_w_and_a_vowel_type_the_dictionary_word(typed: str, word: str) -> None:
    assert roman.type_odia(typed) == word
    assert roman.type_odia(typed, candidates=True) == [word]


@pytest.mark.parametrize("typed", ["win", "wiin", "WIN"])
def test_win_suggests_both_dictionary_spellings(typed: str) -> None:
    assert roman.type_odia(typed, candidates=True) == ["ୱିନ୍", "ୱିଂ"]


_PRE_FIX_OUTPUT = {
    "wa": "ୱ",
    "waa": "ୱଅ",
    "wawa": "ୱୱ",
    "wii": "ୱିଇ",
    "wuu": "ୱୁଉ",
    "win": ["ୱିନ୍"],
}
_PRE_FIX_SPLIT = {"ୱେବ": (["ୱ", "େ", "ବ"], 1), "ସ୍ୱର": (["ସ୍", "ୱ", "ର"], 2)}
_UNCHANGED_NEAR_MISSES = {
    "wi": "ୱି",
    "wu": "ୱୁ",
    "we": "ୱେ",
    "wo": "ୱୋ",
    "wee": "ୱେଏ",
    "woo": "ୱୋଓ",
    "wia": "ୱିଅ",
    "awa": "ଅୱ",
    "swa": "ସ୍ୱ",
    "wun": ["ୱୁନ୍"],
    "wen": ["ୱେନ୍"],
    "wan": ["ୱାନ୍", "ୱନ୍"],
}
_W_CLASS = (
    "ignoring case, and reading a run of one vowel (`aa`, `iii`) as that vowel, "
    "the inputs that read as `wa`, `wawa` or `win`, or as `wi` or `wu` with the vowel repeated, now type a dictionary word"
)
_W_SCOPE = "Across all lowercase inputs of 1 to 3 letters and every `w` input of up to 4 letters in lower, upper or title case, no other output changes."
_W_LINE_OUTLINE = (
    "- `syllable.split` and `syllable.count` treat `ୱ` (U+0B71) as a consonant, so <split> (two aksharas) and <split>. "
    "It used to split `ୱ` from its vowel sign or halant and not count it. "
    f"`roman.type_odia` follows: {_W_CLASS}. "
    "<pair>, <pair>, <pair>, <pair>, and <pair>; <already>. "
    f"{_W_SCOPE}"
)
_COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}
_SPLIT_EXAMPLE = re.compile(r"`(?P<text>\S+)` is `(?P<parts>\[[^`]+\])`(?: \((?P<count>\w+) aksharas\))?")
_PAIR_EXAMPLE = re.compile(
    r"`(?P<typed>\w+)`(?: and `(?P<second>\w+)`)?(?P<candidates> with `candidates=True`)? (?P<verb>gives?) `(?P<new>[^`]+)` "
    r"\((?P<pronoun>it|they) gave `(?P<old>[^`]+)`(?: and `(?P<second_old>[^`]+)`)?\)"
)
_ALREADY_EXAMPLE = re.compile(r"`(\w+)` and `(\w+)` already gave `([^`]+)` and `([^`]+)`")
_CLASS_READINGS = re.compile(r"read as `(\w+)`, `(\w+)` or `(\w+)`, or as `(\w+)` or `(\w+)` with the vowel repeated")
_W_VOWEL_RUN = re.compile(r"([aeiou])\1*")


def _w_changelog_line() -> str:
    changelog = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    [line] = [line for line in changelog.splitlines() if line.startswith("- `syllable.split` and `syllable.count` treat `ୱ`")]
    return line


def _stated(text: str) -> str | list[str]:
    return ast.literal_eval(text) if text.startswith("[") else text


def _changelog_pairs() -> dict[str, tuple[bool, str | list[str], str | list[str]]]:
    pairs: dict[str, tuple[bool, str | list[str], str | list[str]]] = {}
    for match in _PAIR_EXAMPLE.finditer(_w_changelog_line()):
        candidates = match["candidates"] is not None
        pairs[match["typed"]] = (candidates, _stated(match["new"]), _stated(match["old"]))
        if match["second"] is not None:
            pairs[match["second"]] = (candidates, _stated(match["new"]), _stated(match["second_old"]))
    return pairs


def _class_readings() -> list[str]:
    match = _CLASS_READINGS.search(_w_changelog_line())
    assert match is not None
    *plain, short_i, short_u = match.groups()
    return [*plain, short_i + short_i[-1], short_u + short_u[-1]]


def _odia_words() -> set[str]:
    return {token for value in get_dictionary().values() for token in _ODIA_RUN.findall(unicodedata.normalize("NFC", value))}


def test_the_changelog_w_line_is_its_pinned_wording_around_the_examples() -> None:
    line = _w_changelog_line()
    split = _SPLIT_EXAMPLE.sub(lambda match: "<split>" + (f" ({match['count']} aksharas)" if match["count"] else ""), line)
    outline = _ALREADY_EXAMPLE.sub("<already>", _PAIR_EXAMPLE.sub("<pair>", split))
    assert outline == _W_LINE_OUTLINE


def test_each_changelog_type_odia_example_agrees_in_number_with_its_inputs() -> None:
    for match in _PAIR_EXAMPLE.finditer(_w_changelog_line()):
        one = match["second"] is None
        assert (match["verb"], match["pronoun"], match["second_old"] is None) == (
            ("gives", "it", True) if one else ("give", "they", False)
        ), match[0]


def test_each_changelog_type_odia_example_gives_its_stated_new_output_in_its_stated_call_mode() -> None:
    for typed, (candidates, new, _old) in _changelog_pairs().items():
        assert roman.type_odia(typed, candidates=candidates) == new, typed


def test_each_changelog_type_odia_example_states_the_pinned_pre_fix_output_as_its_old_one() -> None:
    pairs = _changelog_pairs()
    assert set(pairs) == set(_PRE_FIX_OUTPUT)
    for typed, (_candidates, new, old) in pairs.items():
        assert old == _PRE_FIX_OUTPUT[typed], typed
        assert new != old, typed


def test_each_changelog_split_example_matches_live_split_and_its_stated_count() -> None:
    examples = list(_SPLIT_EXAMPLE.finditer(_w_changelog_line()))
    assert {match["text"] for match in examples} == set(_PRE_FIX_SPLIT)
    for match in examples:
        parts = ast.literal_eval(match["parts"])
        assert syllable.split(match["text"]) == parts, match["text"]
        assert syllable.count(match["text"]) == len(parts), match["text"]
        if match["count"] is not None:
            assert syllable.count(match["text"]) == _COUNT_WORDS[match["count"]], match["text"]


def test_the_changelog_old_split_rule_gives_the_pinned_pre_fix_split_and_count() -> None:
    for match in _SPLIT_EXAMPLE.finditer(_w_changelog_line()):
        parts = ast.literal_eval(match["parts"])
        old_parts = [piece for part in parts for piece in re.split("(ୱ)", part) if piece]
        old_count = sum("ୱ" not in piece and unicodedata.category(piece[0]) == "Lo" for piece in old_parts)
        assert (old_parts, old_count) == _PRE_FIX_SPLIT[match["text"]], match["text"]


def test_the_changelog_already_gave_example_matches_live_and_pinned_pre_fix_output() -> None:
    [(first, second, first_output, second_output)] = _ALREADY_EXAMPLE.findall(_w_changelog_line())
    for typed, output in ((first, first_output), (second, second_output)):
        assert roman.type_odia(typed) == output == _UNCHANGED_NEAR_MISSES[typed], typed


def test_case_and_vowel_runs_do_not_change_what_a_changelog_class_reading_types() -> None:
    for reading in _class_readings():
        expected = roman.type_odia(reading, candidates=True)
        for run in (1, 2, 3):
            stretched = _W_VOWEL_RUN.sub(lambda vowels, run=run: vowels[0] * run, reading)
            mixed = "".join(letter.upper() if index % 2 else letter for index, letter in enumerate(stretched))
            for spelling in (stretched, stretched.upper(), stretched.title(), mixed):
                assert roman.type_odia(spelling, candidates=True) == expected, spelling


def test_every_changelog_class_reading_types_only_dictionary_words() -> None:
    words = _odia_words()
    for reading in _class_readings():
        assert set(roman.type_odia(reading, candidates=True)) <= words, reading


@pytest.mark.parametrize(("typed", "output"), _UNCHANGED_NEAR_MISSES.items())
def test_inputs_outside_the_changelog_class_keep_their_pre_fix_output(typed: str, output: str | list[str]) -> None:
    assert roman.type_odia(typed, candidates=isinstance(output, list)) == output


def test_fold_and_flap_rules_are_visible() -> None:
    assert roman.type_odia("dadha") == "ଦାଢ଼ା"
    assert roman.type_odia("kii") == "କି"
    assert roman.type_odia("bahuuta") == "ବହୁତ"
    assert roman.type_odia("aaaa") == "ଆ"
    assert "ସାଇଟୋୋକାଇନ୍ସିସ୍" not in roman.type_odia("saitookainsis", candidates=True)
    assert roman.type_odia("sidirigudika") == "ସିଡ଼ିଡ଼ିଗୁଡ଼ିକ"
    assert roman.type_odia("win", candidates=True) == ["ୱିନ୍", "ୱିଂ"]
    assert roman.type_odia("wa") == "ୱା"
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
    typing = "`roman.type_odia` needs a release newer than 0.2.0: it raises `AttributeError` on 0.2.0"
    root = Path(__file__).resolve().parent.parent
    for path in ("docs/index.md", "docs/llms.txt", "CHANGELOG.md"):
        text = " ".join((root / path).read_text(encoding="utf-8").split())
        assert typing in text
        if path != "CHANGELOG.md":
            assert sentence in text


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
