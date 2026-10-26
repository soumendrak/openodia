import pytest

from openodia import roman
from openodia.roman._roman import Scheme


class TestOdiaDigits:
    @pytest.mark.parametrize("scheme", ["Hunterian", "ITRANS"])
    def test_ascii_schemes_write_ascii_digits(self, scheme: Scheme) -> None:
        out = roman.to_roman("୨୦୨୬ ୦୧୨୩୪୫୬୭୮୯", scheme)
        assert out == "2026 0123456789"
        assert out.isascii()

    @pytest.mark.parametrize("scheme", ["Hunterian", "ITRANS"])
    def test_digits_beside_letters(self, scheme: Scheme) -> None:
        assert roman.to_roman("କ୧", scheme) == "ka1"

    def test_iso15919_keeps_odia_digits(self) -> None:
        assert roman.to_roman("୨୦୨୬", "ISO15919") == "୨୦୨୬"

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    def test_reversible_keeps_odia_digits_so_round_trip_is_exact(self, scheme: Scheme) -> None:
        text = "୨୦୨୬ 2026 କ୧"
        out = roman.to_roman(text, scheme, reversible=True)
        assert "୨୦୨୬" in out
        assert roman.from_roman(out, scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "Hunterian", "ITRANS"])
    def test_from_roman_keeps_ascii_digits(self, scheme: Scheme) -> None:
        assert roman.from_roman("2026", scheme) == "2026"
