import ast
import doctest
import json
import random
import re
import time
import unicodedata
from pathlib import Path
from typing import SupportsIndex

import pytest

import openodia.legacy
from openodia import legacy
from openodia.legacy import _convert

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "legacy_ortt_sentences.json"
RULE_PAGES = ("CHANGELOG.md", "docs/index.md", "openodia/legacy/__init__.py")
CONVERT_PAGES = ("README.md", "docs/index.md", "docs/llms.txt", "CHANGELOG.md")
SIGNS = "ାିୀୁୂୃେୈୋୌଁଂଃ"
SIGN_BEFORE_HALANT = re.compile(f"[{SIGNS}]୍")
SIGN_BEFORE_NUKTA = re.compile(f"[{SIGNS}]଼")
JOINER_OR_HALANT_BEFORE_NUKTA = re.compile("[\u200c\u200d୍]଼")
FONT = _convert._FONTS["ORTTSarala"]


def ortt(text: str) -> str:
    return legacy.to_unicode(text, font="ORTTSarala")


def _page(name: str) -> str:
    return " ".join((ROOT / name).read_text(encoding="utf-8").replace("``", "`").split())


def _keys(*extra: str) -> list[str]:
    keys = {char for source, _target in FONT.pairs for char in source if not "\u0b00" <= char <= "\u0b7f"}
    return sorted(keys | {FONT.marker, FONT.reph, *FONT.halves, *extra} - {"ା"})


def test_supported_fonts_is_ortt_only() -> None:
    assert legacy.SUPPORTED_FONTS == ("ORTTSarala",)


def test_an_unknown_font_is_rejected_with_the_supported_names() -> None:
    with pytest.raises(ValueError, match=r"unknown font 'AkrutiOriSarala'; choose from ORTTSarala"):
        legacy.to_unicode("K", font="AkrutiOriSarala")


def test_empty_text_stays_empty() -> None:
    assert ortt("") == ""


def test_the_fifty_known_sentences_convert() -> None:
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))["ORTTSarala"]
    assert len(rows) == 50
    for row in rows:
        assert not any("\u0b00" <= char <= "\u0b7f" for char in row["legacy"])
        assert row["unicode"].strip()
        assert ortt(row["legacy"]) == row["unicode"]


def test_decoded_bytes_convert() -> None:
    assert ortt(legacy.decode(b"JX\xcf\xdeA")) == "ଓଡ଼ିଆ"
    assert ortt(legacy.decode(b"\x85")) == "ଣ୍ଠ"
    assert ortt(b"\x85".decode("latin-1")) == "\x85"


