import json
import random
import re
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
        ("ORTTSarala", "ÒLÔ×", "କ୍ୟୌ"),
        ("ORTTSarala", "ÒLÔß", "କ୍ୟୈ"),
        ("ORTTSarala", "ÒLÔ", "କ୍ୟେ"),
        ("ORTTSarala", "L™", "ର୍କଁ"),
        ("AkrutiOriSarala", "Gø", "ଐ"),
        ("AkrutiOriSarala", "KGø", "କଐ"),
    ],
)
def test_matras_reph_and_conjuncts(font: str, source: str, expected: str) -> None:
    assert legacy.to_unicode(source, font=font) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("LÐÔ", "କ୍ୟା"),
        ("LÞÔ", "କ୍ୟି"),
        ("LÑÔ", "କ୍ୟୀ"),
        ("LÊÔ", "କ୍ୟୁ"),
        ("LËÔ", "କ୍ୟୂ"),
        ("LÌÔ", "କ୍ୟୃ"),
        ("ÒLÊÔ", "କ୍ୟେୁ"),
        ("ÒLßÔ", "କ୍ୟୈ"),
        ("ÒLÐÔ", "କ୍ୟୋ"),
        ("ÒL×Ô", "କ୍ୟୌ"),
        ("LÜÔ", "କ୍ୟଁ"),
        ("LÕÔ", "କ୍ୟଂ"),
        ("LÚÔ", "କ୍ୟିଁ"),
    ],
)
def test_ortt_ya_phala_moves_ahead_of_each_sign_typed_before_it(source: str, expected: str) -> None:
    assert legacy.to_unicode(source, font="ORTTSarala") == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ÒLÔçL", "କ୍ୟ୍\u200dକେ"),
        ("ÒLÔÍ", "କ୍ୟ୍ରେ"),
        ("ÒLÔÍß", "କ୍ୟ୍ରୈ"),
        ("ÒLÔÍ×", "କ୍ୟ୍ରୌ"),
        ("ÒLçLÔ", "କ୍\u200dକ୍ୟେ"),
        ("ÒLÍÔ", "କ୍ର୍ୟେ"),
    ],
)
def test_a_left_matra_goes_after_every_subjoined_form_past_a_ya_phala(source: str, expected: str) -> None:
    assert legacy.to_unicode(source, font="ORTTSarala") == expected


@pytest.mark.parametrize(
    ("after", "before", "expected"),
    [
        ("ÒL™Ô", "ÒLÔ™", "ର୍କ୍ୟେଁ"),
        ("LÙÔ", "LÔÙ", "ର୍କ୍ୟି"),
        ("L™Ô", "LÔ™", "ର୍କ୍ୟଁ"),
    ],
)
def test_ya_phala_after_a_combined_reph_glyph_matches_the_other_key_order(after: str, before: str, expected: str) -> None:
    assert legacy.to_unicode(after, font="ORTTSarala") == expected
    assert legacy.to_unicode(before, font="ORTTSarala") == expected


YA_PHALA_SIGN_ROWS = (
    ("LÐ", "Ð", "କ୍ୟ୍ରା"),
    ("LÞ", "Þ", "କ୍ୟ୍ରି"),
    ("LÑ", "Ñ", "କ୍ୟ୍ରୀ"),
    ("LÊ", "Ê", "କ୍ୟ୍ରୁ"),
    ("LË", "Ë", "କ୍ୟ୍ରୂ"),
    ("LÌ", "Ì", "କ୍ୟ୍ରୃ"),
    ("ÒLÊ", "Ê", "କ୍ୟ୍ରେୁ"),
    ("ÒLß", "ß", "କ୍ୟ୍ରୈ"),
    ("ÒLÐ", "Ð", "କ୍ୟ୍ରୋ"),
    ("ÒL×", "×", "କ୍ୟ୍ରୌ"),
    ("LÜ", "Ü", "କ୍ୟ୍ରଁ"),
    ("LÕ", "Õ", "କ୍ୟ୍ରଂ"),
    ("LÚ", "Ú", "କ୍ୟ୍ରିଁ"),
)
assert len(YA_PHALA_SIGN_ROWS) == 13


