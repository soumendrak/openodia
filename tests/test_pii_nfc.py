import itertools
import random
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from collections.abc import Callable
from types import SimpleNamespace
from typing import Literal

import pytest

from openodia import pii
from openodia.pii import _detect

ROOT = Path(__file__).resolve().parents[1]
NFC_SENTENCES = (
    "Text that is not in NFC is also searched in its NFC form, and each match is mapped back to offsets in the"
    " text you passed, so a PAN followed by a decomposed accented letter is found.",
    "In text that is not in NFC, a match found in the NFC form whose last letter carries 32 or more combining marks"
    " also covers those marks.",
)

EXPANDING = ["ବ\u0b5c ଘର", "କ\u0b4d\u0b3c", "ପ\u0b5dା", "a\u0301\u0323", "ଉ\u0b5cାଣଗୁଡିକ"]


def test_a_pan_before_a_decomposed_accented_letter_is_found() -> None:
    text = "ABCPE1234Fe\u0301"
    assert [(entity.type, entity.text) for entity in pii.detect(text)] == [("PAN", "ABCPE1234F")]
    assert pii.mask(text) == "<PAN>e\u0301"


def test_text_that_is_already_nfc_is_not_mapped() -> None:
    assert _detect._nfc_bounds("ABCPE1234Fé") == ("ABCPE1234Fé", None)


@pytest.mark.parametrize("text", EXPANDING)
def test_expanded_nfc_keeps_offsets_inside_the_original_text(text: str) -> None:
    assert len(EXPANDING) == 5
    nfc_text, bounds = _detect._nfc_bounds(text)
    assert nfc_text == unicodedata.normalize("NFC", text)
    assert bounds is not None
    assert len(bounds) == len(nfc_text) + 1
    assert bounds[0] == 0
    assert bounds[-1] == len(text)
    assert bounds == sorted(bounds)
    full = text + " ABCPE1234F"
    assert [(entity.type, entity.start, entity.end) for entity in pii.detect(full)] == [("PAN", len(text) + 1, len(full))]
    assert pii.mask(full) == text + " <PAN>"


def test_detect_finishes_when_nfc_expands_a_letter() -> None:
    script = f"""
from openodia import pii
for text in {EXPANDING!r}:
    full = text + " ABCPE1234F"
    assert [(entity.start, entity.end) for entity in pii.detect(full)] == [(len(text) + 1, len(full))], text
    assert pii.mask(full) == text + " <PAN>", text
print("ok")
"""
    completed = subprocess.run([sys.executable, "-c", script], check=False, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok"


def test_a_decomposed_letter_before_a_span_does_not_shift_it() -> None:
    for prefix in ("ମୋ ଗୌରବ ", "ଗୋ"):
        text = unicodedata.normalize("NFD", prefix) + "a@b.com"
        assert pii.mask(text) == unicodedata.normalize("NFD", prefix) + "<EMAIL>"
        for entity in pii.detect(text):
            assert text[entity.start : entity.end] == entity.text


@pytest.mark.parametrize(("marks", "masked_tail"), [(31, "\u0302" * 31), (32, "")])
def test_runs_up_to_32_code_points_map_exactly_and_longer_runs_map_to_the_run_end(marks: int, masked_tail: str) -> None:
    prefix = unicodedata.normalize("NFD", "ଗୋ ")
    text = prefix + "x@y.com" + "\u0302" * marks
    assert pii.mask(text) == prefix + "<EMAIL>" + masked_tail


def test_offsets_after_a_long_run_that_nfc_shortens_point_at_the_entities() -> None:
    run = "e" + "\u0301\u0323" * 30
    assert len(run) == 61
    assert len(unicodedata.normalize("NFC", run)) == 60
    text = run + " ABCPE1234F 9876543210 x"
    entities = pii.detect(text, types=["PAN", "PHONE"])
    assert [(entity.type, entity.start, entity.end) for entity in entities] == [("PAN", 62, 72), ("PHONE", 73, 83)]
    assert pii.mask(text, types=["PAN", "PHONE"]) == run + " <PAN> <PHONE> x"


def test_a_short_run_that_nfc_shortens_maps_each_letter_to_its_own_end() -> None:
    assert _detect._nfc_bounds("ABCPE1234Fe\u0301x") == ("ABCPE1234Féx", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13])


def test_a_long_run_maps_every_letter_to_the_run_end() -> None:
    run = "e" + "\u0301" + "\u0323" * 32
    nfc_text, bounds = _detect._nfc_bounds(run + "x")
    assert nfc_text == unicodedata.normalize("NFC", run) + "x"
    assert len(nfc_text) == 34
    assert bounds == [0] + [34] * 33 + [35]