@pytest.mark.parametrize(
    ("byte", "expected"),
    [
        (0x83, "„"),
        (0x85, "ଣ୍ଠ"),
        (0x86, "ପ୍ଟ"),
        (0x87, "ୁ"),
        (0x91, "ଗ୍ଧ"),
        (0x92, "ଗ୍ଦ"),
        (0x93, "ପ୍ପ"),
        (0x94, "ଡ୍ଗ"),
        (0x95, "ବ୍ଧ"),
        (0x96, "ଳ୍କ"),
        (0x97, "ତ୍ସ"),
        (0x98, "୍ଳ"),
        (0x99, "ର୍ଁ"),
        (0x9A, "୍ୱ"),
        (0x9B, "୍ମ"),
        (0x9C, "କ୍ଟ"),
    ],
)
def test_bytes_that_only_cp1252_maps_convert(byte: int, expected: str) -> None:
    assert ortt(legacy.decode(bytes([byte]))) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ÒL", "କେ"),
        ("ÒLÐ", "କୋ"),
        ("ÒL×", "କୌ"),
        ("ÒLß", "କୈ"),
        ("LÞ", "କି"),
        ("LÙ", "ର୍କି"),
        ("lÙ", "ର୍କ୍ଷି"),
        ("Æ", "କ୍ଟ"),
        ("Òw", "ଦ୍ଧେ"),
        ("ÒXÏ", "ଡ଼େ"),
        ("LÕÐ", "କାଂ"),
        ("LÐÔ", "କ୍ୟା"),
        ("ÒLÕß", "କୈଂ"),
        ("LÔà", "ର୍କ୍ୟ"),
        ("LÐÔà", "ର୍କ୍ୟା"),
        ("12", "୧୨"),
        ("ÒLÔ×", "କ୍ୟୌ"),
        ("ÒLÔß", "କ୍ୟୈ"),
        ("ÒLÔ", "କ୍ୟେ"),
        ("L™", "ର୍କଁ"),
        ("crÔà", "ମର୍ତ୍ତ୍ୟ"),
        ("OãôÔg", "ଘ୍ୟୁୃୱ"),
        ("ÒLçL", "କ୍\u200dକେ"),
        ("LçLà", "ର୍କ୍\u200dକ"),
        ("LàçL", "ର୍କ୍\u200dକ"),
        ("K, M.", "ଔ, ଖ."),
        ("Óà", "ଃର୍"),
        ("ÒLàß", "ର୍କୈ"),
        ("ÒLà×", "ର୍କୌ"),
        ("ÒLàÜß", "ର୍କୈଁ"),
    ],
)
def test_matras_reph_and_conjuncts(source: str, expected: str) -> None:
    assert ortt(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("LÐÔ", "କ୍ୟା"),
        ("LÞÔ", "କ୍ୟି"),
        ("LÑÔ", "କ୍ୟୀ"),
        ("LÊÔ", "କ୍ୟୁ"),
        ("LËÔ", "କ୍ୟୂ"),
        ("LÌÔ", "କ୍ୟୃ"),
        ("ÒLÊÔ", "କ୍ୟେୁ"),
        ("ÒLßÔ", "କ୍ୟୈ"),
        ("ÒLÐÔ", "କ୍ୟୋ"),
        ("ÒL×Ô", "କ୍ୟୌ"),
        ("LÜÔ", "କ୍ୟଁ"),
        ("LÕÔ", "କ୍ୟଂ"),
        ("LÚÔ", "କ୍ୟିଁ"),
        ("ÒLÕÔ", "କ୍ୟେଂ"),
        ("ÒLÔÕ", "କ୍ୟେଂ"),
        ("LÔÜ", "କ୍ୟଁ"),
        ("ÒLÕÔß", "କ୍ୟୈଂ"),
        ("ÒLÔÕß", "କ୍ୟୈଂ"),
        ("ÒLÕÔ×", "କ୍ୟୌଂ"),
        ("ÒLÔÕ×", "କ୍ୟୌଂ"),
    ],
)
def test_a_ya_phala_goes_ahead_of_each_sign_typed_before_it(source: str, expected: str) -> None:
    assert ortt(source) == expected


KEY_ORDER_PAIRS = (
    ("ÒLÔçL", "ÒLçLÔ", "କ୍ୟ୍\u200dକେ", "କ୍\u200dକ୍ୟେ"),
    ("ÒLÔÍ", "ÒLÍÔ", "କ୍ୟ୍ରେ", "କ୍ର୍ୟେ"),
)


@pytest.mark.parametrize(("first", "second", "first_out", "second_out"), KEY_ORDER_PAIRS)
def test_subjoined_forms_keep_the_order_typed(first: str, second: str, first_out: str, second_out: str) -> None:
    assert ortt(first) == first_out
    assert ortt(second) == second_out


BOTH_ORDERS = (
    ("ÒLÕÔÍ", "ÒLÔÍÕ", "କ୍ୟ୍ରେଂ"),
    ("ÒLÜÔÍ", "ÒLÔÍÜ", "କ୍ୟ୍ରେଁ"),
    ("ÒLÕÔçL", "ÒLÔçLÕ", "କ୍ୟ୍\u200dକେଂ"),
    ("ÒLàÔß", "ÒLÔßà", "ର୍କ୍ୟୈ"),
    ("ÒLàÔ×", "ÒLÔ×à", "ର୍କ୍ୟୌ"),
    ("ÒLàÔÐ", "ÒLÔÐà", "ର୍କ୍ୟୋ"),
    ("ÒLÕÍ", "ÒLÍÕ", "କ୍ରେଂ"),
    ("ÒLÜÍ", "ÒLÍÜ", "କ୍ରେଁ"),
    ("ÒLàÍ", "ÒLÍà", "ର୍କ୍ରେ"),
    ("ÒLàçL", "ÒLçLà", "ର୍କ୍\u200dକେ"),
    ("ÒLàÍß", "ÒLÍßà", "ର୍କ୍ରୈ"),
    ("ÒLÕÍß", "ÒLÍÕß", "କ୍ରୈଂ"),
    ("LÓÊ", "LÊÓ", "କୁଃ"),
    ("ÒL™Ô", "ÒLÔ™", "ର୍କ୍ୟେଁ"),
    ("LÙÔ", "LÔÙ", "ର୍କ୍ୟି"),
    ("L™Ô", "LÔ™", "ର୍କ୍ୟଁ"),
    ("LÐÔÍ", "LÔÍÐ", "କ୍ୟ୍ରା"),
    ("LÜÔÍ", "LÔÍÜ", "କ୍ୟ୍ରଁ"),
    ("L™ÔÍ", "LÔÍ™", "ର୍କ୍ୟ୍ରଁ"),
    ("LÙÔ˜", "LÔ˜Ù", "ର୍କ୍ୟ୍ଳି"),
    ("LÐÔçL", "LÔçLÐ", "କ୍ୟ୍\u200dକା"),
    ("LÐÔçk", "LÔçkÐ", "କ୍ୟ୍\u200dହା"),
    ("LÐÔç¯", "LÔç¯Ð", "କ୍ୟ୍\u200dୟା"),
    ("LÐÔš", "LÔšÐ", "କ୍ୟ୍ୱା"),
    ("LÐÔçXÏ", "LÔçXÏÐ", "କ୍ୟ୍\u200dଡ଼ା"),
    ("LÐÔÍ˜", "LÔÍ˜Ð", "କ୍ୟ୍ର୍ଳା"),
    ("ÒLàß", "ÒLßà", "ର୍କୈ"),
    ("ÒLà×", "ÒL×à", "ର୍କୌ"),
    ("XÐÏ", "XÏÐ", "ଡ଼ା"),
    ("ÒXßÏ", "ÒXÏß", "ଡ଼ୈ"),
    ("ÒXàÏ", "ÒXÏà", "ର୍ଡ଼େ"),
    ("LÔÐÏ", "LÔÏÐ", "କ୍ୟ଼ା"),
    ("LÔÍÐÏ", "LÔÍÏÐ", "କ୍ୟ୍ର଼ା"),
    ("LçXÐÏ", "LçXÏÐ", "କ୍\u200dଡ଼ା"),
)


