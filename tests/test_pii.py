import pytest

from openodia import numbers, pii
from openodia.pii import PIIEntity

VALID_AADHAAR = "234567890124"
GROUPED_AADHAAR = "2345 6789 0124"
ODIA_GROUPED_AADHAAR = numbers.ascii_to_odia(GROUPED_AADHAAR)
CHECKSUM_FAILING = "234567890125"


def kinds(text: str, **options: object) -> list[tuple[str, str]]:
    return [(entity.type, entity.text) for entity in pii.detect(text, **options)]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ମୋ ଫୋନ ୯୯୯୯୯୯୯୯୯୯ ।", "୯୯୯୯୯୯୯୯୯୯"),
        ("call 9876543210 now", "9876543210"),
        ("call 98765 43210 now", "98765 43210"),
        ("call +91 98765 43210 now", "+91 98765 43210"),
        ("call +91-9876543210 now", "+91-9876543210"),
        ("call 09876543210 now", "09876543210"),
    ],
)
def test_phone_formats(text: str, expected: str) -> None:
    assert kinds(text) == [("PHONE", expected)]


@pytest.mark.parametrize("text", ["call 5876543210", "call 98765432", "call 98765432101", "call 12345678901234"])
def test_non_phone_digit_runs_are_ignored(text: str) -> None:
    assert kinds(text) == []


def test_entity_offsets_index_the_original_text() -> None:
    text = "ମୋ ଫୋନ ୯୯୯୯୯୯୯୯୯୯ ।"
    [entity] = pii.detect(text)
    assert text[entity.start : entity.end] == entity.text
    assert entity == PIIEntity("PHONE", "୯୯୯୯୯୯୯୯୯୯", text.index("୯"), text.index("୯") + 10, 0.9)


@pytest.mark.parametrize("text", ["a.b+c@example.co.in", "ମୋ ଇମେଲ a@b.com ଅଟେ"])
def test_email(text: str) -> None:
    [(kind, found)] = kinds(text)
    assert kind == "EMAIL"
    assert found in text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("see https://openodia.soumendrak.com/docs?a=1.", "https://openodia.soumendrak.com/docs?a=1"),
        ("see www.example.com, ok", "www.example.com"),
        ("ଦେଖନ୍ତୁ https://example.com/ପୃଷ୍ଠା।", "https://example.com/ପୃଷ୍ଠା"),
        ("(http://example.com)", "http://example.com"),
    ],
)
def test_url_excludes_trailing_punctuation(text: str, expected: str) -> None:
    assert kinds(text) == [("URL", expected)]


def test_email_inside_url_is_one_url_entity() -> None:
    assert kinds("https://example.com/?to=a@b.com") == [("URL", "https://example.com/?to=a@b.com")]


@pytest.mark.parametrize("number", [VALID_AADHAAR, GROUPED_AADHAAR, ODIA_GROUPED_AADHAAR, "2345-6789-0124"])
def test_aadhaar_with_valid_checksum(number: str) -> None:
    [entity] = pii.detect(f"ଆଧାର {number} ।")
    assert (entity.type, entity.text, entity.confidence) == ("AADHAAR", number, 0.95)


def test_aadhaar_with_failing_checksum_is_low_confidence() -> None:
    [entity] = pii.detect(CHECKSUM_FAILING)
    assert (entity.type, entity.confidence) == ("AADHAAR", 0.5)


def test_min_confidence_drops_checksum_failures() -> None:
    assert kinds(f"{CHECKSUM_FAILING} {VALID_AADHAAR}", min_confidence=0.9) == [("AADHAAR", VALID_AADHAAR)]


@pytest.mark.parametrize("number", ["123456789012", "023456789012", "2345 6789 012", "2345 67890124"])
def test_aadhaar_shape_rules(number: str) -> None:
    assert kinds(number) == []


def test_aadhaar_wins_over_phone_lookalike() -> None:
    assert kinds("987654321096") == [("AADHAAR", "987654321096")]


