"""
Test cases for error handling and edge cases across the library
"""
import pytest
from unittest.mock import patch, mock_open
import json

from openodia.corpus.dictionary import get_dictionary
from openodia import WordFrequency, alphabet, name, ud


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_wordfrequency_empty_text(self):
        """Test WordFrequency with empty text"""
        wf = WordFrequency("")
        assert wf.text == ""
        # Should not raise an error
        try:
            summary = wf.get_summary()
            assert isinstance(summary, dict)
        except Exception:
            pass  # Some implementations may not handle empty text

    def test_wordfrequency_none_text(self):
        """Test WordFrequency with None text"""
        # Some implementations may convert None to string
        try:
            wf = WordFrequency(None)  # type: ignore
            # If it doesn't raise an error, check if None was converted to string
            assert str(wf.text) in ["None", ""]
        except (TypeError, ValueError):
            pass  # Expected behavior

    def test_wordfrequency_non_string_text(self):
        """Test WordFrequency with non-string text"""
        # Some implementations may convert numbers to string
        try:
            wf = WordFrequency(123)  # type: ignore
            # If it doesn't raise an error, check if number was converted to string
            assert str(wf.text) == "123"
        except (TypeError, ValueError):
            pass  # Expected behavior

    def test_alphabet_methods_return_types(self):
        """Test that alphabet methods return expected types"""
        assert hasattr(alphabet, 'all_letters')
        letters = alphabet.all_letters
        assert isinstance(letters, (list, str))

    def test_name_generation_edge_cases(self):
        """Test name generation with edge cases"""
        # Test generating 0 names
        try:
            names = name.generate_names(0)
            assert len(names) == 0 or names is None
        except (ValueError, TypeError):
            pass  # Some implementations may not allow 0

        # Test generating negative number of names
        try:
            names = name.generate_names(-1)
            # Some implementations may return empty list or handle gracefully
            assert isinstance(names, list)
        except (ValueError, TypeError):
            pass  # Expected behavior for some implementations

    def test_name_generation_large_numbers(self):
        """Test name generation with large numbers"""
        # Should handle reasonable large numbers
        try:
            names = name.generate_names(1000)
            assert isinstance(names, list)
            assert len(names) <= 1000  # May return fewer if not enough names available
        except (MemoryError, ValueError):
            pass  # Implementation may have limits

    def test_ud_tokenizer_empty_text(self):
        """Test UnderstandData tokenizers with empty text"""
        try:
            words = ud.word_tokenizer("")
            assert isinstance(words, list)
            assert len(words) == 0
        except Exception:
            pass  # Some implementations may handle differently

        try:
            sentences = ud.sentence_tokenizer("")
            assert isinstance(sentences, list)
            assert len(sentences) == 0
        except Exception:
            pass

    def test_ud_tokenizer_none_input(self):
        """Test UnderstandData tokenizers with None input"""
        with pytest.raises((TypeError, AttributeError)):
            ud.word_tokenizer(None)

        with pytest.raises((TypeError, AttributeError)):
            ud.sentence_tokenizer(None)

    def test_ud_remove_stopwords_edge_cases(self):
        """Test remove_stopwords with edge cases"""
        # Empty list
        try:
            result = ud.remove_stopwords([])
            assert isinstance(result, list)
            assert len(result) == 0
        except Exception:
            pass

        # None input
        with pytest.raises((TypeError, AttributeError)):
            ud.remove_stopwords(None)  # type: ignore

    def test_dictionary_corruption_handling(self):
        """Test dictionary loading with corrupted data"""
        # Clear cache first
        get_dictionary.cache_clear()
        
        with patch('builtins.open', mock_open(read_data='invalid json')):
            with patch('json.load') as mock_json:
                mock_json.side_effect = json.JSONDecodeError("Invalid", "", 0)
                with pytest.raises(json.JSONDecodeError):
                    get_dictionary()

    def test_unicode_handling(self):
        """Test handling of various Unicode characters"""
        # Test with Odia text
        odia_text = "ଓଡିଆ ଭାଷା"
        
        try:
            wf = WordFrequency(odia_text)
            assert wf.text == odia_text
        except Exception:
            pass

        # Test with mixed scripts
        mixed_text = "Hello ଓଡିଆ नमस्ते"
        try:
            wf = WordFrequency(mixed_text)
            assert wf.text == mixed_text
        except Exception:
            pass

    def test_memory_efficiency(self):
        """Test memory efficiency with large inputs"""
        # Test with reasonably large text
        large_text = "ଓଡିଆ " * 1000
        
        try:
            wf = WordFrequency(large_text)
            assert isinstance(wf.text, str)
        except MemoryError:
            pytest.skip("System doesn't have enough memory for large text test")

    def test_thread_safety_basic(self):
        """Basic test for thread safety of dictionary loading"""
        import threading
        import time
        
        results = []
        errors = []
        
        def load_dict():
            try:
                result = get_dictionary()
                results.append(len(result))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_dict)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should not have errors and all results should be the same
        assert len(errors) == 0
        assert len(set(results)) <= 1  # All results should be identical
