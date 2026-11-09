import unicodedata

import pytest

from openodia import phonetic


class TestSoundex:
    def test_empty_input(self) -> None:
        assert phonetic.soundex("") == ""

    def test_vowel_only_keeps_first_letter(self) -> None:
        assert phonetic.soundex("ଆଇ") == "ଆ000"

    def test_first_consonant_kept_verbatim(self) -> None:
        out = phonetic.soundex("ସ")
        assert out.startswith("ସ")

    def test_padded_to_four_chars(self) -> None:
        out = phonetic.soundex("ସ")
        assert len(out) == 4
        assert out == "ସ000"

    def test_basic_word(self) -> None:
        out = phonetic.soundex("ସୋମେନ୍ଦ୍ର")
        assert out == "ସ657"

    def test_nukta_forms_are_equivalent(self) -> None:
        precomposed = "\u0b5c\u0b3e\u0b15"
        decomposed = "\u0b21\u0b3c\u0b3e\u0b15"
        assert phonetic.soundex(precomposed) == phonetic.soundex(decomposed)
        assert phonetic.similarity(precomposed, decomposed) == 1.0

    def test_nukta_letter_differs_from_plain_letter(self) -> None:
        assert phonetic.soundex("\u0b5c\u0b3e\u0b15") != phonetic.soundex("\u0b21\u0b3e\u0b15")

    def test_zero_width_joiners_do_not_break_conjuncts(self) -> None:
        plain = "ସୋମେନ୍ଦ୍ର"
        for joiner in ("\u200d", "\u200c"):
            assert phonetic.soundex(plain.replace("ନ୍", "ନ୍" + joiner)) == "ସ657"

    def test_truncates_to_four_chars(self) -> None:
        assert len(phonetic.soundex("ଚକ୍ରପାଣିଗ୍ରାହୀ")) == 4

    def test_adjacent_duplicates_collapse(self) -> None:
        out = phonetic.soundex("ଗଗଗ")
        assert out == "ଗ000"

    def test_spelling_variants_match(self) -> None:
        assert phonetic.soundex("ସୋମେନ୍ଦ୍ର") == phonetic.soundex("ସୌମେନ୍ଦ୍ର")

    def test_aspirated_unaspirated_share_digit_code(self) -> None:
        """Standard Soundex keeps the first letter literal — but
        aspirated/unaspirated pairs in *body* positions collapse to one
        digit. So same first consonant + ``ଗ`` vs ``ଘ`` mid-word should match.
        """
        assert phonetic.soundex("ସଗର") == phonetic.soundex("ସଘର")


class TestMetaphone:
    def test_empty_input(self) -> None:
        assert phonetic.metaphone("") == ""

    def test_no_consonant(self) -> None:
        assert phonetic.metaphone("ଆଇ") == ""

    def test_first_consonant(self) -> None:
        assert phonetic.metaphone("ଖ") == "କ"

    def test_aspirated_collapses(self) -> None:
        assert phonetic.metaphone("ଖ") == phonetic.metaphone("କ")

    def test_adjacent_duplicates_collapse(self) -> None:
        assert phonetic.metaphone("ପଫବ") == "ପ"

    def test_basic_word(self) -> None:
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == "ସପତର"

    def test_spelling_variants_match(self) -> None:
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == phonetic.metaphone("ସୌମେନ୍ଦ୍ର")


class TestSimilarity:
    def test_identical_inputs(self) -> None:
        assert phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୋମେନ୍ଦ୍ର") == 1.0

    def test_spelling_variants_high(self) -> None:
        score = phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର")
        assert score == 1.0

    def test_completely_different(self) -> None:
        score = phonetic.similarity("ସୀତା", "ବିଜୟ")
        assert 0.0 <= score < 0.5

    def test_symmetric(self) -> None:
        a, b = "ସୋମେନ୍ଦ୍ର", "ସୁମନ"
        assert phonetic.similarity(a, b) == phonetic.similarity(b, a)

    def test_in_unit_interval(self) -> None:
        for a, b in [("ସୋମ", "ସୌମ"), ("ର", "କ"), ("ସୀତା", "ରାମ")]:
            score = phonetic.similarity(a, b)
            assert 0.0 <= score <= 1.0

    def test_empty_pair(self) -> None:
        assert phonetic.similarity("", "") == 0.0
        assert phonetic.similarity("ଆ", "") == 0.5


