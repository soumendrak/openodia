from datetime import date
from decimal import Decimal

import pytest

from openodia import numbers
from openodia.numbers._tables import UNDER_HUNDRED


class TestDigitConversion:
    @pytest.mark.parametrize(
        "ascii_text, odia_text",
        [
            ("0", "୦"),
            ("1", "୧"),
            ("9", "୯"),
            ("123", "୧୨୩"),
            ("2026", "୨୦୨୬"),
            ("", ""),
        ],
    )
    def test_ascii_to_odia(self, ascii_text: str, odia_text: str) -> None:
        assert numbers.ascii_to_odia(ascii_text) == odia_text

    @pytest.mark.parametrize(
        "ascii_text, odia_text",
        [
            ("0", "୦"),
            ("123", "୧୨୩"),
            ("2026", "୨୦୨୬"),
            ("", ""),
        ],
    )
    def test_odia_to_ascii(self, ascii_text: str, odia_text: str) -> None:
        assert numbers.odia_to_ascii(odia_text) == ascii_text

    def test_non_digits_pass_through(self) -> None:
        # The Odia letter "ନ" is not a digit and must survive both directions.
        assert numbers.ascii_to_odia("ନ123") == "ନ୧୨୩"
        assert numbers.odia_to_ascii("ନ୧୨୩") == "ନ123"

    def test_mixed_input_unchanged_in_both_directions(self) -> None:
        """Non-target digits in the input pass through."""
        assert numbers.ascii_to_odia("୧2") == "୧୨"  # Odia '୧' stays, '2' becomes '୨'
        assert numbers.odia_to_ascii("1୨") == "12"  # ASCII '1' stays, '୨' becomes '2'

    def test_round_trip(self) -> None:
        for x in ["0", "9876543210", "123 456"]:
            assert numbers.odia_to_ascii(numbers.ascii_to_odia(x)) == x


class TestToWords:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0, "ଶୂନ୍ୟ"),
            (1, "ଏକ"),
            (9, "ନଅ"),
            (10, "ଦଶ"),
            (15, "ପନ୍ଦର"),
            (20, "କୋଡ଼ିଏ"),
            (50, "ପଚାଶ"),
            (99, "ଅନେଶ"),
        ],
    )
    def test_under_hundred(self, value: int, expected: str) -> None:
        assert numbers.to_words(value) == expected

    def test_one_hundred(self) -> None:
        assert numbers.to_words(100) == "ଏକ ଶହ"

    def test_two_hundred_thirty_four(self) -> None:
        assert numbers.to_words(234) == "ଦୁଇ ଶହ ଚଉତିରିଶ"

    def test_one_thousand_two_hundred_thirty_four(self) -> None:
        assert numbers.to_words(1234) == "ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ"

    def test_lakh(self) -> None:
        # 12,34,567 in Indian numbering
        assert numbers.to_words(12_34_567) == "ବାର ଲକ୍ଷ ଚଉତିରିଶ ହଜାର ପାଞ୍ଚ ଶହ ସତଷଠି"

    def test_crore(self) -> None:
        # 1,00,00,000 = one crore
        assert numbers.to_words(1_00_00_000) == "ଏକ କୋଟି"

    def test_two_crore_three_lakh(self) -> None:
        assert numbers.to_words(2_03_00_000) == "ଦୁଇ କୋଟି ତିନି ଲକ୍ଷ"

    def test_negative_number(self) -> None:
        assert numbers.to_words(-5) == "ଋଣାତ୍ମକ ପାଞ୍ଚ"
        assert numbers.to_words(-100) == "ଋଣାତ୍ମକ ଏକ ଶହ"

    def test_short_scale_million(self) -> None:
        assert numbers.to_words(1_000_000, scale="short") == "ଏକ ମିଲିୟନ"

    def test_short_scale_billion(self) -> None:
        assert numbers.to_words(1_000_000_000, scale="short") == "ଏକ ବିଲିୟନ"

    def test_short_scale_trillion(self) -> None:
        assert numbers.to_words(1_000_000_000_000, scale="short") == "ଏକ ଟ୍ରିଲିୟନ"

    def test_short_scale_composes(self) -> None:
        # 1,234,567 short scale: 1 million, 234 thousand, 5 hundred sixty-seven
        assert numbers.to_words(1_234_567, scale="short") == "ଏକ ମିଲିୟନ ଦୁଇ ଶହ ଚଉତିରିଶ ହଜାର ପାଞ୍ଚ ଶହ ସତଷଠି"

    def test_invalid_scale_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown scale"):
            numbers.to_words(1, scale="long")  # type: ignore[arg-type]

    def test_zero_in_both_scales(self) -> None:
        assert numbers.to_words(0, scale="indian") == "ଶୂନ୍ୟ"
        assert numbers.to_words(0, scale="short") == "ଶୂନ୍ୟ"