@pytest.mark.parametrize(("typed", "other_order", "expected"), BOTH_ORDERS)
def test_a_syllable_gives_the_same_output_in_either_key_order(typed: str, other_order: str, expected: str) -> None:
    assert len(BOTH_ORDERS) == 34
    assert ortt(typed) == expected
    assert ortt(other_order) == expected


YA_PHALA_SIGNS = ("Ð", "Þ", "Ñ", "Ê", "Ë", "Ì", "ÒÊ", "Òß", "ÒÐ", "Ò×", "Ü", "Õ", "Ú")


@pytest.mark.parametrize("sign", YA_PHALA_SIGNS)
def test_a_sign_typed_before_a_ya_phala_goes_after_a_subjoined_ra_typed_after_it(sign: str) -> None:
    assert len(YA_PHALA_SIGNS) == 13
    lead, key = ("Ò", sign[1]) if sign.startswith("Ò") else ("", sign)
    assert ortt(lead + "L" + key + "ÔÍ") == ortt(lead + "LÔÍ" + key)
    assert SIGN_BEFORE_HALANT.search(ortt(lead + "L" + key + "ÔÍ")) is None
    assert ortt(lead + "L" + key + "ÔÍ").startswith(("କ୍ୟ୍ର", "ର୍କ୍ୟ୍ର"))


def _single_keys(predicate: str) -> list[str]:
    return [source for source, target in FONT.pairs if len(source) == 1 and target and re.fullmatch(predicate, target)]


def test_every_sign_nasal_or_reph_typed_before_a_subjoined_form_matches_the_other_order() -> None:
    marks = [*_single_keys(f"[{SIGNS}{FONT.reph}]+"), *(half for half in FONT.halves if half != "ା"), FONT.reph]
    subjoined = _single_keys("୍.*")
    assert (len(marks), len(subjoined)) == (25, 22)
    for lead in ("", "Ò"):
        for mark in marks:
            for form in subjoined:
                typed = ortt(lead + "L" + mark + form)
                assert typed == ortt(lead + "L" + form + mark), (lead, mark, form)
                assert SIGN_BEFORE_HALANT.search(typed) is None


def test_no_two_key_syllable_leaves_a_sign_before_a_halant_or_nukta_or_a_nukta_after_a_halant() -> None:
    keys = _keys("Ô", "଼")
    assert len(keys) == 189
    inputs = [lead + "L" + first + ya + second for lead in ("", "Ò") for first in keys for ya in ("", "Ô") for second in keys]
    assert len(inputs) == 142884
    for text in inputs:
        output = ortt(text)
        assert SIGN_BEFORE_HALANT.search(output) is None, text
        assert SIGN_BEFORE_NUKTA.search(output) is None, text
        assert JOINER_OR_HALANT_BEFORE_NUKTA.search(output) is None, text


def test_seeded_random_text_leaves_no_sign_before_a_halant_or_nukta() -> None:
    keys = _keys("଼")
    picker = random.Random(301)
    inputs = ["".join(picker.choices(keys, k=picker.randint(1, 8))) for _ in range(20000)]
    assert len(inputs) == 20000
    for text in inputs:
        output = ortt(text)
        assert SIGN_BEFORE_HALANT.search(output) is None, text
        assert SIGN_BEFORE_NUKTA.search(output) is None, text


