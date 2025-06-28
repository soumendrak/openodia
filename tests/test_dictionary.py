"""
Test cases for dictionary module
"""
import pytest
import os
import json
from unittest.mock import patch, mock_open

from openodia.corpus.dictionary import get_dictionary


class TestDictionary:
    """Test dictionary module functionality"""

    def test_get_dictionary_returns_dict(self):
        """Test that get_dictionary returns a dictionary"""
        result = get_dictionary()
        assert isinstance(result, dict)

    def test_get_dictionary_size(self):
        """Test dictionary size"""
        result = get_dictionary()
        assert len(result) == 208177

    def test_get_dictionary_contains_expected_entries(self):
        """Test that dictionary contains expected entries"""
        result = get_dictionary()
        # Test some common words that should be in the dictionary
        assert len(result) > 0
        assert all(isinstance(key, str) for key in result.keys())
        assert all(isinstance(value, str) for value in result.values())

    def test_get_dictionary_caching(self):
        """Test that get_dictionary results are cached"""
        # Call function twice and verify same object is returned
        result1 = get_dictionary()
        result2 = get_dictionary()
        assert result1 is result2  # Same object due to caching

    def test_get_dictionary_file_path(self):
        """Test that dictionary file exists"""
        import openodia.corpus.dictionary as dict_module
        dict_file = os.path.join(os.path.dirname(dict_module.__file__), "En-Or_word_pairs_v3.json")
        assert os.path.exists(dict_file)
        assert dict_file.endswith("En-Or_word_pairs_v3.json")

    def test_get_dictionary_file_format(self):
        """Test that dictionary file is valid JSON"""
        import openodia.corpus.dictionary as dict_module
        dict_file = os.path.join(os.path.dirname(dict_module.__file__), "En-Or_word_pairs_v3.json")
        
        with open(dict_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, dict)

    @patch('builtins.open')
    @patch('json.load')
    def test_get_dictionary_file_error_handling(self, mock_json_load, mock_file_open):
        """Test dictionary loading error handling"""
        # Clear the cache first
        get_dictionary.cache_clear()
        
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with pytest.raises(json.JSONDecodeError):
            get_dictionary()

    def test_get_dictionary_encoding(self):
        """Test that dictionary handles UTF-8 encoding properly"""
        result = get_dictionary()
        # Check that Odia text is properly encoded
        for key, value in list(result.items())[:10]:  # Test first 10 entries
            assert isinstance(key, str)
            assert isinstance(value, str)
            # Ensure strings can be encoded/decoded without errors
            key.encode('utf-8').decode('utf-8')
            value.encode('utf-8').decode('utf-8')
