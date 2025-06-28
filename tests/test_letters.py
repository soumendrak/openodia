import pytest

from openodia import alphabet


class TestLetters:
    # -*- coding: utf-8 -*-
    ALL_CHAR_MAP = {
        "ଁ": 2817,
        "ଂ": 2818,
        "ଃ": 2819,
        "ଅ": 2821,
        "ଆ": 2822,
        "ଇ": 2823,
        "ଈ": 2824,
        "ଉ": 2825,
        "ଊ": 2826,
        "ଋ": 2827,
        "ଌ": 2828,
        "ଏ": 2831,
        "ଐ": 2832,
        "ଓ": 2835,
        "ଔ": 2836,
        "କ": 2837,
        "ଖ": 2838,
        "ଗ": 2839,
        "ଘ": 2840,
        "ଙ": 2841,
        "ଚ": 2842,
        "ଛ": 2843,
        "ଜ": 2844,
        "ଝ": 2845,
        "ଞ": 2846,
        "ଟ": 2847,
        "ଠ": 2848,
        "ଡ": 2849,
        "ଢ": 2850,
        "ଣ": 2851,
        "ତ": 2852,
        "ଥ": 2853,
        "ଦ": 2854,
        "ଧ": 2855,
        "ନ": 2856,
        "ପ": 2858,
        "ଫ": 2859,
        "ବ": 2860,
        "ଭ": 2861,
        "ମ": 2862,
        "ଯ": 2863,
        "ର": 2864,
        "ଲ": 2866,
        "ଳ": 2867,
        "ଵ": 2869,
        "ଶ": 2870,
        "ଷ": 2871,
        "ସ": 2872,
        "ହ": 2873,
        "଼": 2876,
        "ଽ": 2877,
        "ା": 2878,
        "ି": 2879,
        "ୀ": 2880,
        "ୁ": 2881,
        "ୂ": 2882,
        "ୃ": 2883,
        "ୄ": 2884,
        "େ": 2887,
        "ୈ": 2888,
        "ୋ": 2891,
        "ୌ": 2892,
        "୍": 2893,
        "ୖ": 2902,
        "ୗ": 2903,
        "ଡ଼": 2908,
        "ଢ଼": 2909,
        "ୟ": 2911,
        "ୠ": 2912,
        "ୡ": 2913,
        "ୢ": 2914,
        "ୣ": 2915,
        "୦": 2918,
        "୧": 2919,
        "୨": 2920,
        "୩": 2921,
        "୪": 2922,
        "୫": 2923,
        "୬": 2924,
        "୭": 2925,
        "୮": 2926,
        "୯": 2927,
        "୰": 2928,
        "ୱ": 2929,
        "୲": 2930,
    }

    VOWEL_MAP = {
        "ଅ": 2821,
        "ଆ": 2822,
        "ଇ": 2823,
        "ଈ": 2824,
        "ଉ": 2825,
        "ଊ": 2826,
        "ଋ": 2827,
        "ଌ": 2828,
        "ଏ": 2831,
        "ଐ": 2832,
        "ଓ": 2835,
        "ଔ": 2836,
    }

    NUMBER_MAP = {
        "୦": 2918,
        "୧": 2919,
        "୨": 2920,
        "୩": 2921,
        "୪": 2922,
        "୫": 2923,
        "୬": 2924,
        "୭": 2925,
        "୮": 2926,
        "୯": 2927,
    }

    CONSONANT_MAP = {
        "କ": 2837,
        "ଖ": 2838,
        "ଗ": 2839,
        "ଘ": 2840,
        "ଙ": 2841,
        "ଚ": 2842,
        "ଛ": 2843,
        "ଜ": 2844,
        "ଝ": 2845,
        "ଞ": 2846,
        "ଟ": 2847,
        "ଠ": 2848,
        "ଡ": 2849,
        "ଢ": 2850,
        "ଣ": 2851,
        "ତ": 2852,
        "ଥ": 2853,
        "ଦ": 2854,
        "ଧ": 2855,
        "ନ": 2856,
        "ପ": 2858,
        "ଫ": 2859,
        "ବ": 2860,
        "ଭ": 2861,
        "ମ": 2862,
        "ଯ": 2863,
        "ର": 2864,
        "ଲ": 2866,
        "ଳ": 2867,
        "ଵ": 2869,
        "ଶ": 2870,
        "ଷ": 2871,
        "ସ": 2872,
        "ହ": 2873,
    }

    MATRA = {
        "ଁ",
        "ଂ",
        "ଃ",
        "଼",
        "ଽ",
        "ା",
        "ି",
        "ୀ",
        "ୁ",
        "ୂ",
        "ୃ",
        "ୄ",
        "େ",
        "ୈ",
        "ୋ",
        "ୌ",
        "୍",
        "ୖ",
        "ୗ",
        "୰",
        "ୱ",
        "୲",
    }

    PUNCTUATION = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""

    def test_all_letters(self):
        assert len(alphabet.all_letters) == len(self.ALL_CHAR_MAP.keys())

    def test_vowels(self):
        assert len(alphabet.vowels) == len(self.VOWEL_MAP.keys())

    def test_numbers(self):
        assert len(alphabet.numbers) == len(self.NUMBER_MAP.keys())

    def test_consonants(self):
        assert len(alphabet.consonants) == len(self.CONSONANT_MAP.keys())

    def test_matra(self):
        assert len(alphabet.matras) == len(self.MATRA)

    def test_punctuation(self):
        assert len(alphabet.punctuations) == len(self.PUNCTUATION) + 1

    # Additional test cases
    def test_vowels_are_in_all_letters(self):
        """Test that all vowels are present in all_letters"""
        for vowel in alphabet.vowels:
            assert vowel in alphabet.all_letters

    def test_consonants_are_in_all_letters(self):
        """Test that all consonants are present in all_letters"""
        for consonant in alphabet.consonants:
            assert consonant in alphabet.all_letters

    def test_numbers_are_in_all_letters(self):
        """Test that all numbers are present in all_letters"""
        for number in alphabet.numbers:
            assert number in alphabet.all_letters

    def test_matras_are_in_all_letters(self):
        """Test that all matras are present in all_letters"""
        for matra in alphabet.matras:
            assert matra in alphabet.all_letters

    def test_no_duplicates_in_all_letters(self):
        """Test that all_letters has no duplicates"""
        assert len(alphabet.all_letters) == len(set(alphabet.all_letters))

    def test_no_duplicates_in_vowels(self):
        """Test that vowels has no duplicates"""
        assert len(alphabet.vowels) == len(set(alphabet.vowels))

    def test_no_duplicates_in_consonants(self):
        """Test that consonants has no duplicates"""
        assert len(alphabet.consonants) == len(set(alphabet.consonants))

    def test_no_duplicates_in_numbers(self):
        """Test that numbers has no duplicates"""
        assert len(alphabet.numbers) == len(set(alphabet.numbers))

    def test_no_duplicates_in_matras(self):
        """Test that matras has no duplicates"""
        assert len(alphabet.matras) == len(set(alphabet.matras))

    def test_vowels_consonants_no_overlap(self):
        """Test that vowels and consonants don't overlap"""
        vowel_set = set(alphabet.vowels)
        consonant_set = set(alphabet.consonants)
        assert len(vowel_set.intersection(consonant_set)) == 0

    def test_unicode_ranges(self):
        """Test that Odia letters are in correct Unicode range"""
        for letter in alphabet.all_letters:
            # Odia Unicode range is roughly 2816-2943
            unicode_val = ord(letter[0])  # Get first character's Unicode
            assert 2800 <= unicode_val <= 3000, f"Letter {letter} (Unicode: {unicode_val}) outside expected range"

    def test_specific_vowels_present(self):
        """Test that specific important vowels are present"""
        important_vowels = ["ଅ", "ଆ", "ଇ", "ଈ", "ଉ", "ଊ", "ଏ", "ଓ"]
        for vowel in important_vowels:
            assert vowel in alphabet.vowels

    def test_specific_consonants_present(self):
        """Test that specific important consonants are present"""
        important_consonants = ["କ", "ଖ", "ଗ", "ଘ", "ଙ", "ଚ", "ଛ", "ଜ", "ଝ", "ଞ"]
        for consonant in important_consonants:
            assert consonant in alphabet.consonants

    def test_odia_numbers_sequence(self):
        """Test that Odia numbers are in sequence"""
        expected_numbers = ["୦", "୧", "୨", "୩", "୪", "୫", "୬", "୭", "୮", "୯"]
        assert alphabet.numbers == expected_numbers

    def test_punctuations_type(self):
        """Test that punctuations is a tuple"""
        assert isinstance(alphabet.punctuations, tuple)

    def test_lists_are_lists(self):
        """Test that letter collections are lists"""
        assert isinstance(alphabet.all_letters, list)
        assert isinstance(alphabet.vowels, list)
        assert isinstance(alphabet.consonants, list)
        assert isinstance(alphabet.numbers, list)
        assert isinstance(alphabet.matras, list)
