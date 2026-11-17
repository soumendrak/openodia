import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import pytest

from openodia import numbers, pii
from openodia.pii import KeyStore, PIIEntity, _detect

from .test_pii import CHECKSUM_FAILING, VALID_AADHAAR, kinds


def test_aadhaar_verhoeff_accepts_odia_and_ascii_and_lowers_a_bad_checksum() -> None:
    odia_valid = numbers.ascii_to_odia(VALID_AADHAAR)
    odia_bad = numbers.ascii_to_odia(CHECKSUM_FAILING)
    assert [entity.confidence for entity in pii.detect(VALID_AADHAAR)] == [0.95]
    assert [entity.confidence for entity in pii.detect(odia_valid)] == [0.95]
    assert [entity.confidence for entity in pii.detect(CHECKSUM_FAILING)] == [0.5]
    assert [entity.confidence for entity in pii.detect(odia_bad)] == [0.5]


@pytest.mark.parametrize(
    ("text", "expected", "confidence"),
    [
        ("ଜନ୍ମ 15 January 2024 ରେ", "15 January 2024", 0.85),
        ("ଜନ୍ମ ୧୫ ଜାନୁଆରୀ ୨୦୨୪ ରେ", "୧୫ ଜାନୁଆରୀ ୨୦୨୪", 0.85),
        ("on 15th January 2024.", "15th January 2024", 0.85),
        ("May 4, 2024", "May 4, 2024", 0.85),
        ("୨୯ ଫେବ୍ରୁଆରୀ ୨୦୨୪", "୨୯ ଫେବ୍ରୁଆରୀ ୨୦୨୪", 0.85),
        ("issued 15/01/2024 today", "15/01/2024", 0.7),
        ("issued ୧୫-୦୧-୨୦୨୪ today", "୧୫-୦୧-୨୦୨୪", 0.7),
        ("issued 5.1.2024 today", "5.1.2024", 0.7),
    ],
)
def test_dates_in_odia_or_english_with_a_real_calendar_day(text: str, expected: str, confidence: float) -> None:
    [entity] = pii.detect(text)
    assert (entity.type, entity.text, entity.confidence) == ("DATE", expected, confidence)
    assert text[entity.start : entity.end] == expected


@pytest.mark.parametrize(
    "text",
    [
        "31/02/2024",
        "୩୧/୦୨/୨୦୨୪",
        "29 February 2023",
        "01/13/2024",
        "15/01/1899",
        "15/01/2100",
        "15 January",
        "January 2024",
        "15\nJanuary 2024",
        "1.2.3",
    ],
)
def test_impossible_or_partial_dates_are_ignored(text: str) -> None:
    assert kinds(text) == []


def test_min_confidence_keeps_a_named_date_and_drops_a_numeric_one() -> None:
    assert kinds("on 15 January 2024 and 15/01/2024", min_confidence=0.8) == [("DATE", "15 January 2024")]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ଦାମ ₹500 ଟେ", "₹500"),
        ("ଦାମ ₹୫୦୦ ଟେ", "₹୫୦୦"),
        ("fee Rs. 1,50,000 only", "Rs. 1,50,000"),
        ("fee rs500 only", "rs500"),
        ("total INR 99.50", "INR 99.50"),
        ("ମୂଲ୍ୟ ୫୦୦ ଟଙ୍କା ଅଟେ", "୫୦୦ ଟଙ୍କା"),
        ("ମୂଲ୍ୟ 500 ରୁପିଆ ଅଟେ", "500 ରୁପିଆ"),
    ],
)
def test_money_needs_a_currency_marker(text: str, expected: str) -> None:
    assert kinds(text) == [("MONEY", expected)]


@pytest.mark.parametrize("text", ["500", "୫୦୦", "the cost is 500", "500 ଟଙ୍କାରେ", "xRs 10"])
def test_a_bare_number_or_inflected_tanka_is_not_money(text: str) -> None:
    assert kinds(text) == []