class TestFromWords:
    @pytest.mark.parametrize("n", [0, 1, 99, 100, 234, 1234, 12_34_567])
    def test_round_trip_indian(self, n: int) -> None:
        assert numbers.from_words(numbers.to_words(n)) == n

    @pytest.mark.parametrize("n", [0, 1_000_000, 1_234_567, 1_000_000_000_000])
    def test_round_trip_short(self, n: int) -> None:
        assert numbers.from_words(numbers.to_words(n, scale="short"), scale="short") == n

    def test_negative_round_trip(self) -> None:
        for n in [-1, -100, -1234]:
            assert numbers.from_words(numbers.to_words(n)) == n

    def test_extra_whitespace_tolerated(self) -> None:
        assert numbers.from_words("  ଏକ   ହଜାର   ") == 1000

    def test_unrecognised_token_raises(self) -> None:
        with pytest.raises(ValueError, match="unrecognised token"):
            numbers.from_words("ଏକ flarble")

    def test_empty_input_raises(self) -> None:
        with pytest.raises(ValueError, match="empty input"):
            numbers.from_words("")
        with pytest.raises(ValueError, match="empty input"):
            numbers.from_words("   ")

    def test_negative_without_magnitude_raises(self) -> None:
        with pytest.raises(ValueError, match="missing magnitude"):
            numbers.from_words("ଋଣାତ୍ମକ")

    def test_invalid_scale_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown scale"):
            numbers.from_words("ଏକ", scale="long")  # type: ignore[arg-type]

    def test_bare_multiplier_treated_as_one(self) -> None:
        """`ଶହ` alone should mean 100."""
        assert numbers.from_words("ଶହ") == 100
        assert numbers.from_words("ହଜାର") == 1000


class TestOrdinal:
    @pytest.mark.parametrize(
        "n, expected",
        [
            (1, "ପ୍ରଥମ"),
            (2, "ଦ୍ୱିତୀୟ"),
            (3, "ତୃତୀୟ"),
            (4, "ଚତୁର୍ଥ"),
            (5, "ପଞ୍ଚମ"),
            (6, "ଷଷ୍ଠ"),
            (7, "ସପ୍ତମ"),
            (8, "ଅଷ୍ଟମ"),
            (9, "ନବମ"),
            (10, "ଦଶମ"),
        ],
    )
    def test_irregular_ordinals(self, n: int, expected: str) -> None:
        assert numbers.to_ordinal(n) == expected

    def test_regular_ordinal_uses_tam_suffix(self) -> None:
        assert numbers.to_ordinal(11) == f"{UNDER_HUNDRED[11]}ତମ"
        assert numbers.to_ordinal(100) == "ଏକ ଶହତମ"

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="ordinals are defined"):
            numbers.to_ordinal(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="ordinals are defined"):
            numbers.to_ordinal(-1)


class TestCurrency:
    def test_integer_rupees(self) -> None:
        assert numbers.to_words_currency(1) == "ଏକ ଟଙ୍କା"
        assert numbers.to_words_currency(1500) == "ଏକ ହଜାର ପାଞ୍ଚ ଶହ ଟଙ୍କା"

    def test_with_paisa(self) -> None:
        assert numbers.to_words_currency(1500.50) == "ଏକ ହଜାର ପାଞ୍ଚ ଶହ ଟଙ୍କା ପଚାଶ ପଇସା"

    def test_paisa_only(self) -> None:
        assert numbers.to_words_currency(0.05) == "ପାଞ୍ଚ ପଇସା"
        assert numbers.to_words_currency(0.50) == "ପଚାଶ ପଇସା"

    def test_zero_amount(self) -> None:
        assert numbers.to_words_currency(0) == "ଶୂନ୍ୟ ଟଙ୍କା"
        assert numbers.to_words_currency(0.00) == "ଶୂନ୍ୟ ଟଙ୍କା"

    def test_rounding(self) -> None:
        # 1.005 → 1.01 (half-up)
        assert numbers.to_words_currency(1.005) == "ଏକ ଟଙ୍କା ଏକ ପଇସା"

    def test_decimal_input_accepted(self) -> None:
        assert numbers.to_words_currency(Decimal("100.25")) == "ଏକ ଶହ ଟଙ୍କା ପଚିଶ ପଇସା"

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="amount must be >= 0"):
            numbers.to_words_currency(-1)

    def test_unsupported_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported currency"):
            numbers.to_words_currency(1, currency="USD")


class TestDate:
    def test_basic(self) -> None:
        # 27 May 2026
        result = numbers.to_words_date(date(2026, 5, 27))
        # day ordinal -> regular ordinal with suffix; month = ମଇ; year = ଦୁଇ ହଜାର ଛବିଶ
        assert "ମଇ" in result
        assert "ଦୁଇ ହଜାର ଛବିଶ" in result
        assert result.endswith("ଦୁଇ ହଜାର ଛବିଶ")

    def test_irregular_day_ordinal(self) -> None:
        # 1st of any month should use the irregular ordinal.
        result = numbers.to_words_date(date(2026, 1, 1))
        assert result.startswith("ପ୍ରଥମ ")

    def test_each_month_translated(self) -> None:
        # Confirm the table covers all 12 months without crashing.
        for month in range(1, 13):
            numbers.to_words_date(date(2026, month, 15))

    def test_year_zero_raises(self) -> None:
        """``date`` rejects year 0 in its ctor, so we exercise the guard via a stub."""

        class _StubDate:
            year = 0
            month = 1
            day = 1

        with pytest.raises(ValueError, match="year must be >= 1"):
            numbers.to_words_date(_StubDate())  # type: ignore[arg-type]


class TestPublicAPI:
    def test_top_level_namespace(self) -> None:
        import openodia

        assert openodia.numbers is numbers
        assert openodia.numbers.to_words(1) == "ଏକ"
        assert openodia.numbers.from_words("ଏକ") == 1


class TestTableSanity:
    """Guard rails against accidental edits of the lookup tables."""

    def test_under_hundred_has_100_entries(self) -> None:
        assert len(UNDER_HUNDRED) == 100

    def test_under_hundred_all_unique(self) -> None:
        # If any two words are equal, from_words would round-trip wrong.
        assert len(set(UNDER_HUNDRED)) == 100
