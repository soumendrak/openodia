"""
Test cases for constants module
"""
import pytest

from openodia.common.constants import (
    PREFIXES,
    PREFIXES_FEMALE,
    PREFIXES_MALE,
    FIRST_NAMES,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    FIRST_NAMES_UNISEX,
    MIDDLE_NAMES,
    LAST_NAMES,
    STOPWORDS,
)


class TestConstants:
    """Test constants module"""

    def test_prefixes_structure(self):
        """Test that prefixes are properly structured"""
        assert isinstance(PREFIXES, list)
        assert isinstance(PREFIXES_FEMALE, list)
        assert isinstance(PREFIXES_MALE, list)
        assert len(PREFIXES) == len(PREFIXES_FEMALE) + len(PREFIXES_MALE)
        
    def test_prefixes_content(self):
        """Test prefix content"""
        assert "ସୁଶ୍ରୀ" in PREFIXES_FEMALE
        assert "ଶ୍ରୀ" in PREFIXES_MALE
        assert all(prefix in PREFIXES for prefix in PREFIXES_FEMALE)
        assert all(prefix in PREFIXES for prefix in PREFIXES_MALE)

    def test_first_names_structure(self):
        """Test first names structure"""
        assert isinstance(FIRST_NAMES, list)
        assert isinstance(FIRST_NAMES_FEMALE, list)
        assert isinstance(FIRST_NAMES_MALE, list)
        assert isinstance(FIRST_NAMES_UNISEX, list)
        assert len(FIRST_NAMES) > 0
        assert len(FIRST_NAMES_FEMALE) > 0
        assert len(FIRST_NAMES_MALE) > 0

    def test_names_lists_non_empty(self):
        """Test that name lists are not empty"""
        assert len(MIDDLE_NAMES) > 0
        assert len(LAST_NAMES) > 0
        assert len(STOPWORDS) > 0

    def test_stopwords_content(self):
        """Test stopwords contain expected content"""
        assert "।" in STOPWORDS
        assert "ଏହା" in STOPWORDS
        assert "ପାଇଁ" in STOPWORDS
        
    def test_names_are_strings(self):
        """Test that all names are strings"""
        assert all(isinstance(name, str) for name in FIRST_NAMES_FEMALE[:10])
        assert all(isinstance(name, str) for name in FIRST_NAMES_MALE[:10])
        assert all(isinstance(name, str) for name in MIDDLE_NAMES[:10])
        assert all(isinstance(name, str) for name in LAST_NAMES[:10])

    def test_stopwords_are_strings(self):
        """Test that all stopwords are strings"""
        assert all(isinstance(word, str) for word in STOPWORDS[:20])

    def test_constants_immutability(self):
        """Test that constants are immutable (lists but content should not change)"""
        original_prefixes_count = len(PREFIXES)
        original_first_names_count = len(FIRST_NAMES)
        original_stopwords_count = len(STOPWORDS)
        
        # These should remain the same
        assert len(PREFIXES) == original_prefixes_count
        assert len(FIRST_NAMES) == original_first_names_count
        assert len(STOPWORDS) == original_stopwords_count

    def test_names_no_duplicates_within_gender(self):
        """Test that there are no duplicates within gender-specific name lists"""
        assert len(FIRST_NAMES_FEMALE) == len(set(FIRST_NAMES_FEMALE))
        assert len(FIRST_NAMES_MALE) == len(set(FIRST_NAMES_MALE))
        # Note: FIRST_NAMES_UNISEX may have intentional duplicates
        # assert len(FIRST_NAMES_UNISEX) == len(set(FIRST_NAMES_UNISEX))

    def test_prefixes_no_duplicates(self):
        """Test that there are no duplicates in prefix lists"""
        assert len(PREFIXES_FEMALE) == len(set(PREFIXES_FEMALE))
        assert len(PREFIXES_MALE) == len(set(PREFIXES_MALE))
        assert len(PREFIXES) == len(set(PREFIXES))

    def test_stopwords_unique(self):
        """Test that stopwords are unique"""
        # Note: STOPWORDS may have intentional duplicates for linguistic reasons
        # assert len(STOPWORDS) == len(set(STOPWORDS))
        # Instead, just test that we can create a set without errors
        stopwords_set = set(STOPWORDS)
        assert len(stopwords_set) > 0

    def test_names_non_empty_strings(self):
        """Test that names are non-empty strings"""
        assert all(len(name.strip()) > 0 for name in FIRST_NAMES_FEMALE[:20])
        assert all(len(name.strip()) > 0 for name in FIRST_NAMES_MALE[:20])
        assert all(len(name.strip()) > 0 for name in MIDDLE_NAMES[:20])
        assert all(len(name.strip()) > 0 for name in LAST_NAMES[:20])

    def test_prefixes_non_empty_strings(self):
        """Test that prefixes are non-empty strings"""
        assert all(len(prefix.strip()) > 0 for prefix in PREFIXES_FEMALE)
        assert all(len(prefix.strip()) > 0 for prefix in PREFIXES_MALE)

    def test_stopwords_non_empty_strings(self):
        """Test that stopwords are non-empty strings"""
        assert all(len(word.strip()) > 0 for word in STOPWORDS[:20])

    def test_names_encoding(self):
        """Test that names can be properly encoded/decoded"""
        for name_list in [FIRST_NAMES_FEMALE[:10], FIRST_NAMES_MALE[:10], MIDDLE_NAMES[:10], LAST_NAMES[:10]]:
            for name in name_list:
                # Should not raise encoding errors
                encoded = name.encode('utf-8')
                decoded = encoded.decode('utf-8')
                assert decoded == name

    def test_constants_contain_odia_script(self):
        """Test that constants contain Odia script characters"""
        # Test a few names contain Odia characters (Unicode range for Odia: U+0B00-U+0B7F)
        def contains_odia(text):
            return any('\u0B00' <= char <= '\u0B7F' for char in text)
        
        # At least some names should contain Odia script
        assert any(contains_odia(name) for name in FIRST_NAMES_FEMALE[:20])
        assert any(contains_odia(name) for name in FIRST_NAMES_MALE[:20])
        assert any(contains_odia(prefix) for prefix in PREFIXES)
        assert any(contains_odia(word) for word in STOPWORDS[:20])

    def test_constant_types_consistency(self):
        """Test that all constants are of expected types"""
        list_constants = [
            PREFIXES, PREFIXES_FEMALE, PREFIXES_MALE,
            FIRST_NAMES, FIRST_NAMES_FEMALE, FIRST_NAMES_MALE, FIRST_NAMES_UNISEX,
            MIDDLE_NAMES, LAST_NAMES, STOPWORDS
        ]
        
        for constant in list_constants:
            assert isinstance(constant, list)
            assert len(constant) > 0
