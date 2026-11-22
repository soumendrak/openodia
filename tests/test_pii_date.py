import calendar
import json
import time
import unicodedata

import pytest

from openodia import cli, pii
from openodia.numbers import odia_to_ascii
from openodia.numbers._tables import GREGORIAN_MONTHS
from openodia.pii import _date

ENGLISH_MONTHS = (
    ("January", "Jan"),
    ("February", "Feb"),
    ("March", "Mar"),
    ("April", "Apr"),
    ("May",),
    ("June", "Jun"),
    ("July", "Jul"),
    ("August", "Aug"),
    ("September", "Sept", "Sep"),
    ("October", "Oct"),
    ("November", "Nov"),
    ("December", "Dec"),
)
MONTH_NAMES = [
    (name, number) for number, names in enumerate(ENGLISH_MONTHS, start=1) for name in (*names, GREGORIAN_MONTHS[number - 1])
]


def dates(text: str, **options: float) -> list[tuple[str, float]]:
    return [(entity.text, entity.confidence) for entity in pii.detect(text, **options) if entity.type == "DATE"]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("ଜନ୍ମ 15 January 2024 ରେ", "15 January 2024"),
        ("୧୫ ଜାନୁଆରୀ ୨୦୨୪", "୧୫ ଜାନୁଆରୀ ୨୦୨୪"),
        ("୧୫ ଜାନୁଆରୀ ୨୦୨୪ରେ", "୧୫ ଜାନୁଆରୀ ୨୦୨୪"),
        ("on 15th January 2024.", "15th January 2024"),
        ("1st Feb 2024", "1st Feb 2024"),
        ("2nd Mar 2024", "2nd Mar 2024"),
        ("3rd Apr 2024", "3rd Apr 2024"),
        ("05 June 2024", "05 June 2024"),
        ("15 Jan. 2024", "15 Jan. 2024"),
        ("15 January, 2024", "15 January, 2024"),
        ("15 JANUARY 2024", "15 JANUARY 2024"),
        ("15 sePT 2024", "15 sePT 2024"),
        ("15\tJanuary\u00a0 2024", "15\tJanuary\u00a0 2024"),
        ("May 4, 2024", "May 4, 2024"),
        ("May 4 2024", "May 4 2024"),
        ("May 4th, 2024", "May 4th, 2024"),
        ("Jan. 15, 2024", "Jan. 15, 2024"),
        ("ଜାନୁଆରୀ ୧୫, ୨୦୨୪", "ଜାନୁଆରୀ ୧୫, ୨୦୨୪"),
        ("୨୯ ଫେବ୍ରୁଆରୀ ୨୦୨୪", "୨୯ ଫେବ୍ରୁଆରୀ ୨୦୨୪"),
        ("1 January 1900", "1 January 1900"),
        ("31 December 2099", "31 December 2099"),
    ],
)
def test_a_named_date_is_found_at_085(text: str, found: str) -> None:
    assert dates(text) == [(found, 0.85)]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("born 15/01/2024", "15/01/2024"),
        ("୧୫-୦୧-୨୦୨୪", "୧୫-୦୧-୨୦୨୪"),
        ("5.1.2024", "5.1.2024"),
        ("1.2.2024", "1.2.2024"),
        ("31/12/2099", "31/12/2099"),
        ("01/01/1900", "01/01/1900"),
        ("29/02/2024", "29/02/2024"),
        ("15/01-2024", "15/01-2024"),
        ("ଜନ୍ମ15/01/2024ରେ", "15/01/2024"),
    ],
)
def test_a_numeric_date_is_found_at_07(text: str, found: str) -> None:
    assert dates(text) == [(found, 0.7)]


@pytest.mark.parametrize(
    "text",
    [
        "31/02/2024",
        "29/02/2023",
        "29 February 2023",
        "31 April 2024",
        "01/13/2024",
        "00/01/2024",
        "32/01/2024",
        "15/00/2024",
        "15/01/1899",
        "15/01/2100",
        "15 January 1899",
        "15 January 2100",
        "0 January 2024",
        "32 January 2024",
        "115/01/2024",
        "15/01/20245",
        "115 January 2024",
        "15 January 20245",
        "May 4, 20245",
        "15 January",
        "January 2024",
        "15\nJanuary 2024",
        "15 January\n2024",
        "May\n4, 2024",
        "May 4,\n2024",
        "15January 2024",
        "15 January2024",
        "15 Janu 2024",
        "15 Mayday 2024",
        "15 XMay 2024",
        "15 ମଇରେ 2024",
        "15 ଅମଇ 2024",
        "XMay 4, 2024",
        "15 January,, 2024",
        "15 Jan.. 2024",
        "May 4,, 2024",
        "15 Aprıl 2024",
        "15 APRİL 2024",
        "15 ſept 2024",
        "1.2.3",
        "15/01/24",
        "15 / 01 / 2024",
    ],
)
def test_text_that_is_not_a_real_date_is_not_a_date(text: str) -> None:
    assert dates(text) == []


