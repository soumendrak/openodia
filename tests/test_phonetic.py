import unicodedata

import pytest

from openodia import phonetic


class TestSoundex:
    def test_empty_input(self) -> None:
        assert phonetic.soundex("") == ""

    def test_vowel_only_keeps_first_letter(self) -> None:
        # Only vowels and matras.
        assert phonetic.soundex("ଆଇ") == "ଆ000"

    def test_first_consonant_kept_verbatim(self) -> None:
        out = phonetic.soundex("ସ")
        assert out.startswith("ସ")

    def test_padded_to_four_chars(self) -> None:
        out = phonetic.soundex("ସ")
        assert len(out) == 4
        assert out == "ସ000"

    def test_basic_word(self) -> None:
        # ସୋମେନ୍ଦ୍ର → ସ (verbatim) + ମ(6) + ନ(5) + ଦ(5)→same as ନ, skipped → ର(7)
        # → "ସ657"
        out = phonetic.soundex("ସୋମେନ୍ଦ୍ର")
        assert out == "ସ657"

    def test_nukta_forms_are_equivalent(self) -> None:
        precomposed = "\u0b5c\u0b3e\u0b15"  # ଡ଼ (U+0B5C) + ା + କ
        decomposed = "\u0b21\u0b3c\u0b3e\u0b15"  # ଡ + nukta + ା + କ
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
        # ଗଗଗ → all gutturals → 'ଗ' + (2 dropped as dup) + padding
        out = phonetic.soundex("ଗଗଗ")
        assert out == "ଗ000"

    def test_spelling_variants_match(self) -> None:
        # The difference between ସୋ vs ସୌ is just the vowel sign — Soundex
        # ignores vowels/matras, so the codes must match.
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
        # ଖ collapses to କ.
        assert phonetic.metaphone("ଖ") == "କ"

    def test_aspirated_collapses(self) -> None:
        # ଖ → କ; both should produce "କ"
        assert phonetic.metaphone("ଖ") == phonetic.metaphone("କ")

    def test_adjacent_duplicates_collapse(self) -> None:
        # Three labials in a row should yield a single ପ.
        assert phonetic.metaphone("ପଫବ") == "ପ"

    def test_basic_word(self) -> None:
        # ସୋମେନ୍ଦ୍ର — consonants ସ ମ ନ ଦ ର → bases ସ ପ ତ ତ ର
        # adjacent duplicates collapse: ସ ପ ତ ର
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == "ସପତର"

    def test_spelling_variants_match(self) -> None:
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == phonetic.metaphone("ସୌମେନ୍ଦ୍ର")


class TestSimilarity:
    def test_identical_inputs(self) -> None:
        assert phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୋମେନ୍ଦ୍ର") == 1.0

    def test_spelling_variants_high(self) -> None:
        # Different matras only — soundex equal AND metaphone equal.
        score = phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର")
        assert score == 1.0

    def test_completely_different(self) -> None:
        # Names from different articulation groups.
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
        # Two empty inputs score zero; a vowel-only input retains its
        # Soundex initial but has the same empty Metaphone as empty input.
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
        # x between two ପ-group consonants behaves like the vowel in ପାପ.
        assert phonetic.metaphone("ପxପ") == phonetic.metaphone("ପାପ") == "ପପ"
        assert phonetic.soundex("ପxପ") == phonetic.soundex("ପାପ") == "ପ600"

    def test_mixed_input(self) -> None:
        # Latin emits nothing; the Odia part is still encoded.
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
        # Different Soundex initials, identical Metaphone: half the score.
        assert phonetic.similarity("କ", "ଖ") == 0.5
        # Equal Soundex, Metaphone similarity 0.8: 0.5 + 0.5 * 0.8.
        assert phonetic.soundex("କଚଟତପ") == phonetic.soundex("କଚଟତର")
        assert phonetic.similarity("କଚଟତପ", "କଚଟତର") == pytest.approx(0.9)

    @pytest.mark.parametrize("word", ["ପ୍ପ", "ପ୍\u200dପ", "ପ୍\u200cପ"])
    def test_conjunct_marks_preserve_merge_chain(self, word) -> None:
        assert phonetic.soundex(word) == "ପ000"
        assert phonetic.metaphone(word) == "ପ"


class TestTypesAndEmptyInput:
    @pytest.mark.parametrize("bad", [1, b"\xe0\xac\x95", ["କ"], 1.5])
    def test_similarity_rejects_non_str(self, bad) -> None:
        # N1/N4: a non-str on either side must raise, not score 0.0.
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity(bad, "କ")
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity("କ", bad)
        with pytest.raises(TypeError, match="expected str"):
            phonetic.similarity(None, bad)

    @pytest.mark.parametrize("encoder", [phonetic.soundex, phonetic.metaphone])
    @pytest.mark.parametrize("bad", [None, 0, b"", []])
    def test_encoders_reject_non_str(self, encoder, bad) -> None:
        # N14: None (and other falsy non-str) must not return "".
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
        # P2: କ + େ + ା is the decomposed spelling of କୋ (U+0B4B); NFC
        # recomposes it, so both spellings give the same keys.
        import unicodedata

        decomposed = "କ\u0b47\u0b3eଶଲ"
        composed = unicodedata.normalize("NFC", decomposed)
        assert composed == "କ\u0b4bଶଲ" != decomposed
        assert phonetic.soundex(decomposed) == phonetic.soundex(composed) == "କ870"
        assert phonetic.metaphone(decomposed) == phonetic.metaphone(composed)
        assert phonetic.similarity(decomposed, composed) == 1.0

    def test_nya_mapping(self) -> None:
        # P21: ଞ is palatal: Soundex digit 3, Metaphone base ଚ.
        assert phonetic.soundex("କଞ") == "କ300"
        assert phonetic.metaphone("ଞ") == "ଚ"
        assert phonetic.metaphone("ଚଞ") == "ଚ"