@pytest.mark.parametrize(
    "text",
    ["1,5 ଟଙ୍କା", "1,2345 ଟଙ୍କା", "1234,50 ଟଙ୍କା", "500. ଟଙ୍କା", "500.123 ଟଙ୍କା", "₹", "ମୂଲ୍ୟ ଟଙ୍କା"],
)
def test_a_broken_amount_shape_is_not_money(text: str) -> None:
    assert pii.detect(text, types=["MONEY"]) == []


def test_an_overlong_ungrouped_amount_is_left_entirely_visible() -> None:
    text = "1234567890123 ଟଙ୍କା"
    assert pii.detect(text, types=["MONEY"]) == []
    assert pii.mask(text, types=["MONEY"]) == text
    assert kinds("123456789012 ଟଙ୍କା") == [("MONEY", "123456789012 ଟଙ୍କା")]


def test_a_long_comma_separated_number_without_a_currency_marker_stays_fast() -> None:
    text = "11," * 8_000 + "11"
    started = time.perf_counter()
    assert pii.detect(text) == []
    assert time.perf_counter() - started < 0.5


def test_dictionary_given_name_and_surname_is_a_name() -> None:
    text = "ବୈଦ୍ୟନାଥ ସିଂହଦେଓ ଆସିଲେ"
    assert kinds(text) == [("NAME", "ବୈଦ୍ୟନାଥ ସିଂହଦେଓ")]
    [entity] = pii.detect(text)
    assert entity.confidence == 0.7


@pytest.mark.parametrize("text", ["ବ\u0b5c ଘର", "କ\u0b4d\u0b3c", "ପ\u0b5dା", "a\u0301\u0323", "ଉ\u0b5cାଣଗୁଡିକ"])
def test_expanded_nfc_keeps_offsets_inside_the_original_text(text: str) -> None:
    pii.mask(text)
    for entity in pii.detect(text):
        assert text[entity.start : entity.end] == entity.text


def test_detect_finishes_when_nfc_expands_a_letter() -> None:
    script = """
import unicodedata
from openodia import pii
samples = ["ବ\\u0B5C ଘର", "କ\\u0B4D\\u0B3C", "ପ\\u0B5Dା", "a\\u0301\\u0323", "ଉ\\u0B5Cାଣଗୁଡିକ"]
for text in samples:
    for entity in pii.detect(text):
        assert text[entity.start:entity.end] == entity.text, text
    pii.mask(text)
    pii.pseudonymize(text, pii.KeyStore())
print("ok")
"""
    completed = subprocess.run([sys.executable, "-c", script], check=False, capture_output=True, text=True, timeout=5)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok"


def test_a_decomposed_letter_before_a_span_does_not_shift_it() -> None:
    for prefix in ("ମୋ ଗୌରବ ", "ଗୋ"):
        text = unicodedata.normalize("NFD", prefix) + "a@b.com"
        assert pii.mask(text) == unicodedata.normalize("NFD", prefix) + "<EMAIL>"
        for entity in pii.detect(text):
            assert text[entity.start : entity.end] == entity.text


def test_nfd_text_masks_the_same_name_and_date_as_nfc() -> None:
    for text in ("ଶ୍ରୀ ଗୌତମ ଦାସ", "ଜନ୍ମ ୧୫ ଅକ୍ଟୋବର ୨୦୨୪"):
        nfd = unicodedata.normalize("NFD", text)
        assert nfd != text
        assert pii.mask(nfd) == unicodedata.normalize("NFD", pii.mask(text))
        for entity in pii.detect(nfd):
            assert nfd[entity.start : entity.end] == entity.text


def test_consecutive_surnames_are_masked_with_the_given_name() -> None:
    assert pii.mask("ଅଶୋକ କୁମାର ଦାସ") == "<NAME>"
    assert pii.mask("ଶ୍ରୀ ଅଶୋକ କୁମାର ଦାସ ମହାପାତ୍ର") == "<NAME>"
    assert pii.mask("ଅଶୋକ ଚନ୍ଦ୍ର ଦାସ ମହାପାତ୍ର") == "<NAME>"


