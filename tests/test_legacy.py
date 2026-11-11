import json
from pathlib import Path

import pytest

from openodia import legacy
from openodia.legacy import _convert

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
        ("AkrutiOriSarala", "ùKõø", "କୌଂ"),
        ("AkrutiOriSarala", "ùKñø", "କୌଁ"),
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
        ("ORTTSarala", "ÒLÕß", "କୈଂ"),
        ("ORTTSarala", "LÔà", "ର୍କ୍ୟ"),
        ("ORTTSarala", "LÐÔà", "ର୍କ୍ୟା"),
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


def test_shared_ascii_is_a_tie_and_is_not_guessed() -> None:
    guess = legacy.detect_font("Hello")
    assert guess == {"font": None, "confidence": 0.5}
    assert legacy.to_unicode_auto("Hello") == "Hello"


def test_auto_uses_the_detected_font() -> None:
    text = "IWÿò@û"
    assert legacy.to_unicode_auto(text) == legacy.to_unicode(text, font="AkrutiOriSarala")
    other = "JXÏÞA"
    assert legacy.to_unicode_auto(other) == legacy.to_unicode(other, font="ORTTSarala")


def test_package_exports_the_module_once() -> None:
    import openodia

    assert openodia.legacy is legacy
    assert "legacy" in openodia.__all__


def test_a_font_table_must_have_the_expected_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(TypeError):
        _convert._pairs(None)
    with pytest.raises(TypeError):
        _convert._pairs([["only"]])
    with pytest.raises(TypeError):
        _convert._pairs([["", "x"]])
    with pytest.raises(TypeError):
        _convert._strings(None)
    with pytest.raises(TypeError):
        _convert._strings([""])
    assert _convert._matra(None) is None
    with pytest.raises(TypeError):
        _convert._matra([])
    with pytest.raises(TypeError):
        _convert._matra({})
    with pytest.raises(TypeError):
        _convert._matra({"marker": "m", "default": "d", "forms": ["no"]})
    with pytest.raises(TypeError):
        _convert._matra({"marker": "m", "default": "d", "forms": [["", "x"]]})
    with pytest.raises(TypeError):
        _convert._rules("no")
    with pytest.raises(TypeError):
        _convert._rules([["a"]])
    with pytest.raises(TypeError):
        _convert._rules([["a", "b", "no"]])
    with pytest.raises(TypeError):
        _convert._reph("")
    monkeypatch.setattr(_convert.json, "loads", lambda _text: [])
    with pytest.raises(TypeError):
        _convert._read_font("AkrutiOriSarala")


CP1252_BYTES = (
    ("AkrutiOriSarala", 0x83, "ଞ୍ଝ"),
    ("AkrutiOriSarala", 0x85, "ଟ୍ଟ"),
    ("AkrutiOriSarala", 0x89, "ଣ୍ଣ"),
    ("AkrutiOriSarala", 0x8A, "ଣ୍ଡ"),
    ("AkrutiOriSarala", 0x8B, "ଣ୍ଢ"),
    ("AkrutiOriSarala", 0x8C, "ଣ୍ଠ"),
    ("AkrutiOriSarala", 0x99, "ତ୍ମ"),
    ("AkrutiOriSarala", 0x9A, "ତ୍ପ"),
    ("AkrutiOriSarala", 0x9B, "ତ୍ସ"),
    ("AkrutiOriSarala", 0x9C, "ତ୍ସ୍ନ"),
    ("AkrutiOriSarala", 0x9F, "ଦ୍ଦ"),
    ("ORTTSarala", 0x83, "„"),
    ("ORTTSarala", 0x85, "ଣ୍ଠ"),
    ("ORTTSarala", 0x86, "ପ୍ଟ"),
    ("ORTTSarala", 0x87, "ୁ"),
    ("ORTTSarala", 0x91, "ଗ୍ଧ"),
    ("ORTTSarala", 0x92, "ଗ୍ଦ"),
    ("ORTTSarala", 0x93, "ପ୍ପ"),
    ("ORTTSarala", 0x94, "ଡ୍ଗ"),
    ("ORTTSarala", 0x95, "ବ୍ଧ"),
    ("ORTTSarala", 0x96, "ଳ୍କ"),
    ("ORTTSarala", 0x97, "ତ୍ସ"),
    ("ORTTSarala", 0x98, "୍ଳ"),
    ("ORTTSarala", 0x99, "ର୍ଁ"),
    ("ORTTSarala", 0x9A, "୍ୱ"),
    ("ORTTSarala", 0x9B, "୍ମ"),
    ("ORTTSarala", 0x9C, "କ୍ଟ"),
)

RELEASE_SENTENCE = "`openodia.legacy` needs a release newer than 0.1.14"
RELEASE_PAGES = ("README.md", "docs/index.md", "docs/llms.txt", "AGENTS.md")


@pytest.mark.parametrize("page", RELEASE_PAGES)
def test_legacy_pages_name_the_release(page: str) -> None:
    text = (Path(__file__).resolve().parents[1] / page).read_text(encoding="utf-8")
    assert RELEASE_SENTENCE in text


@pytest.mark.parametrize(("font", "byte", "expected"), CP1252_BYTES)
def test_cp1252_only_bytes_convert(font: str, byte: int, expected: str) -> None:
    assert legacy.to_unicode(bytes([byte]).decode("cp1252"), font=font) == expected


def test_ellipsis_byte_is_cp1252_not_latin_1() -> None:
    assert legacy.to_unicode(b"\x85".decode("cp1252"), font="AkrutiOriSarala") == "ଟ୍ଟ"
    assert legacy.to_unicode(b"\x85".decode("latin-1"), font="AkrutiOriSarala") == "\u0085"


def test_reph_walks_every_halant_in_the_conjunct() -> None:
    assert legacy.to_unicode("crÔà", font="ORTTSarala") == "ମର୍ତ୍ତ୍ୟ"


def test_yaphala_moves_past_every_vowel_sign() -> None:
    assert legacy.to_unicode("OãôÔg", font="ORTTSarala") == "ଘ୍ୟୁୃୱ"


def test_each_font_has_fifty_known_sentences() -> None:
    fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert set(fixture) == set(legacy.SUPPORTED_FONTS)
    for font, rows in fixture.items():
        assert len(rows) >= 50
        assert sum("\u0b3e" in row["legacy"] for row in rows) == 0
        for row in rows:
            assert not any("\u0b00" <= character <= "\u0b7f" for character in row["legacy"])
            assert legacy.to_unicode(row["legacy"], font=font) == row["unicode"]
            assert row["unicode"].strip()
            guess = legacy.detect_font(row["legacy"])
            auto = legacy.to_unicode_auto(row["legacy"])
            if guess["font"] is None:
                assert auto == row["legacy"]
            else:
                assert guess["font"] == font
                assert auto == row["unicode"]
    tied = fixture["ORTTSarala"][40]
    assert legacy.detect_font(tied["legacy"])["font"] is None
    assert legacy.to_unicode(tied["legacy"], font="ORTTSarala") == tied["unicode"]
    assert legacy.to_unicode_auto(tied["legacy"]) == tied["legacy"]
    first = fixture["AkrutiOriSarala"][0]
    assert legacy.detect_font(first["legacy"]) == {"font": "AkrutiOriSarala", "confidence": 24 / 39}