@pytest.mark.parametrize(("typed", "sign", "expected"), YA_PHALA_SIGN_ROWS)
def test_each_sign_typed_before_a_ya_phala_goes_after_the_subjoined_ra_typed_after_it(
    typed: str, sign: str, expected: str
) -> None:
    other_order = typed.removesuffix(sign) + "ÔÍ" + sign
    assert legacy.to_unicode(typed + "ÔÍ", font="ORTTSarala") == expected
    assert legacy.to_unicode(other_order, font="ORTTSarala") == expected


SUBJOINED_AFTER_YA_PHALA = (
    ("LÐÔÍ", "LÔÍÐ", "କ୍ୟ୍ରା"),
    ("LÜÔÍ", "LÔÍÜ", "କ୍ୟ୍ରଁ"),
    ("L™ÔÍ", "LÔÍ™", "ର୍କ୍ୟ୍ରଁ"),
    ("LÙÔ˜", "LÔ˜Ù", "ର୍କ୍ୟ୍ଳି"),
    ("LÐÔçL", "LÔçLÐ", "କ୍ୟ୍\u200dକା"),
    ("LÐÔçk", "LÔçkÐ", "କ୍ୟ୍\u200dହା"),
    ("LÐÔç¯", "LÔç¯Ð", "କ୍ୟ୍\u200dୟା"),
    ("LÐÔš", "LÔšÐ", "କ୍ୟ୍ୱା"),
    ("LÐÔçXÏ", "LÔçXÏÐ", "କ୍ୟ୍\u200dଡ଼ା"),
    ("LÐÔÍ˜", "LÔÍ˜Ð", "କ୍ୟ୍ର୍ଳା"),
)
assert len(SUBJOINED_AFTER_YA_PHALA) == 10


@pytest.mark.parametrize(("typed", "other_order", "expected"), SUBJOINED_AFTER_YA_PHALA)
def test_a_sign_before_a_ya_phala_lands_after_every_subjoined_form_typed_after_it(
    typed: str, other_order: str, expected: str
) -> None:
    assert legacy.to_unicode(typed, font="ORTTSarala") == expected
    assert legacy.to_unicode(other_order, font="ORTTSarala") == expected


@pytest.mark.parametrize(
    ("reph_first", "reph_last", "expected"),
    [
        ("ÒLàß", "ÒLßà", "ର୍କୈ"),
        ("ÒLà×", "ÒL×à", "ର୍କୌ"),
        ("ÒLàÜß", "ÒLÜßà", "ର୍କୈଁ"),
    ],
)
def test_reph_before_the_right_half_of_a_composite_matra_matches_the_other_key_order(
    reph_first: str, reph_last: str, expected: str
) -> None:
    assert legacy.to_unicode(reph_first, font="ORTTSarala") == expected
    assert legacy.to_unicode(reph_last, font="ORTTSarala") == expected


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
    with pytest.raises(TypeError):
        _convert._matra(None)
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
        _convert._rules([["a", 1]])
    with pytest.raises(TypeError):
        _convert._rules(None)
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

RELEASE_SENTENCE = "`openodia.legacy` needs a release newer than 0.2.0: `import openodia.legacy` fails on 0.2.0"
RELEASE_PAGES = ("README.md", "docs/index.md", "docs/llms.txt", "AGENTS.md")


def test_auto_mode_passthrough_is_documented() -> None:
    text = (Path(__file__).resolve().parents[1] / "docs/index.md").read_text(encoding="utf-8")
    assert "A tie leaves `font` as None and `confidence` at 0.5." in text
    assert "No legacy-font evidence leaves `font` as None and `confidence` at 0.0." in text
    assert "Text that contains an Odia code point or a danda is already Unicode, so it has no legacy-font evidence" in text
    assert "`to_unicode_auto` returns the input unchanged in both cases." in text
    assert "Call `detect_font` to tell them apart." in text
    assert "auto mode converts 83 and leaves 17 unchanged." in text


@pytest.mark.parametrize("page", RELEASE_PAGES)
def test_legacy_pages_name_the_release(page: str) -> None:
    text = (Path(__file__).resolve().parents[1] / page).read_text(encoding="utf-8")
    assert RELEASE_SENTENCE in text


@pytest.mark.parametrize(("font", "byte", "expected"), CP1252_BYTES)
def test_cp1252_only_bytes_convert(font: str, byte: int, expected: str) -> None:
    assert legacy.to_unicode(legacy.decode(bytes([byte])), font=font) == expected