def test_a_surname_run_stops_at_a_comma_and_at_a_given_name() -> None:
    assert pii.mask("ଅଶୋକ ଦାସ, ମହାପାତ୍ର ଆସିଲେ") == "<NAME>, ମହାପାତ୍ର ଆସିଲେ"
    assert pii.mask("ଅଶୋକ ଦାସ ଅଶୋକ") == "<NAME> ଅଶୋକ"


@pytest.mark.parametrize("gap", [" ", "  ", "\t", "\u00a0", "\n", " \u00a0\t"])
def test_name_words_separated_by_any_whitespace_run_are_masked_whole(gap: str) -> None:
    for words in (["ଅଶୋକ", "ଦାସ"], ["ଶ୍ରୀ", "ଅଶୋକ"], ["ଅଶୋକ", "କୁମାର", "ଦାସ", "ମହାପାତ୍ର"], ["ଗୁନ୍", "ଗୁନ୍", "ସିଂହଦେଓ"]):
        text = "ମୁଁ " + gap.join(words) + " ଆସିଲି"
        assert pii.mask(text, types=["NAME"]) == "ମୁଁ <NAME> ଆସିଲି"
        [entity] = pii.detect(text, types=["NAME"])
        assert text[entity.start : entity.end] == entity.text == gap.join(words)


def test_a_surname_written_with_a_precomposed_nukta_letter_is_masked_to_its_end() -> None:
    text = "ଅଶୋକ ମହାକୁ\u0b5c"
    assert pii.mask(text) == "<NAME>"
    [entity] = pii.detect(text, types=["NAME"])
    assert (entity.start, entity.end) == (0, len(text))


def test_an_ungrouped_amount_before_a_comma_is_masked() -> None:
    assert pii.mask("paid ₹1500, thanks") == "paid <MONEY>, thanks"
    assert pii.mask("paid 1500 ଟଙ୍କା, thanks") == "paid <MONEY>, thanks"


@pytest.mark.parametrize(("marks", "masked_tail"), [(31, "\u0302" * 31), (32, "")])
def test_runs_up_to_32_code_points_map_exactly_and_longer_runs_map_to_the_run_end(marks: int, masked_tail: str) -> None:
    prefix = unicodedata.normalize("NFD", "ଗୋ ")
    text = prefix + "x@y.com" + "\u0302" * marks
    assert pii.mask(text) == prefix + "<EMAIL>" + masked_tail


def test_an_honorific_includes_three_dictionary_words_and_not_only_two() -> None:
    assert pii.mask("ଶ୍ରୀ ଅଶୋକ କୁମାର ଦାସ") == "<NAME>"


def test_a_currency_prefix_does_not_mask_part_of_an_overlong_amount() -> None:
    assert pii.mask("₹1234567890123") == "₹1234567890123"
    assert pii.mask("₹123456789012") == "<MONEY>"


def test_address_gap_includes_40_characters_and_excludes_41() -> None:
    inside = "ଜିଲ୍ଲା" + "x" * 40 + "123456"
    outside = "ଜିଲ୍ଲା" + "x" * 41 + "123456"
    assert kinds(inside, types=["ADDRESS"]) == [("ADDRESS", inside)]
    assert kinds(outside, types=["ADDRESS"]) == []


def test_a_token_already_in_the_input_is_rewritten_on_restore() -> None:
    store = KeyStore()
    text = "ପୂର୍ବ <EMAIL:1> ଓ a@b.com"
    assert pii.restore(pii.pseudonymize(text, store), store) == "ପୂର୍ବ a@b.com ଓ a@b.com"