class TestNonOdiaInputs:
    @pytest.mark.parametrize("word", ["hello", "123", "ା", "   ", "हिन्दी"])
    @pytest.mark.parametrize("encoder", [phonetic.soundex, phonetic.metaphone])
    def test_no_odia_letters_raises(self, word, encoder) -> None:
        with pytest.raises(ValueError, match="Odia letter"):
            encoder(word)

    @pytest.mark.parametrize(
        "words",
        [
            ("hello", "ସ"),
            ("ସ", "hello"),
            ("hello", "hello"),
            (None, "ସ"),
            ("ସ", None),
            (None, None),
            ("   ", "ସ"),
            ("ସ", "\t\n"),
            ("   ", "   "),
        ],
    )
    def test_similarity_returns_zero_for_none_latin_or_whitespace(self, words) -> None:
        assert phonetic.similarity(*words) == 0.0

    def test_non_odia_resets_duplicate_suppression_like_vowels(self) -> None:
        assert phonetic.metaphone("ପxପ") == phonetic.metaphone("ପାପ") == "ପପ"
        assert phonetic.soundex("ପxପ") == phonetic.soundex("ପାପ") == "ପ600"

    def test_mixed_input(self) -> None:
        assert phonetic.soundex("ସୋ hello") == "ସ000"
        assert phonetic.metaphone("ସୋ hello") == "ସ"


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.phonetic is phonetic
        assert callable(openodia.phonetic.soundex)
        assert callable(openodia.phonetic.metaphone)
        assert callable(openodia.phonetic.similarity)