@pytest.mark.parametrize(("text", "expected"), [("PAN ABCPE1234F ଅଛି", "ABCPE1234F"), ("ABCPE୧୨୩୪F", "ABCPE୧୨୩୪F")])
def test_pan(text: str, expected: str) -> None:
    assert kinds(text) == [("PAN", expected)]


@pytest.mark.parametrize("text", ["ABCZE1234F", "abcpe1234f", "XABCPE1234F", "ABCPE1234FG"])
def test_pan_rejects_bad_shapes(text: str) -> None:
    assert kinds(text) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("PIN 751001", "751001"),
        ("pincode: 751001", "751001"),
        ("PIN code - 751001", "751001"),
        ("ପିନ ୭୫୧୦୦୧", "୭୫୧୦୦୧"),
        ("ପିନ୍‌କୋଡ୍: ୭୫୧୦୦୧", "୭୫୧୦୦୧"),
    ],
)
def test_pincode_needs_context(text: str, expected: str) -> None:
    assert kinds(text) == [("PINCODE", expected)]


@pytest.mark.parametrize("text", ["751001", "amount 751001", "SPIN 751001", "PIN 051001", "PIN 7510011"])
def test_pincode_without_context_or_shape_is_ignored(text: str) -> None:
    assert kinds(text) == []


@pytest.mark.parametrize("text", ["98765\n43210", "2345\n6789\n0124"])
def test_a_line_break_does_not_join_digit_groups(text: str) -> None:
    assert kinds(text) == []


def test_types_filter_and_validation() -> None:
    text = "a@b.com 9876543210"
    assert kinds(text, types=["EMAIL"]) == [("EMAIL", "a@b.com")]
    with pytest.raises(ValueError, match="unknown PII type"):
        pii.detect(text, types=["NAME"])


def test_detect_returns_entities_sorted_by_position() -> None:
    text = f"9876543210 a@b.com {VALID_AADHAAR}"
    assert [entity.type for entity in pii.detect(text)] == ["PHONE", "EMAIL", "AADHAAR"]


def test_detect_finds_nothing_in_plain_odia() -> None:
    assert pii.detect("ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।") == []
    assert pii.detect("") == []


def test_mask_replaces_with_type_tags() -> None:
    assert pii.mask("ଫୋନ 9876543210, ମେଲ a@b.com") == "ଫୋନ <PHONE>, ମେଲ <EMAIL>"


def test_mask_is_idempotent() -> None:
    once = pii.mask(f"9876543210 a@b.com {VALID_AADHAAR} PIN 751001 ABCPE1234F https://x.com")
    assert once == "<PHONE> <EMAIL> <AADHAAR> PIN <PINCODE> <PAN> <URL>"
    assert pii.mask(once) == once


def test_mask_honours_types_and_min_confidence() -> None:
    text = f"9876543210 a@b.com {CHECKSUM_FAILING}"
    assert pii.mask(text, types=["PHONE"]) == f"<PHONE> a@b.com {CHECKSUM_FAILING}"
    assert pii.mask(text, min_confidence=0.9) == f"<PHONE> <EMAIL> {CHECKSUM_FAILING}"


def test_mask_accepts_custom_placeholder() -> None:
    masked = pii.mask("call 9876543210", placeholder=lambda entity: "*" * (len(entity.text) - 4) + entity.text[-4:])
    assert masked == "call ******3210"


def test_verhoeff_checksum() -> None:
    from openodia.pii._verhoeff import is_valid

    assert is_valid("2363")
    assert not is_valid("2364")
    assert is_valid(VALID_AADHAAR)


@pytest.mark.parametrize("doc", ["AGENTS.md", "docs/index.md"])
def test_docs_name_every_pii_type(doc: str) -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / doc).read_text(encoding="utf-8")
    assert all(f"`{kind}`" in text for kind in pii.PII_TYPES)