@pytest.mark.parametrize(
    ("byte", "expected"),
    ((0x81, "ଞ୍ଚ"), (0x8D, "ଣ୍ଟ"), (0x8F, "ତ୍ତ"), (0x9D, "ତ୍ଥ")),
)
def test_bytes_cp1252_leaves_undefined_still_convert(byte: int, expected: str) -> None:
    assert legacy.to_unicode(legacy.decode(bytes([byte])), font="AkrutiOriSarala") == expected


def test_ghanta_survives_the_documented_decode() -> None:
    assert legacy.to_unicode(legacy.decode(b"N\x8d\xfb"), font="AkrutiOriSarala") == "ଘଣ୍ଟା"


def test_decode_rejects_text() -> None:
    with pytest.raises(TypeError):
        legacy.decode("N")


def test_ellipsis_byte_is_cp1252_not_latin_1() -> None:
    assert legacy.decode(b"\x85") == "\u2026"
    assert legacy.to_unicode(legacy.decode(b"\x85"), font="AkrutiOriSarala") == "ଟ୍ଟ"
    assert legacy.to_unicode(b"\x85".decode("latin-1"), font="AkrutiOriSarala") == "\u0085"


def test_decode_uses_cp1252_for_every_defined_byte() -> None:
    data = bytes(range(0x80, 0xA0))
    expected = "".join(
        chr(byte) if byte in {0x81, 0x8D, 0x8F, 0x90, 0x9D} else bytes([byte]).decode("cp1252") for byte in data
    )
    assert legacy.decode(data) == expected
    assert legacy.decode(bytearray(data)) == expected


def test_decode_of_empty_bytes_is_empty() -> None:
    assert legacy.decode(b"") == ""
    assert legacy.decode(bytearray()) == ""


def test_reph_walks_every_halant_in_the_conjunct() -> None:
    assert legacy.to_unicode("crÔà", font="ORTTSarala") == "ମର୍ତ୍ତ୍ୟ"


def test_yaphala_moves_past_every_vowel_sign() -> None:
    assert legacy.to_unicode("OãôÔg", font="ORTTSarala") == "ଘ୍ୟୁୃୱ"


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("ÒLÕÔ", "କ୍ୟେଂ"),
        ("ÒLÔÕ", "କ୍ୟେଂ"),
        ("LÕÔ", "କ୍ୟଂ"),
        ("LÜÔ", "କ୍ୟଁ"),
        ("LÔÜ", "କ୍ୟଁ"),
    ),
)
def test_yaphala_moves_past_a_nasal_typed_before_it(text: str, expected: str) -> None:
    assert legacy.to_unicode(text, font="ORTTSarala") == expected


def test_matra_moves_across_a_halant_that_carries_a_joiner() -> None:
    assert legacy.to_unicode("ÒLçL", font="ORTTSarala") == "କ୍‍କେ"


def test_reph_moves_across_a_halant_that_carries_a_joiner() -> None:
    assert legacy.to_unicode("LçLà", font="ORTTSarala") == "ର୍କ୍‍କ"
    assert legacy.to_unicode("LàçL", font="ORTTSarala") == "ର୍କ୍‍କ"


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("ÒLÕÔß", "କ୍ୟୈଂ"),
        ("ÒLÔÕß", "କ୍ୟୈଂ"),
        ("ÒLÕÔ×", "କ୍ୟୌଂ"),
        ("ÒLÔÕ×", "କ୍ୟୌଂ"),
    ),
)
def test_yaphala_reorders_across_a_nasal_before_a_composite_matra(text: str, expected: str) -> None:
    assert legacy.to_unicode(text, font="ORTTSarala") == expected


def test_every_numeric_separator_in_a_run_converts() -> None:
    assert legacy.to_unicode("1Ð2Ð3", font="ORTTSarala") == "୧|୨|୩"
    assert legacy.to_unicode("1Ð2", font="ORTTSarala") == "୧|୨"


