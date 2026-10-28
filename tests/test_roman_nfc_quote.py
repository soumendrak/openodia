import pytest

from openodia import roman
from openodia.roman._roman import Scheme


class TestReversibleQuotesNfcChanges:
    @pytest.mark.parametrize("scheme", ["ISO15919", "Hunterian", "ITRANS"])
    @pytest.mark.parametrize("sign", ["\u212b", "\u2126", "\u212a"])
    def test_canonical_singleton_signs_round_trip(self, scheme: Scheme, sign: str) -> None:
        text = "କ" + sign
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text

    def test_a_run_that_nfc_changes_is_quoted(self) -> None:
        assert roman.to_roman("କ\u212b", reversible=True) == "ka:{\u212b:}"

    def test_a_run_that_nfc_keeps_is_not_quoted(self) -> None:
        assert roman.to_roman("କ\u00c5", "ITRANS", reversible=True) == "ka\u00c5"
