import random
import time
import typing
from typing import Any

import pytest

from openodia import pii
from openodia.pii import _detect

from .test_pii import kinds


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("alice@www.example.com", "<EMAIL>"),
        ("x www.foo@bar.com", "x <EMAIL>"),
        ("tel:+919876543210", "tel:<PHONE>"),
        ("tel:00919876543210.", "tel:<PHONE>."),
        ("91 9876543210", "<PHONE>"),
        ("91-9876543210", "<PHONE>"),
        ("(+91) 9876543210", "<PHONE>"),
        ("(+91)9876543210", "<PHONE>"),
        ("+91 (98765) 43210", "+91 (98765) 43210"),
        ("9876543210ABCPE1234F", "<PHONE><PAN>"),
        ("ABCPE1234F9876543210", "<PAN><PHONE>"),
        ("a@b.comwww.x.com", "<EMAIL>"),
        ("a@b.com-a@b.com", "<EMAIL>-<EMAIL>"),
        ("ଇମେଲa@b.com", "ଇମେଲ<EMAIL>"),
        ("ଲିଙ୍କwww.x.com", "ଲିଙ୍କ<URL>"),
        ("9876543210a@b.com", "<EMAIL>"),
        ("http://u@h.com/9876543210", "<URL>"),
    ],
)
def test_mask_never_leaves_part_of_a_value_visible(text: str, masked: str) -> None:
    assert pii.mask(text) == masked
    assert pii.mask(masked) == masked


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("91 9876543210", "91 9876543210"),
        ("(+91) 9876543210", "(+91) 9876543210"),
        ("tel:+919876543210", "+919876543210"),
        ("191 9876543210", "9876543210"),
        ("x91 9876543210", "91 9876543210"),
    ],
)
def test_phone_takes_its_country_code(text: str, expected: str) -> None:
    assert kinds(text) == [("PHONE", expected)]


def test_the_longest_overlapping_match_decides_the_type() -> None:
    assert kinds("x www.foo@bar.com") == [("EMAIL", "www.foo@bar.com")]
    assert kinds("www.foo@bar.com/x") == [("URL", "www.foo@bar.com/x")]
    assert kinds("tel:+919876543210") == [("PHONE", "+919876543210")]
    assert kinds("919876543210") == [("AADHAAR", "919876543210")]


def any_value(value: object) -> Any:
    return value


def candidate(start: int, end: int, kind: str, confidence: float = 0.9) -> _detect._Candidate:
    return _detect._Candidate(start, end, kind, confidence)


def test_partial_overlaps_merge_into_one_span_typed_by_the_longer_match() -> None:
    merged = _detect._merge([candidate(0, 6, "PHONE"), candidate(4, 14, "AADHAAR", 0.5), candidate(14, 16, "PAN")])
    assert [(c.start, c.end, c.kind, c.confidence) for c in merged] == [(0, 14, "AADHAAR", 0.5), (14, 16, "PAN", 0.9)]


def test_equal_length_overlaps_fall_back_to_the_documented_order() -> None:
    merged = _detect._merge([candidate(0, 5, "PHONE"), candidate(0, 5, "URL"), candidate(0, 5, "EMAIL")])
    assert [c.kind for c in merged] == ["EMAIL"]


def test_a_contained_match_never_shrinks_the_span() -> None:
    merged = _detect._merge([candidate(0, 20, "URL"), candidate(5, 8, "PHONE"), candidate(18, 25, "EMAIL")])
    assert [(c.start, c.end) for c in merged] == [(0, 25)]


FRAGMENTS = [
    "9876543210",
    "98765 43210",
    "+91",
    "91 ",
    "(+91) ",
    "0",
    "234567890124",
    "2345 6789 0124",
    "a@b.com",
    "x.y@z.co.in",
    "www.a.com",
    "https://h.org/p?q=1",
    "ABCPE1234F",
    "PIN 751001",
    "pin",
    " ",
    "-",
    ".",
    ",",
    "@",
    "/",
    "\n",
    "ମୋ ଫୋନ ",
    "୯୮୭୬୫୪୩୨୧୦",
    "abc",
    "A",
    "5",
    "1234",
    "tel:",
    "<PHONE>",
    "<URL>",
    "ଓ",
    "।",
    "9",
    "78",
]