class TestLevenshteinHelper:
    """The Wagner-Fischer routine — exercise its branches."""

    def test_identical(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("abc", "abc") == 0

    def test_one_empty(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("", "abc") == 3
        assert _levenshtein("abc", "") == 3

    def test_both_empty(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("", "") == 0

    def test_single_substitution(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("abc", "axc") == 1


class TestNormalisedEditSimilarity:
    def test_both_empty_is_one(self) -> None:
        from openodia.phonetic._phonetic import _normalised_edit_similarity

        assert _normalised_edit_similarity("", "") == 1.0

    def test_one_empty_is_zero(self) -> None:
        from openodia.phonetic._phonetic import _normalised_edit_similarity

        assert _normalised_edit_similarity("abc", "") == 0.0
        assert _normalised_edit_similarity("", "abc") == 0.0


class TestReviewRegressions:
    def test_four_character_truncation(self) -> None:
        assert phonetic.soundex("କଚଟତପରସ") == "କ345"
        assert phonetic.soundex("କଚଟତ") == "କ345"

    @pytest.mark.parametrize("word", ["ପାପା", "ପଅପ"])
    def test_vowels_reset_merge_chain(self, word) -> None:
        assert phonetic.soundex(word) == "ପ600"
        assert phonetic.metaphone(word) == "ପପ"

    def test_leading_vowel_is_preserved(self) -> None:
        assert phonetic.soundex("ଅମର") == "ଅ670"
        assert phonetic.soundex("ମର") == "ମ700"
        assert phonetic.similarity("ଅମର", "ମର") == 0.5

    @pytest.mark.parametrize("letter,digit,base", [("ୱ", "7", "ର"), ("ୟ", "7", "ର"), ("ହ", "8", "ସ"), ("ଡ଼", "4", "ଟ")])
    def test_table_entries(self, letter, digit, base) -> None:
        assert phonetic.soundex("କ" + letter) == "କ" + digit + "00"
        assert phonetic.metaphone(letter) == base

    @pytest.mark.parametrize("encoder", [phonetic.soundex, phonetic.metaphone])
    def test_nfc_normalisation(self, encoder) -> None:
        word = "କୋପୌଡ଼"
        decomposed = unicodedata.normalize("NFD", word)
        assert decomposed != word
        assert encoder(word) == encoder(decomposed)

    def test_similarity_equal_weights(self) -> None:
        assert phonetic.similarity("କ", "ଖ") == 0.5
        assert phonetic.soundex("କଚଟତପ") == phonetic.soundex("କଚଟତର")
        assert phonetic.similarity("କଚଟତପ", "କଚଟତର") == pytest.approx(0.9)

    @pytest.mark.parametrize("word", ["ପ୍ପ", "ପ୍\u200dପ", "ପ୍\u200cପ"])
    def test_conjunct_marks_preserve_merge_chain(self, word) -> None:
        assert phonetic.soundex(word) == "ପ000"
        assert phonetic.metaphone(word) == "ପ"

    def test_nukta_between_identical_consonants_does_not_split_them(self) -> None:
        assert phonetic.soundex("କ\u0b3cକ") == "କ000"
        assert phonetic.metaphone("କ\u0b3cକ") == "କ"
        assert phonetic.similarity("କ\u0b3cକ", "କ") == 1.0


class TestTypesAndEmptyInput:
    @pytest.mark.parametrize("bad", [1, b"\xe0\xac\x95", ["କ"], 1.5])
    def test_similarity_rejects_non_str(self, bad) -> None:
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity(bad, "କ")
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity("କ", bad)
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity(None, bad)

    @pytest.mark.parametrize("encoder", [phonetic.soundex, phonetic.metaphone])
    @pytest.mark.parametrize("bad", [None, 0, b"", []])
    def test_encoders_reject_non_str(self, encoder, bad) -> None:
        with pytest.raises(TypeError, match="expected str"):
            encoder(bad)

    def test_empty_input(self) -> None:
        assert phonetic.soundex("") == ""
        assert phonetic.metaphone("") == ""
        assert phonetic.similarity("", "") == 0.0
        assert phonetic.similarity("ଆ", "") == 0.5
        assert phonetic.similarity("", "କ") == 0.0


class TestNfcAndTable:
    def test_decomposed_input_that_nfc_changes(self) -> None:
        import unicodedata

        decomposed = "କ\u0b47\u0b3eଶଲ"
        composed = unicodedata.normalize("NFC", decomposed)
        assert composed == "କ\u0b4bଶଲ" != decomposed
        assert phonetic.soundex(decomposed) == phonetic.soundex(composed) == "କ870"
        assert phonetic.metaphone(decomposed) == phonetic.metaphone(composed)
        assert phonetic.similarity(decomposed, composed) == 1.0

    def test_nukta_and_halant_mark_order_shares_a_key(self) -> None:
        halant_then_nukta = "ଢ\u0b4d\u0b3c"
        nukta_then_halant = "ଢ\u0b3c\u0b4d"
        assert phonetic.soundex(halant_then_nukta) == "\u0b5d000"
        assert phonetic.soundex(nukta_then_halant) == "\u0b5d000"
        assert phonetic.similarity(halant_then_nukta, nukta_then_halant) == 1.0

    def test_nya_mapping(self) -> None:
        assert phonetic.soundex("କଞ") == "କ300"
        assert phonetic.metaphone("ଞ") == "ଚ"
        assert phonetic.metaphone("ଚଞ") == "ଚ"


class TestAvagraha:
    @pytest.mark.parametrize("encoder", [phonetic.soundex, phonetic.metaphone])
    def test_avagraha_alone_raises(self, encoder) -> None:
        with pytest.raises(ValueError, match="Odia letter"):
            encoder("ଽ")

    def test_avagraha_is_not_the_first_letter(self) -> None:
        assert phonetic.soundex("ଽକ") == "କ000"
        assert phonetic.metaphone("ଽକ") == "କ"

    def test_avagraha_after_a_letter_resets_duplicate_suppression(self) -> None:
        assert phonetic.soundex("କଽଖ") == "କ200"
        assert phonetic.metaphone("କଽଖ") == "କକ"

    def test_avagraha_only_input_scores_zero(self) -> None:
        assert phonetic.similarity("ଽ", "ସ") == 0.0


SAME_NAME_SPELLINGS = {
    "o-au": (
        ("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର"),
        ("ସୋମନାଥ", "ସୌମନାଥ"),
        ("ଅଶୋକ", "ଅଶୌକ"),
        ("ବିନୋଦ", "ବିନୌଦ"),
        ("ଗୋପାଳ", "ଗୌପାଳ"),
        ("ମୋହନ", "ମୌହନ"),
        ("ଲୋକନାଥ", "ଲୌକନାଥ"),
        ("ପ୍ରମୋଦ", "ପ୍ରମୌଦ"),
        ("ସନ୍ତୋଷ", "ସନ୍ତୌଷ"),
        ("ଜୋଗେନ୍ଦ୍ର", "ଜୌଗେନ୍ଦ୍ର"),
    ),
    "i-ii": (
        ("ଦିପକ", "ଦୀପକ"),
        ("ସିତା", "ସୀତା"),
        ("ଗିତା", "ଗୀତା"),
        ("ଲକ୍ଷ୍ମି", "ଲକ୍ଷ୍ମୀ"),
        ("ସୁନିତା", "ସୁନୀତା"),
        ("କବିତା", "କବୀତା"),
        ("କିରଣ", "କୀରଣ"),
        ("ନିଳମଣି", "ନୀଳମଣି"),
        ("ମିନତି", "ମୀନତି"),
        ("ପ୍ରଦୀପ", "ପ୍ରଦିପ"),
    ),
    "u-uu": (
        ("ସୁରେନ୍ଦ୍ର", "ସୂରେନ୍ଦ୍ର"),
        ("ସୁଶାନ୍ତ", "ସୂଶାନ୍ତ"),
        ("ପୁରୁଷୋତ୍ତମ", "ପୂରୁଷୋତ୍ତମ"),
        ("ସୁଭଦ୍ରା", "ସୂଭଦ୍ରା"),
        ("ମଧୁ", "ମଧୂ"),
        ("ରଘୁ", "ରଘୂ"),
        ("ସୁକାନ୍ତ", "ସୂକାନ୍ତ"),
        ("କୁମାର", "କୂମାର"),
    ),
    "e-ai": (
        ("ବୈଷ୍ଣବ", "ବେଷ୍ଣବ"),
        ("ବୈଦ୍ୟନାଥ", "ବେଦ୍ୟନାଥ"),
        ("ଦୈତାରି", "ଦେତାରି"),
        ("ବୈଦେହୀ", "ବେଦେହୀ"),
    ),
    "final-aa": (
        ("ବିଜୟ", "ବିଜୟା"),
        ("ସଞ୍ଜୟ", "ସଞ୍ଜୟା"),
        ("ଅଜୟ", "ଅଜୟା"),
        ("ରାମ", "ରାମା"),
    ),
    "ya": (
        ("ସତ୍ୟ", "ସତ୍ଯ"),
        ("ସତ୍ୟଜିତ", "ସତ୍ଯଜିତ"),
        ("ଆଦିତ୍ୟ", "ଆଦିତ୍ଯ"),
        ("ନିତ୍ୟାନନ୍ଦ", "ନିତ୍ଯାନନ୍ଦ"),
    ),
    "aspiration": (
        ("ମୁକେଶ", "ମୁଖେଶ"),
        ("ରାକେଶ", "ରାଖେଶ"),
        ("ଅକିଳ", "ଅଖିଳ"),
        ("ଶେକର", "ଶେଖର"),
        ("ସୁଭାଷ", "ସୁବାଷ"),
        ("ସୁଧାକର", "ସୁଦାକର"),
    ),
    "sibilant": (
        ("ମହେଶ", "ମହେସ"),
        ("ରମେଶ", "ରମେସ"),
    ),
    "anusvara": (
        ("ସଂଜୟ", "ସଞ୍ଜୟ"),
        ("ସଂକର", "ସଙ୍କର"),
    ),
}


class TestSameNameSpellings:
    def test_fifty_pairs_share_soundex_key(self) -> None:
        pairs = [pair for group in SAME_NAME_SPELLINGS.values() for pair in group]
        assert len(SAME_NAME_SPELLINGS) >= 5
        assert len(pairs) == 50
        assert len(set(pairs)) == 50
        assert all(left != right for left, right in pairs)
        matched = sum(phonetic.soundex(left) == phonetic.soundex(right) for left, right in pairs)
        assert matched / len(pairs) >= 0.9