@pytest.mark.parametrize("text", ["a@b.co\u0301", "foo@example.com\u0301", "ଗୋ\u0301 a@b.co\u0301"])
def test_an_ascii_email_before_a_combining_accent_is_masked(text: str) -> None:
    masked = pii.mask(text, types=["EMAIL"])
    assert "@" not in masked
    assert masked.endswith("<EMAIL>\u0301")
    for entity in pii.detect(text):
        assert text[entity.start : entity.end] == entity.text


def test_odia_digits_keep_numeric_boundaries_when_the_text_is_not_nfc() -> None:
    text = "a\u0301 ୧9876543210"
    assert pii.detect(text, types=["PHONE"]) == []
    assert pii.mask(text, types=["PHONE"]) == text
    phone = "a\u0301 9876543210"
    assert pii.mask(phone, types=["PHONE"]) == "a\u0301 <PHONE>"


ODIA_AND_MARKS = [chr(code) for code in range(0x0B00, 0x0B80)] + ["a", "e", "\u0301", "\u0323", "\u200c", "\u200d", " "]


def _assert_maps_to_nfc(text: str) -> None:
    nfc_text, bounds = _detect._nfc_bounds(text)
    assert nfc_text == unicodedata.normalize("NFC", text), text
    if bounds is None:
        assert unicodedata.is_normalized("NFC", text)
        return
    assert len(bounds) == len(nfc_text) + 1
    assert bounds[0] == 0
    assert bounds[-1] == len(text)
    assert all(left <= right for left, right in itertools.pairwise(bounds))


def test_every_pair_of_odia_code_points_and_marks_maps_to_its_nfc_form() -> None:
    assert len(ODIA_AND_MARKS) == 135
    for pair in itertools.product(ODIA_AND_MARKS, repeat=2):
        _assert_maps_to_nfc("".join(pair))


def test_seeded_random_odia_text_maps_to_its_nfc_form() -> None:
    rng = random.Random(300)
    for _ in range(20_000):
        _assert_maps_to_nfc("".join(rng.choice(ODIA_AND_MARKS) for _ in range(rng.randint(1, 12))))


def test_a_vowel_sign_composes_with_the_sign_before_it() -> None:
    assert _detect._nfc_bounds("\u0b15\u0b47\u0b3e") == ("\u0b15\u0b4b", [0, 1, 3])