@pytest.mark.parametrize(
    ("text", "expected"),
    [("ÒLçÏ", "କ଼୍\u200dେ"), ("LçÏ", "କ଼୍\u200d"), ("LÍçÏ", "କ୍ର଼୍\u200d"), ("ÒLçÐÏ", "କ଼୍\u200dୋ"), ("LXÏ", "କଡ଼")],
)
def test_a_nukta_goes_on_the_consonant_before_a_trailing_halant_or_joiner(text: str, expected: str) -> None:
    assert ortt(text) == expected


def test_a_nukta_does_not_cross_a_syllable() -> None:
    assert ortt("L1Ï") == "କ୧଼"
    assert ortt("LAÏ") == "କଆ଼"
    assert ortt("L ÏX") == "କ ଼ଡ"
    assert ortt("XÐÏÏ") == "ଡ଼଼ା"


def test_a_nukta_in_a_syllable_with_no_consonant_goes_ahead_of_its_vowel_signs() -> None:
    assert ortt("ÐÏà") == "଼ାର୍"
    assert ortt("ÏÐà") == "଼ାର୍"
    assert ortt("ÐÊÏ") == "଼ାୁ"
    assert ortt("çÏ") == "୍\u200d଼"


def test_signs_typed_without_a_base_letter_go_after_the_subjoined_form() -> None:
    assert ortt("ôÒð") == "୍ନୃେ"
    assert ortt("L ÊÔ") == "କ ୍ୟୁ"


def test_a_marker_before_a_consonant_starts_the_next_syllable() -> None:
    assert ortt("LÒL") == "କକେ"
    assert ortt("ÒLÒ") == "କେେ"
    assert ortt("Ò") == "େ"


def test_every_numeric_separator_in_a_run_converts() -> None:
    assert ortt("1Ð2Ð3") == "୧|୨|୩"
    assert ortt("1Ð2") == "୧|୨"
    assert ortt("1Ð2Ð3Ð4Ð5") == "୧|୨|୩|୪|୫"


def _rules(page: str) -> str:
    start = "After the glyph table, `to_unicode` rebuilds each syllable"
    end = "(`1Ð2Ð3` gives `୧|୨|୩`)."
    text = _page(page)
    assert text.count(start) == 1, page
    return text[text.index(start) : text.index(end, text.index(start)) + len(end)]


def test_the_rules_paragraph_is_the_same_on_every_page() -> None:
    assert len({_rules(page) for page in RULE_PAGES}) == 1


BOTH_GIVE = re.compile(r"`([^`]+)` and `([^`]+)` both give `([^`]+)`")
GIVES = re.compile(r"\(`([^`]+)` gives `([^`]+)`\)")


@pytest.mark.parametrize("page", RULE_PAGES)
def test_every_example_in_the_rules_is_what_to_unicode_gives(page: str) -> None:
    text = _rules(page)
    both = BOTH_GIVE.findall(text)
    gives = GIVES.findall(text)
    assert (len(both), len(gives)) == (3, 1)
    for typed, other_order, expected in both:
        assert ortt(typed) == expected
        assert ortt(other_order) == expected
    for typed, expected in gives:
        assert ortt(typed) == expected


EXAMPLE = re.compile(r'^legacy\.to_unicode\(legacy\.decode\((b"[^"]*")\), font="ORTTSarala"\)  # \'([^\']*)\'$', re.M)


@pytest.mark.parametrize("page", ("README.md", "docs/index.md"))
def test_the_conversion_example_on_each_page_is_what_to_unicode_gives(page: str) -> None:
    examples = EXAMPLE.findall((ROOT / page).read_text(encoding="utf-8"))
    assert len(examples) == 1
    for data, expected in examples:
        assert ortt(legacy.decode(ast.literal_eval(data))) == expected


@pytest.mark.parametrize("page", CONVERT_PAGES)
def test_pages_name_to_unicode_and_its_one_font(page: str) -> None:
    text = _page(page)
    assert '`legacy.to_unicode(text, font="ORTTSarala")` converts those keystrokes to NFC Unicode Odia' in text
    assert '`SUPPORTED_FONTS` is `("ORTTSarala",)`.' in text


def test_the_module_examples_run() -> None:
    result = doctest.testmod(openodia.legacy, optionflags=doctest.ELLIPSIS)
    assert result == doctest.TestResults(failed=0, attempted=4)