def test_a_dictionary_given_name_that_contains_a_space_is_detected() -> None:
    assert kinds("ଗୁନ୍ ଗୁନ୍ ସିଂହଦେଓ ଆସିଲେ") == [("NAME", "ଗୁନ୍ ଗୁନ୍ ସିଂହଦେଓ")]
    assert kinds("ଶ୍ରୀ ଗୁନ୍ ଗୁନ୍ ଆସିଲେ") == [("NAME", "ଶ୍ରୀ ଗୁନ୍ ଗୁନ୍")]


def test_a_dictionary_middle_name_stays_inside_the_name() -> None:
    assert kinds("ବୈଦ୍ୟନାଥ କିଶୋର ସିଂହଦେଓ ଆସିଲେ") == [("NAME", "ବୈଦ୍ୟନାଥ କିଶୋର ସିଂହଦେଓ")]


def test_an_honorific_plus_a_dictionary_name_is_a_name() -> None:
    text = "ଶ୍ରୀ ବୈଦ୍ୟନାଥ ସିଂହଦେଓ ଆସିଲେ"
    assert kinds(text) == [("NAME", "ଶ୍ରୀ ବୈଦ୍ୟନାଥ ସିଂହଦେଓ")]
    assert pii.detect(text)[0].confidence == 0.8


@pytest.mark.parametrize("text", ["ରାମ ସୀତା ଘରକୁ ଯାଏ ।", "ବୈଦ୍ୟନାଥ", "ବୈଦ୍ୟନାଥ ଆସିଲେ", "ସିଂହଦେଓ ଆସିଲେ", "ଶ୍ରୀ ଆସିଲେ"])
def test_a_single_name_or_a_name_without_a_dictionary_partner_is_ignored(text: str) -> None:
    assert kinds(text) == []


def test_address_joins_an_admin_word_and_a_nearby_pin() -> None:
    text = "ଗ୍ରାମ ରାମପୁର PIN 751001 ରେ"
    [entity] = pii.detect(text)
    assert entity.type == "ADDRESS"
    assert entity.text == "ଗ୍ରାମ ରାମପୁର PIN 751001"
    assert entity.confidence == 0.45
    odia = "ଜିଲ୍ଲା ଖୋର୍ଦ୍ଧା ୭୫୧୦୦୩"
    assert kinds(odia) == [("ADDRESS", odia)]


def test_address_accepts_a_pin_glued_to_the_admin_word() -> None:
    assert kinds("ସହର751001") == [("ADDRESS", "ସହର751001")]


@pytest.mark.parametrize(
    "text",
    [
        "ଗ୍ରାମ ରାମପୁର",
        "751001",
        "ଜିଲ୍ଲାରେ 751001 ଲୋକ",
        "ଗ୍ରାମ " + ("ଅ" * 41) + " 751001",
    ],
)
def test_address_requires_a_whole_admin_word_within_40_characters_of_a_pin(text: str) -> None:
    assert kinds(text, types=["ADDRESS"]) == []


def test_min_confidence_drops_the_address_and_keeps_a_marked_pin() -> None:
    text = "ଗ୍ରାମ ରାମପୁର PIN 751001"
    assert [entity.type for entity in pii.detect(text, min_confidence=0.5)] == ["PINCODE"]


def test_requesting_only_pincode_still_finds_the_pin_inside_an_address() -> None:
    assert kinds("ଗ୍ରାମ ରାମପୁର PIN 751001", types=["PINCODE"]) == [("PINCODE", "751001")]


def test_every_entity_type_is_detectable_and_mask_is_idempotent() -> None:
    text = (
        "PIN 751002 ଶ୍ରୀ ବୈଦ୍ୟନାଥ ସିଂହଦେଓ ଫୋନ 9876543210 ମେଲ a@b.com "
        "ଆଧାର 234567890124 PAN ABCPE1234F ଜନ୍ମ 15 January 2024 ଦାମ ₹500 "
        "ଗ୍ରାମ ରାମପୁର PIN 751001 https://x.com"
    )
    found = {entity.type for entity in pii.detect(text)}
    assert found == set(pii.PII_TYPES)
    once = pii.mask(text)
    assert once == (
        "PIN <PINCODE> <NAME> ଫୋନ <PHONE> ମେଲ <EMAIL> ଆଧାର <AADHAAR> PAN <PAN> ଜନ୍ମ <DATE> ଦାମ <MONEY> <ADDRESS> <URL>"
    )
    assert pii.mask(once) == once
    assert "9876543210" not in once
    assert "a@b.com" not in once
    assert "ବୈଦ୍ୟନାଥ" not in once


