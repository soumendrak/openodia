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
    "In text that is not in NFC, a match whose last letter carries 32 or more combining marks also covers those marks.",
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
}


def _shape(name: str, count: int) -> str:
    assert len(MARK_RUN_SHAPES) == 2
    return MARK_RUN_SHAPES[name](count) + "a@b.com"


def _only_the_email(text: str) -> None:
    entities = pii.detect(text)
    assert [(entity.type, text[entity.start : entity.end]) for entity in entities] == [("EMAIL", "a@b.com")]


@pytest.mark.parametrize("shape", MARK_RUN_SHAPES)
def test_mark_run_mapping_does_linear_unicodedata_work(shape: str, monkeypatch: pytest.MonkeyPatch) -> None:
    normalized: list[int] = []
    looked_up: list[int] = []

    def normalize(form: Literal["NFC", "NFD", "NFKC", "NFKD"], text: str) -> str:
        normalized.append(len(text))
        return unicodedata.normalize(form, text)

    def category(char: str) -> str:
        looked_up.append(1)
        return unicodedata.category(char)

    def combining(char: str) -> int:
        looked_up.append(1)
        return unicodedata.combining(char)

    counting = SimpleNamespace(
        normalize=normalize, is_normalized=unicodedata.is_normalized, category=category, combining=combining
    )
    monkeypatch.setattr(_detect, "unicodedata", counting)

    def steps(count: int) -> tuple[int, int]:
        normalized.clear()
        looked_up.clear()
        _only_the_email(_shape(shape, count))
        return sum(normalized), sum(normalized) + sum(looked_up)

    small_normalized, small = steps(100)
    _, large = steps(400)
    assert small_normalized >= 100
    assert large < small * 5


def test_an_exact_run_resumes_its_search_where_the_last_letter_ended(monkeypatch: pytest.MonkeyPatch) -> None:
    normalized: list[int] = []

    def normalize(form: Literal["NFC", "NFD", "NFKC", "NFKD"], text: str) -> str:
        normalized.append(len(text))
        return unicodedata.normalize(form, text)

    counting = SimpleNamespace(normalize=normalize, is_normalized=unicodedata.is_normalized, category=unicodedata.category)
    monkeypatch.setattr(_detect, "unicodedata", counting)
    run = "e\u0301" + "\u0323" * 30
    assert len(run) == _detect._LONGEST_EXACT_RUN
    _detect._nfc_ends(run, unicodedata.normalize("NFC", run), 0)
    assert sum(normalized) == sum(range(1, 33))


BUDGET_SECONDS = 2.5
BUDGET_MARKS = 64_000


def _seconds(text: str) -> float:
    start = time.perf_counter()
    _only_the_email(text)
    return time.perf_counter() - start


@pytest.mark.parametrize("shape", MARK_RUN_SHAPES)
def test_64000_marks_are_mapped_within_the_time_budget(shape: str) -> None:
    text = _shape(shape, BUDGET_MARKS)
    times: list[float] = []
    for _ in range(3):
        times.append(_seconds(text))
        if times[-1] < BUDGET_SECONDS:
            break
    assert min(times) < BUDGET_SECONDS, times


@pytest.mark.parametrize("page", ["CHANGELOG.md", "docs/guides/pii.md"])
def test_pages_state_the_nfc_mapping_rule(page: str) -> None:
    text = " ".join((ROOT / page).read_text(encoding="utf-8").split())
    for sentence in NFC_SENTENCES:
        assert sentence in text


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
