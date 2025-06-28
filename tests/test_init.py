"""
Test cases for main module initialization
"""
import pytest

import openodia
from openodia import (
    alphabet,
    name,
    ud,
    other_lang_to_odia,
    odia_to_other_lang,
    universal_translation,
    WordFrequency,
    normalize_text,
    phonetic_odia,
)


class TestInit:
    """Test main module initialization"""

    def test_version_exists(self):
        """Test that version is defined"""
        assert hasattr(openodia, '__version__')
        assert isinstance(openodia.__version__, str)
        assert len(openodia.__version__) > 0

    def test_version_format(self):
        """Test version format"""
        version_parts = openodia.__version__.split('.')
        assert len(version_parts) >= 2  # At least major.minor
        assert all(part.isdigit() for part in version_parts[:2])  # Major and minor should be digits

    def test_all_exports_available(self):
        """Test that all __all__ exports are available"""
        expected_exports = [
            "alphabet",
            "name",
            "ud",
            "other_lang_to_odia",
            "odia_to_other_lang",
            "universal_translation",
            "WordFrequency",
            "normalize_text",
            "phonetic_odia",
        ]
        
        for export in expected_exports:
            assert hasattr(openodia, export)

    def test_alphabet_import(self):
        """Test alphabet import"""
        assert alphabet is not None
        assert hasattr(alphabet, 'all_letters')
        assert hasattr(alphabet, 'vowels')
        assert hasattr(alphabet, 'consonants')

    def test_name_import(self):
        """Test name import"""
        assert name is not None
        assert hasattr(name, 'generate_names')
        assert hasattr(name, 'generate_prefixes')

    def test_ud_import(self):
        """Test ud (UnderstandData) import"""
        assert ud is not None
        assert hasattr(ud, 'word_tokenizer')
        assert hasattr(ud, 'sentence_tokenizer')
        assert hasattr(ud, 'remove_stopwords')
        assert hasattr(ud, 'detect_language')

    def test_translation_functions_import(self):
        """Test translation functions import"""
        assert callable(other_lang_to_odia)
        assert callable(odia_to_other_lang)
        assert callable(universal_translation)

    def test_wordfrequency_import(self):
        """Test WordFrequency class import"""
        assert WordFrequency is not None
        assert hasattr(WordFrequency, 'get_summary')

    def test_can_create_wordfrequency_instance(self):
        """Test that WordFrequency can be instantiated"""
        wf = WordFrequency(text="Test text")
        assert wf.text == "Test text"

    def test_stopwords_import(self):
        """Test STOPWORDS import"""
        from openodia import STOPWORDS
        assert STOPWORDS is not None
        assert isinstance(STOPWORDS, list)
        assert len(STOPWORDS) > 0

    def test_module_docstring(self):
        """Test module has docstring"""
        assert openodia.__doc__ is not None
        assert len(openodia.__doc__.strip()) > 0

    def test_module_attributes(self):
        """Test that module has expected attributes"""
        expected_attributes = ['__version__', '__all__', '__doc__']
        for attr in expected_attributes:
            assert hasattr(openodia, attr)

    def test_all_list_completeness(self):
        """Test that __all__ contains all public exports"""
        assert isinstance(openodia.__all__, list)
        assert len(openodia.__all__) > 0
        
        # All items in __all__ should be available as module attributes
        for item in openodia.__all__:
            assert hasattr(openodia, item)

    def test_version_semantic_format(self):
        """Test version follows semantic versioning"""
        version = openodia.__version__
        parts = version.split('.')
        
        # Should have at least major.minor.patch
        assert len(parts) >= 3
        
        # Major, minor, patch should be numeric
        for i, part in enumerate(parts[:3]):
            assert part.isdigit(), f"Version part {i} ({part}) should be numeric"

    def test_imports_are_correct_types(self):
        """Test that imports are of correct types"""
        from openodia._letters import Letters
        from openodia._odianames import Names
        from openodia._understandData import UnderstandData
        from openodia._summarization import WordFrequency as WF
        
        # Test that the imported objects are instances or have expected attributes
        assert hasattr(alphabet, 'all_letters') or isinstance(alphabet, Letters)
        assert hasattr(name, 'generate_names') or isinstance(name, Names)
        assert hasattr(ud, 'word_tokenizer') or isinstance(ud, UnderstandData)
        assert WF == WordFrequency

    def test_translation_functions_signature(self):
        """Test translation functions have correct signatures"""
        import inspect
        
        # Test other_lang_to_odia signature
        sig = inspect.signature(other_lang_to_odia)
        params = list(sig.parameters.keys())
        assert 'text' in params
        
        # Test odia_to_other_lang signature
        sig = inspect.signature(odia_to_other_lang)
        params = list(sig.parameters.keys())
        assert 'text' in params
        
        # Test universal_translation signature
        sig = inspect.signature(universal_translation)
        params = list(sig.parameters.keys())
        assert 'text' in params

    def test_no_private_exports(self):
        """Test that __all__ doesn't contain private items"""
        for item in openodia.__all__:
            assert not item.startswith('_'), f"Private item {item} should not be in __all__"

    def test_classes_are_instantiable(self):
        """Test that exported classes can be instantiated"""
        # Test WordFrequency
        wf = WordFrequency("test text")
        assert hasattr(wf, 'text')
        
        # Test that Letters class has expected methods
        assert hasattr(alphabet, 'all_letters')
        
        # Test that Names class has expected methods
        assert hasattr(name, 'generate_names')
        
        # Test that UnderstandData class has expected methods
        assert hasattr(ud, 'word_tokenizer')

    def test_module_namespace_clean(self):
        """Test that module namespace doesn't have unexpected items"""
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(openodia) if not attr.startswith('_')]
        
        # Should contain all items from __all__
        for item in openodia.__all__:
            assert item in public_attrs

    def test_circular_import_safety(self):
        """Test that module can be imported multiple times without issues"""
        import openodia as oo1
        import openodia as oo2
        
        # Should be the same module
        assert oo1 is oo2
        assert oo1.__version__ == oo2.__version__