def test_pseudonymize_round_trips_through_the_store_and_is_stable() -> None:
    store = KeyStore()
    text = "ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ଓ a@b.com ଓ ପୁଣି ୯୮୭୬୫୪୩୨୧୦"
    hidden = pii.pseudonymize(text, store)
    assert hidden == "ଫୋନ <PHONE:1> ଓ <EMAIL:1> ଓ ପୁଣି <PHONE:1>"
    assert "୯୮୭୬୫୪୩୨୧୦" not in hidden
    assert pii.restore(hidden, store) == text
    assert pii.pseudonymize(hidden, store) == hidden
    assert pii.mask(hidden) == hidden


def test_pseudonymize_round_trips_when_a_later_span_swallows_an_earlier_token() -> None:
    text = "ଗ୍ରାମ " + "a" * 45 + "@example.com 751001"
    store = KeyStore()
    hidden = pii.pseudonymize(text, store)
    assert "a" * 45 not in hidden
    assert "@example.com" not in hidden
    assert pii.restore(hidden, store) == text


def test_pseudonymize_of_glued_values_round_trips() -> None:
    store = KeyStore()
    text = "ABCPE1234Fhttps://x.com"
    hidden = pii.pseudonymize(text, store)
    assert hidden == "<PAN:1><URL:1>"
    assert pii.restore(hidden, store) == text


def test_the_same_store_reuses_a_token_for_the_same_value() -> None:
    store = KeyStore()
    assert pii.pseudonymize("call 9876543210", store) == "call <PHONE:1>"
    assert pii.pseudonymize("again 9123456780", store) == "again <PHONE:2>"
    assert pii.pseudonymize("back 9876543210", store) == "back <PHONE:1>"


def test_restore_follows_a_chain_as_long_as_the_pass_limit() -> None:
    store = KeyStore()
    store.token_for(PIIEntity("PHONE", "core", 0, 4, 0.9))
    for number in range(1, 10):
        store.token_for(PIIEntity("PHONE", f"<PHONE:{number}>", 0, 10, 0.9))
    assert pii.restore("<PHONE:10>", store) == "core"


def test_restore_leaves_a_token_the_store_does_not_know() -> None:
    store = KeyStore()
    pii.pseudonymize("9876543210", store)
    assert pii.restore("see <PHONE:9> please", store) == "see <PHONE:9> please"


@pytest.mark.parametrize("value", [None, b"secret-9876543210", 98765])
def test_pseudonymize_and_restore_reject_a_non_str_without_echoing_it(value: object) -> None:
    store = KeyStore()
    for call in (pii.pseudonymize, pii.restore):
        with pytest.raises(TypeError, match=r"text must be str, got \w+") as error:
            call(value, store)
        assert "secret" not in str(error.value)
        assert "9876543210" not in str(error.value)


def test_restore_requires_a_key_store() -> None:
    with pytest.raises(TypeError, match="store must be KeyStore") as error:
        pii.restore("secret <PHONE:1>", "nope")
    assert "secret" not in str(error.value)


def test_pseudonymize_requires_a_key_store() -> None:
    with pytest.raises(TypeError, match="store must be KeyStore") as error:
        pii.pseudonymize("secret 9876543210", "nope")
    assert "secret" not in str(error.value)
    assert "9876543210" not in str(error.value)


def test_pii_is_exported_once_from_the_package_root() -> None:
    import openodia

    assert openodia.pii is pii
    assert openodia.__all__.count("pii") == 1