def random_text(rng: random.Random) -> str:
    return "".join(rng.choice(FRAGMENTS) for _ in range(rng.randint(1, 12)))


def test_mask_is_idempotent_on_random_glued_input() -> None:
    rng = random.Random(281)
    for _ in range(4000):
        text = random_text(rng)
        once = pii.mask(text)
        assert pii.mask(once) == once, text


def test_detected_entities_are_sorted_and_never_overlap_on_random_input() -> None:
    rng = random.Random(282)
    for _ in range(2000):
        text = random_text(rng)
        entities = pii.detect(text)
        for entity in entities:
            assert text[entity.start : entity.end] == entity.text
        for first, second in zip(entities, entities[1:], strict=False):
            assert first.end <= second.start, text


@pytest.mark.parametrize(
    "unit",
    [
        "9876 ",
        "http://a ",
        "a@b.com ",
        "www.a.com ",
        "9876543210 ",
        "2345 6789 0124 ",
        "PIN 751001 ",
        "ABCPE1234F ",
        "a.",
        "a@",
        "a-",
        "www.",
        "http://",
        "9 ",
        "+91 ",
        "ମୋ ",
    ],
)
def test_detection_scales_linearly_with_input_size(unit: str) -> None:
    text = unit * 100_000
    started = time.perf_counter()
    pii.mask(text)
    assert time.perf_counter() - started < 10


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("a" * 1_000_000 + "@", id="long-local-part"),
        pytest.param("@" + "b." * 500_000, id="dotted-run-after-at"),
        pytest.param("www." + "." * 1_000_000, id="www-then-dots"),
        pytest.param("a@" + "b-" * 500_000, id="dashed-domain"),
    ],
)
def test_detection_survives_one_huge_token(text: str) -> None:
    started = time.perf_counter()
    pii.mask(text)
    assert time.perf_counter() - started < 10


def test_types_must_be_a_list_not_a_bare_string() -> None:
    with pytest.raises(TypeError, match="types must be a list of PII type names, not a single string"):
        pii.detect("a@b.com", types=any_value("EMAIL"))
    with pytest.raises(TypeError, match="types must be a list"):
        pii.mask("a@b.com", types=any_value("EMAIL"))


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf"), True, "0.5", None])
def test_min_confidence_must_be_a_number_between_zero_and_one(value: object) -> None:
    with pytest.raises(ValueError, match="min_confidence must be a number between 0 and 1"):
        pii.detect("a@b.com", min_confidence=any_value(value))


@pytest.mark.parametrize("value", [0, 1, 0.5, 0.0, 1.0])
def test_min_confidence_bounds_are_inclusive(value: float) -> None:
    pii.detect("a@b.com", min_confidence=any_value(value))


@pytest.mark.parametrize("value", [None, b"secret-9876543210", 98765, ["a@b.com"]])
def test_text_must_be_a_str_and_the_error_does_not_echo_it(value: object) -> None:
    for call in (pii.detect, pii.mask):
        with pytest.raises(TypeError, match=r"text must be str, got \w+") as error:
            call(any_value(value))
        assert "secret" not in str(error.value)
        assert "9876543210" not in str(error.value)


def test_unknown_type_error_names_only_the_type() -> None:
    with pytest.raises(ValueError, match="unknown PII type 'NAME'") as error:
        pii.detect("secret 9876543210", types=["NAME"])
    assert "9876543210" not in str(error.value)


def test_pii_type_literal_matches_the_exported_names() -> None:
    assert typing.get_args(pii.PIIType) == pii.PII_TYPES


@pytest.mark.parametrize(("text", "found"), [("a@b.c", False), ("a@b.co", True), ("a@b.c1", False), ("a@b.com", True)])
def test_email_needs_a_top_level_domain_of_two_letters(text: str, found: bool) -> None:
    assert bool(pii.detect(text)) is found


