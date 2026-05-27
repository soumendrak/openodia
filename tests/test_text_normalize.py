import unicodedata

import pytest

from openodia import clean, normalize
from openodia.text import (
    ASCII_DIGITS,
    DEFAULT_CLEAN,
    ODIA_DIGITS,
    ZWJ,
    ZWNJ,
    CleanOptions,
)


class TestNormalize:
    """Tests for :func:`openodia.normalize`."""

    @pytest.mark.parametrize("form", ["NFC", "NFD", "NFKC", "NFKD"])
    def test_accepts_all_four_standard_forms(self, form: str) -> None:
        assert normalize("ଓଡ଼ିଆ", form=form) == unicodedata.normalize(form, "ଓଡ଼ିଆ")

    def test_default_form_is_nfc(self) -> None:
        decomposed = "ଡ" + "଼"
        assert normalize(decomposed) == unicodedata.normalize("NFC", decomposed)

    def test_nfc_composes_nukta(self) -> None:
        decomposed = "ଡ" + "଼"
        composed = "ଡ଼"
        assert normalize(decomposed, form="NFC") == composed

    def test_nfd_decomposes_nukta(self) -> None:
        assert normalize("ଡ଼", form="NFD") == "ଡ" + "଼"

    def test_idempotent_under_repeated_application(self) -> None:
        text = "ନମସ୍କାର ଓଡ଼ିଆ"
        once = normalize(text)
        twice = normalize(once)
        assert once == twice

    def test_empty_string(self) -> None:
        assert normalize("") == ""

    def test_ascii_unchanged(self) -> None:
        assert normalize("hello world 123") == "hello world 123"

    def test_invalid_form_raises(self) -> None:
        with pytest.raises(ValueError, match="form must be one of"):
            normalize("ଓଡ଼ିଆ", form="NFX")  # type: ignore[arg-type]


class TestCleanOptions:
    def test_default_options_are_safe(self) -> None:
        opts = CleanOptions()
        assert opts.form == "NFC"
        assert opts.strip_zwj is True
        assert opts.strip_zwnj is True
        assert opts.collapse_whitespace is True
        assert opts.latin_to_odia_digits is False
        assert opts.odia_to_latin_digits is False

    def test_mutually_exclusive_digit_conversions(self) -> None:
        with pytest.raises(ValueError, match="mutually exclusive"):
            CleanOptions(latin_to_odia_digits=True, odia_to_latin_digits=True)

    def test_default_clean_singleton_matches_default_options(self) -> None:
        assert DEFAULT_CLEAN == CleanOptions()


class TestClean:
    """Tests for :func:`openodia.clean`."""

    def test_idempotent(self) -> None:
        text = f" ନମ{ZWNJ}ସ୍କାର  {ZWJ}ଓଡ଼ିଆ  "
        once = clean(text)
        twice = clean(once)
        assert once == twice

    def test_strips_zwnj_by_default(self) -> None:
        assert ZWNJ not in clean(f"ନମ{ZWNJ}ସ୍କାର")

    def test_strips_zwj_by_default(self) -> None:
        assert ZWJ not in clean(f"ନମ{ZWJ}ସ୍କାର")

    def test_keep_zwj_when_disabled(self) -> None:
        out = clean(
            f"ନମ{ZWJ}ସ୍କାର",
            options=CleanOptions(strip_zwj=False, strip_zwnj=False),
        )
        assert ZWJ in out

    def test_collapses_whitespace_by_default(self) -> None:
        assert clean("  ନମସ୍କାର    ଓଡ଼ିଆ  ") == "ନମସ୍କାର ଓଡ଼ିଆ"

    def test_collapses_tabs_and_newlines(self) -> None:
        assert clean("ନମସ୍କାର\t\nଓଡ଼ିଆ") == "ନମସ୍କାର ଓଡ଼ିଆ"

    def test_keep_whitespace_when_disabled(self) -> None:
        out = clean(
            "  ନମସ୍କାର  ",
            options=CleanOptions(collapse_whitespace=False),
        )
        assert out == "  ନମସ୍କାର  "

    def test_normalizes_to_nfc_by_default(self) -> None:
        decomposed = "ଡ" + "଼"
        assert clean(decomposed) == "ଡ଼"

    def test_latin_to_odia_digits(self) -> None:
        out = clean(
            "ଆଜି 123 ବର୍ଷ",
            options=CleanOptions(latin_to_odia_digits=True),
        )
        assert out == "ଆଜି ୧୨୩ ବର୍ଷ"

    def test_odia_to_latin_digits(self) -> None:
        out = clean(
            "ଆଜି ୧୨୩ ବର୍ଷ",
            options=CleanOptions(odia_to_latin_digits=True),
        )
        assert out == "ଆଜି 123 ବର୍ଷ"

    def test_default_does_not_convert_digits(self) -> None:
        assert clean("123") == "123"
        assert clean("୧୨୩") == "୧୨୩"

    def test_empty_string(self) -> None:
        assert clean("") == ""

    def test_options_none_uses_default(self) -> None:
        text = f" ନମ{ZWNJ}ସ୍କାର "
        assert clean(text) == clean(text, options=None)


class TestModuleConstants:
    def test_digit_strings_are_aligned(self) -> None:
        assert len(ASCII_DIGITS) == len(ODIA_DIGITS) == 10

    def test_zwj_codepoint(self) -> None:
        assert ord(ZWJ) == 0x200D

    def test_zwnj_codepoint(self) -> None:
        assert ord(ZWNJ) == 0x200C


class TestPublicAPI:
    """The user-facing aliases should exist on the top-level package."""

    def test_normalize_is_exported(self) -> None:
        import openodia

        assert openodia.normalize is normalize

    def test_clean_is_exported(self) -> None:
        import openodia

        assert openodia.clean is clean
