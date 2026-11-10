import json
from pathlib import Path

import pytest

from openodia import legacy

FIXTURES = Path(__file__).parent / "fixtures" / "legacy_sentences.json"
ODIA = "\u0b13\u0b21\u0b3c\u0b3f\u0b06"
NUKTA_E = "\u0b21\u0b3c\u0b47"


def test_supported_fonts_lists_the_shipped_encodings() -> None:
    assert legacy.SUPPORTED_FONTS == ("AkrutiOriSarala", "ORTTSarala")


def test_akruti_converts_odia_and_keeps_nfc_nukta() -> None:
    assert legacy.to_unicode("IWÿò@û", font="AkrutiOriSarala") == ODIA


def test_ortt_converts_the_same_word() -> None:
    assert legacy.to_unicode("JXÏÞA", font="ORTTSarala") == ODIA


@pytest.mark.parametrize(
    ("font", "source", "expected"),
    [
        ("AkrutiOriSarala", "ùK", "କେ"),
        ("AkrutiOriSarala", "ùKû", "କୋ"),
        ("AkrutiOriSarala", "ùKø", "କୌ"),
        ("AkrutiOriSarala", "ùK÷", "କୈ"),
        ("AkrutiOriSarala", "Kò", "କି"),
        ("AkrutiOriSarala", "@û", "ଆ"),
        ("AkrutiOriSarala", "l", "କ୍ଷ"),
        ("AkrutiOriSarala", "12", "୧୨"),
        ("AkrutiOriSarala", "ùKþK", "କ୍କେ"),
        ("AkrutiOriSarala", "ù\\þ]", "ଦ୍ଧେ"),
        ("AkrutiOriSarala", "ùKþKþK", "କ୍କ୍କେ"),
        ("AkrutiOriSarala", "ùWÿ", NUKTA_E),
        ("AkrutiOriSarala", "Kõû", "କାଂ"),
        ("ORTTSarala", "ÒL", "କେ"),
        ("ORTTSarala", "ÒLÐ", "କୋ"),
        ("ORTTSarala", "ÒL×", "କୌ"),
        ("ORTTSarala", "ÒLß", "କୈ"),
        ("ORTTSarala", "LÞ", "କି"),
        ("ORTTSarala", "LÙ", "ର୍କି"),
        ("ORTTSarala", "lÙ", "ର୍କ୍ଷି"),
        ("ORTTSarala", "Æ", "କ୍ଟ"),
        ("ORTTSarala", "Òw", "ଦ୍ଧେ"),
        ("ORTTSarala", "ÒXÏ", NUKTA_E),
        ("ORTTSarala", "LÕÐ", "କାଂ"),
        ("ORTTSarala", "LÐÔ", "କ୍ୟା"),
        ("ORTTSarala", "12", "୧୨"),
    ],
)
def test_matras_reph_and_conjuncts(font: str, source: str, expected: str) -> None:
    assert legacy.to_unicode(source, font=font) == expected


def test_unmapped_ascii_punctuation_passes_through() -> None:
    assert legacy.to_unicode("K, M.", font="AkrutiOriSarala") == "କ, ଗ."


def test_text_outside_both_fonts_is_not_a_guess() -> None:
    assert legacy.detect_font("???") == {"font": None, "confidence": 0.0}
    assert legacy.to_unicode_auto("???") == "???"


def test_empty_text_stays_empty() -> None:
    assert legacy.to_unicode("", font="AkrutiOriSarala") == ""
    assert legacy.to_unicode_auto("") == ""


def test_unknown_font_is_rejected() -> None:
    with pytest.raises(ValueError, match="ORTTSarala"):
        legacy.to_unicode("K", font="Soumya")


def test_detect_font_reports_font_and_confidence() -> None:
    akruti = legacy.detect_font("IWÿò@û")
    ortt = legacy.detect_font("JXÏÞA")
    empty = legacy.detect_font("")
    assert akruti == {"font": "AkrutiOriSarala", "confidence": akruti["confidence"]}
    assert ortt["font"] == "ORTTSarala"
    assert empty == {"font": None, "confidence": 0.0}
    assert isinstance(akruti["confidence"], float)
    assert akruti["confidence"] > 0.5
    assert ortt["confidence"] > 0.5


def test_shared_ascii_ties_and_stays_inside_one() -> None:
    guess = legacy.detect_font("Hello")
    assert guess["font"] == "AkrutiOriSarala"
    assert guess["confidence"] == 0.5


def test_auto_uses_the_detected_font() -> None:
    text = "IWÿò@û"
    assert legacy.to_unicode_auto(text) == legacy.to_unicode(text, font="AkrutiOriSarala")
    other = "JXÏÞA"
    assert legacy.to_unicode_auto(other) == legacy.to_unicode(other, font="ORTTSarala")


def test_package_exports_the_module_once() -> None:
    import openodia

    assert openodia.legacy is legacy
    assert "legacy" in openodia.__all__


def test_each_font_has_fifty_known_sentences() -> None:
    fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert set(fixture) == set(legacy.SUPPORTED_FONTS)
    for font, rows in fixture.items():
        assert len(rows) >= 50
        for row in rows:
            assert legacy.to_unicode(row["legacy"], font=font) == row["unicode"]
            assert row["unicode"].strip()