@pytest.mark.parametrize(
    "text",
    (
        "ପ",
        "ପ ୧।୨",
        "ଓଡ଼ିଆ ଭାଷା ସୁନ୍ଦର ।",
        "୧୨୩ ॥",
        "ସତ୍ଯ",
        "ଯୋଗ୍ଯ କାର୍ଯ୍ଯ ।",
        " ଙ୍ଗ ",
        "ଏହା 25% ଅଧିକ",
        "ମୂଲ୍ୟ 10% ବଢ଼ିଲା ।",
        "ଓଡ଼ିଆ #OpenOdia",
        "2+2=4 > 3 ଠିକ୍",
        "ପ " + "".join(chr(code) for code in range(0x21, 0x7F)),
    ),
)
def test_unicode_odia_is_not_detected_as_a_legacy_font(text: str) -> None:
    assert legacy.detect_font(text) == {"font": None, "confidence": 0.0}
    assert legacy.to_unicode_auto(text) == text


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
    converted = sum(legacy.to_unicode_auto(row["legacy"]) == row["unicode"] for rows in fixture.values() for row in rows)
    assert converted == 83


def test_font_evidence_holds_no_odia_or_danda() -> None:
    target = {chr(code) for code in range(0x0B00, 0x0B80)} | {"\u0964", "\u0965"}
    for font in _convert._FONTS:
        assert font.signatures
        assert not any(set(signature) & target for signature in font.signatures)
        assert font.alphabet
        assert not font.alphabet & target


@pytest.mark.parametrize("page", ("CHANGELOG.md", "docs/index.md", "openodia/legacy/_convert.py"))
def test_docs_name_every_byte_cp1252_leaves_undefined(page: str) -> None:
    undefined = [byte for byte in range(0x80, 0xA0) if bytes([byte]).decode("cp1252", "ignore") == ""]
    names = [f"0x{byte:02X}" for byte in undefined]
    listed = ", ".join(names[:-1]) + " and " + names[-1]
    text = " ".join((Path(__file__).resolve().parents[1] / page).read_text(encoding="utf-8").split())
    assert listed == "0x81, 0x8D, 0x8F, 0x90 and 0x9D"
    assert listed in text


LEGACY_RULE_FILES = ("CHANGELOG.md", "docs/index.md")
assert len(LEGACY_RULE_FILES) == 2
EXAMPLE = re.compile(r"`([^`]+)` and `([^`]+)` both give `([^`]+)`")


@pytest.mark.parametrize("path", LEGACY_RULE_FILES)
def test_every_both_orders_example_on_the_page_is_what_the_converter_gives(path: str) -> None:
    text = (Path(__file__).parent.parent / path).read_text(encoding="utf-8")
    examples = EXAMPLE.findall(text)
    assert len(examples) == 3
    for first, second, expected in examples:
        font = "AkrutiOriSarala" if first.startswith("ù") else "ORTTSarala"
        assert legacy.to_unicode(first, font=font) == expected
        assert legacy.to_unicode(second, font=font) == expected


KEY_ORDER_PAIRS = (
    ("ORTTSarala", "ÒLÕÔÍ", "ÒLÔÍÕ", "କ୍ୟ୍ରେଂ"),
    ("ORTTSarala", "ÒLÜÔÍ", "ÒLÔÍÜ", "କ୍ୟ୍ରେଁ"),
    ("ORTTSarala", "ÒLÕÔçL", "ÒLÔçLÕ", "କ୍ୟ୍\u200dକେଂ"),
    ("ORTTSarala", "ÒLàÔß", "ÒLÔßà", "ର୍କ୍ୟୈ"),
    ("ORTTSarala", "ÒLàÔ×", "ÒLÔ×à", "ର୍କ୍ୟୌ"),
    ("ORTTSarala", "ÒLàÔÐ", "ÒLÔÐà", "ର୍କ୍ୟୋ"),
    ("ORTTSarala", "ÒLÕÍ", "ÒLÍÕ", "କ୍ରେଂ"),
    ("ORTTSarala", "ÒLÜÍ", "ÒLÍÜ", "କ୍ରେଁ"),
    ("ORTTSarala", "ÒLàÍ", "ÒLÍà", "ର୍କ୍ରେ"),
    ("ORTTSarala", "ÒLàçL", "ÒLçLà", "ର୍କ୍\u200dକେ"),
    ("ORTTSarala", "ÒLàÍß", "ÒLÍßà", "ର୍କ୍ରୈ"),
    ("ORTTSarala", "ÒLÕÍß", "ÒLÍÕß", "କ୍ରୈଂ"),
    ("ORTTSarala", "LÓÊ", "LÊÓ", "କୁଃ"),
    ("AkrutiOriSarala", "ùKõ£", "ùK£õ", "କ୍ମେଂ"),
    ("AkrutiOriSarala", "ùKõ£ø", "ùK£õø", "କ୍ମୌଂ"),
    ("AkrutiOriSarala", "Küé", "Kéü", "କୃଃ"),
)
assert len(KEY_ORDER_PAIRS) == 16