def test_a_long_run_of_combining_marks_is_mapped_in_linear_time() -> None:
    def elapsed(count: int) -> float:
        text = "a" + "\u0323" * count + "a@b.com"
        started = time.perf_counter()
        entities = pii.detect(text)
        spent = time.perf_counter() - started
        assert [(entity.type, text[entity.start : entity.end]) for entity in entities] == [("EMAIL", "a@b.com")]
        return spent

    small = min(elapsed(4000) for _ in range(3))
    large = min(elapsed(16000) for _ in range(3))
    assert large < small * 8


NEW_PII_RELEASE = (
    "Dates, amounts, names, addresses, `pseudonymize`, `restore` and `KeyStore` need a release newer than 0.2.0: "
    "`from openodia.pii import pseudonymize` fails on 0.2.0, and `pii.detect` there finds only phone, email, URL, "
    "Aadhaar, PAN and PIN code."
)


@pytest.mark.parametrize(
    "doc",
    [
        "README.md",
        "AGENTS.md",
        "skills/openodia/SKILL.md",
        "docs/index.md",
        "docs/guides/pii.md",
        "docs/llms.txt",
        "docs/application.md",
        "CHANGELOG.md",
    ],
)
def test_docs_name_the_release_that_adds_the_new_pii_types(doc: str) -> None:
    root = Path(__file__).resolve().parents[1]
    text = " ".join((root / doc).read_text(encoding="utf-8").split())
    assert NEW_PII_RELEASE in text


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("paid ₹500.", "paid <MONEY>."),
        ("paid Rs. 1,500, thanks", "paid <MONEY>, thanks"),
        ("paid ₹500.50.", "paid <MONEY>."),
        ("₹1,5 x", "₹1,5 x"),
        ("₹1,50000 x", "₹1,50000 x"),
    ],
)
def test_sentence_punctuation_ends_a_prefixed_amount(text: str, masked: str) -> None:
    assert pii.mask(text, types=["MONEY"]) == masked


def test_names_above_surname_confidence_skip_the_surname_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    scanned: list[int] = []
    real = _detect._surname_end

    def counting(text: str, words: list[re.Match[str]], index: int) -> int | None:
        scanned.append(index)
        return real(text, words, index)

    monkeypatch.setattr(_detect, "_surname_end", counting)
    text = " ".join(["ରାମ"] * 50)
    assert pii.detect(text, types=["NAME"], min_confidence=0.8) == []
    assert scanned == []
    assert pii.detect(text, types=["NAME"], min_confidence=0.7) != []
    assert scanned != []


@pytest.mark.parametrize("doc", ["AGENTS.md", "docs/index.md", "docs/guides/pii.md"])
def test_docs_state_the_name_whitespace_rule(doc: str) -> None:
    text = " ".join((Path(__file__).resolve().parents[1] / doc).read_text(encoding="utf-8").split())
    assert "Name words may be separated by any run of whitespace, including tabs, no-break spaces and line breaks." in text


@pytest.mark.parametrize("text", ["a@b.co\u0301", "foo@example.com\u0301", "ଗୋ\u0301 a@b.co\u0301"])
def test_an_ascii_email_before_a_combining_accent_is_masked(text: str) -> None:
    masked = pii.mask(text, types=["EMAIL"])
    assert "@" not in masked
    assert masked.endswith("<EMAIL>\u0301")
    for entity in pii.detect(text):
        assert text[entity.start : entity.end] == entity.text


def test_odia_digits_keep_numeric_boundaries_when_the_text_is_not_nfc() -> None:
    text = "a\u0301 ୧9876543210"
    assert pii.detect(text, types=["PHONE"]) == []
    assert pii.mask(text, types=["PHONE"]) == text
    phone = "a\u0301 9876543210"
    masked = pii.mask(phone, types=["PHONE"])
    assert "9876543210" not in masked
    assert pii.detect(phone, types=["PHONE"])[0].text == "9876543210"
