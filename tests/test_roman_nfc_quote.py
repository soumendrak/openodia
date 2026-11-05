from pathlib import Path

import pytest

from openodia import roman
from openodia.roman._roman import Scheme

ROOT = Path(__file__).resolve().parents[1]


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


class TestReversibleQuotesNonzeroCombiningClass:
    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [
            ("ISO15919", "କ\u0e31", "ka\u0e31"),
            ("ISO15919", "କ\u093f", "ka\u093f"),
            ("ISO15919", "ଓ\u0b3f", "ō\u0b3f"),
            ("ISO15919", "କ\u0301", "ka:{\u0301:}"),
            ("ITRANS", "କ\u0e31", "ka\u0e31"),
            ("ITRANS", "କ\u0301", "ka_{\u0301_}"),
        ],
    )
    def test_class_zero_mark_stays_unquoted_and_nonzero_class_is_quoted(
        self, scheme: Scheme, text: str, expected: str
    ) -> None:
        assert roman.to_roman(text, scheme, reversible=True) == expected
        assert roman.from_roman(expected, scheme) == text

    def test_quoting_rule_names_nonzero_canonical_combining_class(self) -> None:
        sources = {
            "openodia/roman/_roman.py": (ROOT / "openodia/roman/_roman.py").read_text(encoding="utf-8"),
            "docs/index.md": (ROOT / "docs/index.md").read_text(encoding="utf-8"),
        }
        for name, text in sources.items():
            assert "combining mark" not in text, name
            assert "nonzero canonical combining class" in text, name
            assert "unicodedata.combining(c) != 0" in text, name