@pytest.mark.parametrize(("font", "typed", "other_order", "expected"), KEY_ORDER_PAIRS)
def test_a_syllable_gives_the_same_output_in_either_key_order(font: str, typed: str, other_order: str, expected: str) -> None:
    assert legacy.to_unicode(typed, font=font) == expected
    assert legacy.to_unicode(other_order, font=font) == expected


SIGN_BEFORE_HALANT = re.compile("[ାିୀୁୂୃେୈୋୌଁଂଃ]୍")


def _font(font_name: str) -> "_convert._Font":
    [font] = [font for font in _convert._FONTS if font.name == font_name]
    return font


def _keys(font_name: str, extra: str) -> list[str]:
    return sorted(_font(font_name).alphabet | set(extra))


def test_no_two_key_ortt_syllable_leaves_a_sign_before_a_halant() -> None:
    keys = _keys("ORTTSarala", "ÔàÒ")
    assert len(keys) == 188
    inputs = [lead + "L" + first + ya + second for lead in ("", "Ò") for first in keys for ya in ("", "Ô") for second in keys]
    assert len(inputs) == 141376
    bad = [text for text in inputs if SIGN_BEFORE_HALANT.search(legacy.to_unicode(text, font="ORTTSarala"))]
    assert bad == []


def _raw_glyphs(font_name: str, text: str) -> list[str]:
    return [char for char in text if not char.isascii() and char in _font(font_name).alphabet]


def test_seeded_random_ortt_text_leaves_no_sign_before_a_halant() -> None:
    keys = _keys("ORTTSarala", "")
    picker = random.Random(301)
    inputs = ["".join(picker.choices(keys, k=picker.randint(1, 8))) for _ in range(20000)]
    assert len(inputs) == 20000
    bad = [text for text in inputs if SIGN_BEFORE_HALANT.search(legacy.to_unicode(text, font="ORTTSarala"))]
    assert bad == []


@pytest.mark.parametrize(("font_name", "text"), [("ORTTSarala", "ôÒð"), ("ORTTSarala", "L ÊÔ"), ("AkrutiOriSarala", "ëùÔ")])
def test_signs_typed_without_a_base_letter_go_after_the_subjoined_form(font_name: str, text: str) -> None:
    output = legacy.to_unicode(text, font=font_name)
    assert output.startswith("୍") or output.startswith("କ ୍")
    assert SIGN_BEFORE_HALANT.search(output) is None


@pytest.mark.parametrize(
    ("font_name", "lead", "sizes"), [("ORTTSarala", "ÒL", (7, 22, 4)), ("AkrutiOriSarala", "ùK", (3, 31, 4))]
)
def test_a_nasal_or_reph_before_a_subjoined_form_leaves_no_sign_before_a_halant_or_raw_glyph(
    font_name: str, lead: str, sizes: tuple[int, int, int]
) -> None:
    font = _font(font_name)
    between = [src for src, dst in font.pairs if len(src) == 1 and dst != "" and set(dst) <= set("ଁଂଃ")]
    between += [font.reph] if font.reph is not None else []
    subjoined = [src for src, dst in font.pairs if len(src) == 1 and dst.startswith("୍")]
    halves = [""] + [suffix for suffix, _sign in font.matra.forms]
    assert (len(between), len(subjoined), len(halves)) == sizes
    for text in (lead + mark + form + half for mark in between for form in subjoined for half in halves):
        output = legacy.to_unicode(text, font=font_name)
        assert SIGN_BEFORE_HALANT.search(output) is None, text
        assert _raw_glyphs(font_name, output) == [], text


def test_a_reph_with_no_consonant_in_its_syllable_stays_where_it_was_typed() -> None:
    assert legacy.to_unicode("Óà", font="ORTTSarala") == "ଃର୍"