VERHOEFF_NUMBERS = [
    "819326751928",
    "485703102046",
    "923284385715",
    "256917239480",
    "737444870156",
    "365590026940",
    "920159912476",
    "653032698894",
    "967271490539",
    "913655564274",
    "727166841670",
    "570988240520",
]


def test_verhoeff_numbers_exercise_every_permutation_row_and_digit() -> None:
    covered = {(position % 8, int(digit)) for number in VERHOEFF_NUMBERS for position, digit in enumerate(reversed(number))}
    assert covered == {(row, digit) for row in range(8) for digit in range(10)}


@pytest.mark.parametrize("number", VERHOEFF_NUMBERS)
def test_verhoeff_accepts_valid_numbers_and_rejects_every_single_digit_error_and_transposition(number: str) -> None:
    from openodia.pii._verhoeff import is_valid

    assert is_valid(number)
    for index, digit in enumerate(number):
        for other in "0123456789".replace(digit, ""):
            assert not is_valid(number[:index] + other + number[index + 1 :])
    for index in range(len(number) - 1):
        if number[index] != number[index + 1]:
            swapped = number[:index] + number[index + 1] + number[index] + number[index + 2 :]
            assert not is_valid(swapped)


def test_masking_a_glued_neighbour_exposes_the_value_before_it() -> None:
    assert pii.mask("ABCPE1234Fhttps://x.com") == "<PAN><URL>"
    assert pii.mask("9876543210PIN 751001") == "<PHONE>PIN <PINCODE>"


def test_custom_placeholder_that_looks_like_pii_cannot_loop_forever() -> None:
    assert pii.mask("call 9876543210", placeholder=lambda entity: entity.text + " ") == "call 9876543210" + " " * 10


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("9876543210ABCPE1234F", [("PHONE", "9876543210"), ("PAN", "ABCPE1234F")]),
        ("ABCPE1234F9876543210", [("PAN", "ABCPE1234F"), ("PHONE", "9876543210")]),
        ("9876543210PIN 751001", [("PHONE", "9876543210"), ("PINCODE", "751001")]),
        ("alice@www.example.com", [("EMAIL", "alice@www.example.com")]),
        ("awww.example.com", []),
        ("foo.www.example.com", []),
        ("see (www.example.com)", [("URL", "www.example.com")]),
    ],
)
def test_glued_values_are_detected_one_by_one(text: str, expected: list[tuple[str, str]]) -> None:
    assert kinds(text) == expected


def test_mask_materialises_types_once_so_an_iterator_is_not_exhausted_by_the_first_pass() -> None:
    glued = "ABCPE1234Fhttps://x.com"
    assert pii.mask(glued, types=iter(["PAN", "URL"])) == "<PAN><URL>"
    assert pii.mask(glued, types=(kind for kind in ["PAN", "URL"])) == pii.mask(glued, types=["PAN", "URL"])


def test_mask_validates_types_even_when_given_an_iterator() -> None:
    with pytest.raises(ValueError, match="unknown PII type 'NOPE'"):
        pii.mask("a@b.com", types=iter(["NOPE"]))
    with pytest.raises(TypeError, match="not a single string"):
        pii.mask("a@b.com", types="PAN")


def test_detect_reads_a_types_iterator_once() -> None:
    assert [e.type for e in pii.detect("ABCPE1234F a@b.com", types=iter(["PAN"]))] == ["PAN"]


def test_a_url_that_swallows_many_phone_candidates_is_still_linear() -> None:
    text = "https://x.com/" + "9876543210-" * 30_000
    started = time.perf_counter()
    [entity] = pii.detect(text)
    assert time.perf_counter() - started < 10
    assert (entity.type, entity.start, entity.end) == ("URL", 0, len(text))


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("HTTPS://x.com/?token=s", "<URL>"),
        ("Http://x.com/a", "<URL>"),
        ("WWW.example.com", "<URL>"),
        ("Www.example.com/path.", "<URL>."),
        ("see wWw.a.com now", "see <URL> now"),
        ("xWWW.example.com", "xWWW.example.com"),
    ],
)
def test_url_scheme_and_www_match_in_any_letter_case(text: str, masked: str) -> None:
    assert pii.mask(text) == masked