LONG_SHAPES = {
    "nuktas on the base": ("L", "Ï"),
    "nuktas after a joiner": ("Lç", "Ï"),
    "nuktas after a ya-phala": ("LÔ", "Ï"),
    "nasals": ("L", "Õ"),
    "vowel signs": ("L", "Ð"),
    "right halves after a left matra": ("ÒL", "ß"),
    "left matras": ("", "Ò"),
    "rephs": ("L", "à"),
    "subjoined consonants": ("L", "çL"),
    "ya-phalas": ("L", "Ô"),
    "joiners": ("Lç", "\u200d"),
    "left matras after a consonant": ("L", "Ò"),
    "syllables": ("", "LÐ"),
    "numeric separators": ("1", "Ð1"),
}


@pytest.mark.parametrize(("head", "unit"), LONG_SHAPES.values(), ids=LONG_SHAPES)
def test_string_work_grows_linearly_with_the_input(head: str, unit: str, monkeypatch: pytest.MonkeyPatch) -> None:
    assert len(LONG_SHAPES) == 14
    work: list[int] = []

    class Measured(str):
        def __getitem__(self, key: SupportsIndex | slice) -> str:
            value = super().__getitem__(key)
            work.append(len(value))
            return Measured(value)

        def __add__(self, other: str) -> str:
            work.append(len(self) + len(other))
            return Measured(super().__add__(other))

        def __radd__(self, other: str) -> str:
            work.append(len(self) + len(other))
            return Measured(other.__add__(self))

    replace = _convert._replace

    def measured(text: str, font: _convert._Font) -> str:
        return Measured(replace(text, font))

    monkeypatch.setattr(_convert, "_replace", measured)

    def steps(count: int) -> int:
        work.clear()
        legacy.to_unicode(head + unit * count, font="ORTTSarala")
        return sum(work)

    small = steps(500)
    large = steps(2000)
    assert small >= 500
    assert large < small * 5


BUDGET_SECONDS = 4.0
BUDGET_REPEATS = 200_000


@pytest.mark.parametrize(("head", "unit"), LONG_SHAPES.values(), ids=LONG_SHAPES)
def test_200000_repeats_convert_within_the_time_budget(head: str, unit: str) -> None:
    text = head + unit * BUDGET_REPEATS
    times: list[float] = []
    for _ in range(2):
        start = time.perf_counter()
        legacy.to_unicode(text, font="ORTTSarala")
        times.append(time.perf_counter() - start)
        if times[-1] < BUDGET_SECONDS:
            break
    assert min(times) < BUDGET_SECONDS, times


ODIA_CONSONANTS = [
    chr(code)
    for code in range(0x0B15, 0x0B80)
    if unicodedata.name(chr(code), "").startswith("ORIYA LETTER") and code not in (0x0B60, 0x0B61)
]


def test_a_left_matra_goes_after_every_odia_consonant() -> None:
    assert len(ODIA_CONSONANTS) == 38
    for consonant in ODIA_CONSONANTS:
        assert ortt("Ò" + consonant) == unicodedata.normalize("NFC", consonant + "େ"), consonant


@pytest.mark.parametrize("sign", "ାିୀୁୂୃେୈୋୌଁଂଃ")
def test_each_vowel_sign_and_nasal_typed_before_a_ya_phala_goes_after_it(sign: str) -> None:
    assert ortt("L" + sign + "Ô") == "କ୍ୟ" + sign


def test_a_halant_with_a_zero_width_non_joiner_is_part_of_the_syllable() -> None:
    assert ortt("ÒL\u0b4d\u200cL") == "କ୍\u200cକେ"
    assert ortt("ÒL\u0b4d\u200c\u200dL") == "କ୍\u200c\u200dକେ"


def test_the_first_right_half_typed_joins_the_left_matra() -> None:
    assert ortt("ÒLßÐ") == "କୈା"
    assert ortt("ÒLÐß") == "କୋß"


@pytest.mark.parametrize("pad", [" ", "\t", "\n", "\r", "\r\n", "  \r\n\r\n ", "\u00a0"])
def test_padding_around_keystrokes_is_kept_exactly(pad: str) -> None:
    assert ortt(pad) == pad
    assert ortt(pad + "L" + pad + "XÏÐ" + pad) == pad + "କ" + pad + "ଡ଼ା" + pad


def test_long_text_keeps_every_syllable_and_line_break() -> None:
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))["ORTTSarala"]
    text = "\r\n".join(row["legacy"] for row in rows) + "\r\n"
    assert len(text) > 256
    assert ortt(text) == "\r\n".join(row["unicode"] for row in rows) + "\r\n"
    assert ortt("LÐ " * 300) == "କା " * 300