MARK_RUN_SHAPES: dict[str, Callable[[int], str]] = {
    "one long run": lambda count: "a" + "\u0323" * count + " ",
    "many short runs": lambda count: "a\u0323" * count + " ",
    "many runs of 33 marks": lambda count: ("a" + "\u0323" * 33) * (count // 33) + " ",
    "a short run then many letters": lambda count: "a\u0323" + "x" * count + " ",
    "letters that NFC splits into astral pairs": lambda count: "\U0001d15e" * count + " ",
}


def _shape(name: str, count: int) -> str:
    return MARK_RUN_SHAPES[name](count) + "a@b.com"


def test_mark_run_shapes_cover_long_runs_short_runs_and_expanding_letters() -> None:
    assert list(MARK_RUN_SHAPES) == [
        "one long run",
        "many short runs",
        "many runs of 33 marks",
        "a short run then many letters",
        "letters that NFC splits into astral pairs",
    ]
    assert unicodedata.normalize("NFC", "\U0001d15e") == "\U0001d157\U0001d165"


def _only_the_email(text: str) -> None:
    entities = pii.detect(text)
    assert [(entity.type, text[entity.start : entity.end]) for entity in entities] == [("EMAIL", "a@b.com")]


def test_an_exact_run_maps_each_letter_to_its_own_end() -> None:
    composed = "a\u0301" + "\u0302" * 30
    assert len(composed) == _detect._LONGEST_EXACT_RUN
    assert _detect._nfc_bounds(composed + "x") == ("\u00e1" + "\u0302" * 30 + "x", [0, *range(2, 34)])
    already_nfc = "x" + "\u0301" * 31
    assert len(already_nfc) == _detect._LONGEST_EXACT_RUN
    assert _detect._nfc_bounds(already_nfc + "\u00e9") == (already_nfc + "\u00e9", None)
    assert _detect._nfc_ends(already_nfc, already_nfc, 5) == list(range(6, 38))


def test_an_exact_run_never_normalizes_more_than_one_pass_over_its_prefixes(monkeypatch: pytest.MonkeyPatch) -> None:
    normalized: list[int] = []

    def normalize(form: Literal["NFC", "NFD", "NFKC", "NFKD"], text: str) -> str:
        normalized.append(len(text))
        return unicodedata.normalize(form, text)

    counting = SimpleNamespace(normalize=normalize, is_normalized=unicodedata.is_normalized, category=unicodedata.category)
    monkeypatch.setattr(_detect, "unicodedata", counting)
    run = "x" + "\u0301" * 31
    assert len(run) == _detect._LONGEST_EXACT_RUN
    assert _detect._nfc_ends(run, run, 0) == list(range(1, 33))
    assert sum(normalized) <= sum(range(1, 33))


GROWTH_COUNTS = (2_000, 8_000, 32_000, 128_000)
GROWTH_LIMIT = 7.0
GROWTH_TRIES = 3
MIN_MEASURED_SECONDS = 0.1


def _cpu_seconds_per_call(text: str) -> float:
    calls = 0
    start = time.thread_time()
    while (elapsed := time.thread_time() - start) < MIN_MEASURED_SECONDS:
        _only_the_email(text)
        calls += 1
    return elapsed / calls


def _growth_ratios(shape: str, fastest: dict[int, float]) -> list[float]:
    ratios: list[float] = []
    for smaller, larger in itertools.pairwise(GROWTH_COUNTS):
        for count in (smaller, larger):
            fastest[count] = min(fastest.get(count, float("inf")), _cpu_seconds_per_call(_shape(shape, count)))
        ratios.append(fastest[larger] / fastest[smaller])
        if ratios[-1] >= GROWTH_LIMIT:
            break
    return ratios


@pytest.mark.parametrize("shape", MARK_RUN_SHAPES)
def test_four_times_the_text_takes_less_than_seven_times_the_cpu_time(shape: str) -> None:
    assert [larger / smaller for smaller, larger in itertools.pairwise(GROWTH_COUNTS)] == [4, 4, 4]
    fastest: dict[int, float] = {}
    tries: list[list[float]] = []
    while len(tries) < GROWTH_TRIES:
        tries.append(_growth_ratios(shape, fastest))
        if max(tries[-1]) < GROWTH_LIMIT and len(tries[-1]) == len(GROWTH_COUNTS) - 1:
            break
    assert max(tries[-1]) < GROWTH_LIMIT, (tries, fastest)
    assert len(tries[-1]) == len(GROWTH_COUNTS) - 1


@pytest.mark.parametrize("page", ["CHANGELOG.md", "docs/guides/pii.md"])
def test_pages_state_the_nfc_mapping_rule(page: str) -> None:
    text = " ".join((ROOT / page).read_text(encoding="utf-8").split())
    for sentence in NFC_SENTENCES:
        assert sentence in text


def test_a_joiner_keeps_the_following_mark_out_of_the_letter_before_it() -> None:
    joiners = ("\N{ZERO WIDTH NON-JOINER}", "\N{ZERO WIDTH JOINER}")
    assert len(joiners) == 2
    for joiner in joiners:
        text = "e" + joiner + "\u0301 ABCPE1234F"
        assert _detect._nfc_bounds(text)[0] == unicodedata.normalize("NFC", text)
        assert pii.mask(text) == "e" + joiner + "\u0301 <PAN>"
        for entity in pii.detect(text):
            assert text[entity.start : entity.end] == entity.text


def test_hangul_jamo_are_composed_like_marks() -> None:
    assert _detect._nfc_bounds("\u1100\u1161\u11a8 a\u0301") == ("\uac01 \u00e1", [0, 3, 4, 6])
    assert _detect._nfc_bounds("\uac00\u11a8a\u0301") == ("\uac01\u00e1", [0, 2, 4])


def test_every_canonical_composition_is_searched_in_nfc_form() -> None:
    checked = 0
    for code in range(sys.maxunicode + 1):
        char = chr(code)
        decomposed = unicodedata.normalize("NFD", char)
        if decomposed == char:
            continue
        text = "a" + decomposed + " " + char + "\u0301"
        assert _detect._nfc_bounds(text)[0] == unicodedata.normalize("NFC", text), hex(code)
        checked += 1
    assert checked > 13_000


def test_a_match_found_only_in_the_original_text_keeps_its_marks() -> None:
    text = "ABCPE1234F" + "\u0307" * 32
    assert pii.mask(text) == "<PAN>" + "\u0307" * 32
