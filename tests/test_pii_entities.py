import time

import pytest

from openodia import numbers, pii
from openodia.pii import KeyStore

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


def test_a_dictionary_given_name_that_contains_a_space_is_detected() -> None:
    assert kinds("ଗୁନ୍ ଗୁନ୍ ସିଂହଦେଓ ଆସିଲେ") == [("NAME", "ଗୁନ୍ ଗୁନ୍ ସିଂହଦେଓ")]
    assert kinds("ଶ୍ରୀ ଗୁନ୍ ଗୁନ୍ ଆସିଲେ") == [("NAME", "ଶ୍ରୀ ଗୁନ୍ ଗୁନ୍")]


def test_a_dictionary_middle_name_stays_inside_the_name() -> None:
    assert kinds("ବୈଦ୍ୟନାଥ କିଶୋର ସିଂହଦେଓ ଆସିଲେ") == [("NAME", "ବୈଦ୍ୟନାଥ କିଶୋର ସିଂହଦେଓ")]


def test_an_honorific_plus_a_dictionary_name_is_a_name() -> None:
    text = "ଶ୍ରୀ ବୈଦ୍ୟନାଥ ସିଂହଦେଓ ଆସିଲେ"
    assert kinds(text) == [("NAME", "ଶ୍ରୀ ବୈଦ୍ୟନାଥ ସିଂହଦେଓ")]
    assert pii.detect(text)[0].confidence == 0.8


@pytest.mark.parametrize("text", ["ରାମ ସୀତା ଘରକୁ ଯାଏ ।", "ବୈଦ୍ୟନାଥ ଆସିଲେ", "ସିଂହଦେଓ ଆସିଲେ", "ଶ୍ରୀ ଆସିଲେ"])
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