@pytest.mark.parametrize(("name", "month"), MONTH_NAMES)
@pytest.mark.parametrize("year", [2023, 2024])
def test_every_month_name_allows_exactly_its_days(name: str, month: int, year: int) -> None:
    last = calendar.monthrange(year, month)[1]
    for day in range(1, 32):
        expected = [0.85] if day <= last else []
        assert [confidence for _, confidence in dates(f"{day} {name} {year}")] == expected
        assert [confidence for _, confidence in dates(f"{name} {day}, {year}")] == expected


@pytest.mark.parametrize("month", range(1, 13))
def test_every_numeric_month_allows_exactly_its_days(month: int) -> None:
    for year in (2023, 2024):
        last = calendar.monthrange(year, month)[1]
        for day in range(1, 32):
            assert len(dates(f"{day}/{month}/{year}")) == (day <= last)


def test_min_confidence_keeps_a_named_date_and_drops_a_numeric_one() -> None:
    text = "15/01/2024 ଓ 15 January 2024"
    assert dates(text, min_confidence=0.8) == [("15 January 2024", 0.85)]
    assert dates(text, min_confidence=0.7) == [("15/01/2024", 0.7), ("15 January 2024", 0.85)]
    assert dates(text, min_confidence=0.86) == []
    assert pii.mask(text, min_confidence=0.8) == "15/01/2024 ଓ <DATE>"


def test_types_limits_detection_to_dates() -> None:
    text = "9876543210 ଓ 15/01/2024"
    assert [entity.type for entity in pii.detect(text, types=["DATE"])] == ["DATE"]
    assert [entity.type for entity in pii.detect(text, types=["PHONE"])] == ["PHONE"]
    assert pii.mask(text) == "<PHONE> ଓ <DATE>"


@pytest.mark.parametrize("text", ["ଜନ୍ମ ୧୫ ଅକ୍ଟୋବର ୨୦୨୪", "ମୌସୁମୀ ୧ ଫେବ୍ରୁଆରୀ ୨୦୨୪ ରେ", "ଯୋଗ ମଇ ୪, ୨୦୨୪"])
def test_nfd_text_masks_the_same_date_as_nfc(text: str) -> None:
    decomposed = unicodedata.normalize("NFD", text)
    assert decomposed != text
    assert pii.mask(text).count("<DATE>") == 1
    assert unicodedata.normalize("NFC", pii.mask(decomposed)) == pii.mask(text)
    for entity in pii.detect(decomposed):
        assert decomposed[entity.start : entity.end] == entity.text


def test_a_date_inside_a_longer_match_is_merged_into_it() -> None:
    assert pii.mask("https://x.com/15/01/2024") == "<URL>"


def test_cli_reports_a_date(capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    assert cli.main(["pii", "born 15/01/2024", "--type", "DATE", "--json"]) == 0
    entity = {"type": "DATE", "text": "15/01/2024", "start": 5, "end": 15, "confidence": 0.7}
    assert json.loads(capsys.readouterr().out) == {"entities": [entity]}


LONG_SHAPES = {
    "named dates": "15 January 2024 ",
    "numeric dates": "15/01/2024 ",
    "month-first dates": "May 4, 2024 ",
    "Odia dates": "୧୫ ଜାନୁଆରୀ ୨୦୨୪ ",
    "days and months without a year": "15 January ",
    "impossible dates": "31/02/2024 ",
    "digits and spaces": "1 ",
    "month names": "May ",
}


class _Measured(str):
    work = 0

    def __getitem__(self, key: int | slice) -> str:
        item = str.__getitem__(self, key)
        type(self).work += len(item)
        return _Measured(item)

    def __add__(self, other: str) -> str:
        type(self).work += len(self) + len(other)
        return _Measured(str.__add__(self, other))


@pytest.mark.parametrize("shape", LONG_SHAPES)
def test_finding_dates_copies_a_linear_amount_of_the_text(shape: str) -> None:
    def work(count: int) -> tuple[int, int]:
        _Measured.work = 0
        found = _date.find_dates(_Measured(odia_to_ascii(LONG_SHAPES[shape]) * count))
        return _Measured.work, len(found)

    small, small_found = work(500)
    large, large_found = work(2_000)
    assert large_found == 4 * small_found
    assert large <= 5 * max(small, 500)


BUDGET_SECONDS = 4.0
BUDGET_REPEATS = 64_000


@pytest.mark.parametrize("shape", LONG_SHAPES)
def test_64000_repeats_are_searched_within_the_time_budget(shape: str) -> None:
    text = LONG_SHAPES[shape] * BUDGET_REPEATS
    times: list[float] = []
    for _ in range(2):
        start = time.perf_counter()
        pii.detect(text, types=["DATE"])
        times.append(time.perf_counter() - start)
    assert min(times) < BUDGET_SECONDS, times


def test_long_shapes_cover_found_and_rejected_dates() -> None:
    counts = {shape: len(pii.detect(unit * 3, types=["DATE"])) for shape, unit in LONG_SHAPES.items()}
    assert list(counts.values()) == [3, 3, 3, 3, 0, 0, 0, 0]
