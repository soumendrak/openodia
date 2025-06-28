"""
Test cases for corpus module initialization
"""
import pytest
import os

import openodia.corpus


class TestCorpusInit:
    """Test corpus module initialization"""

    def test_corpus_module_exists(self):
        """Test that corpus module can be imported"""
        assert openodia.corpus is not None

    def test_corpus_module_path(self):
        """Test corpus module path"""
        corpus_path = openodia.corpus.__file__
        assert corpus_path is not None
        assert os.path.exists(os.path.dirname(corpus_path))

    def test_corpus_package_structure(self):
        """Test that corpus is a package"""
        assert hasattr(openodia.corpus, '__path__')
        assert isinstance(openodia.corpus.__path__, list)

    def test_corpus_directory_contents(self):
        """Test corpus directory contains expected files"""
        corpus_dir = os.path.dirname(openodia.corpus.__file__)
        expected_files = [
            '__init__.py',
            'dictionary.py',
            'En-Or_word_pairs_v3.json',
            'embeddings.txt'
        ]
        
        for expected_file in expected_files:
            file_path = os.path.join(corpus_dir, expected_file)
            assert os.path.exists(file_path), f"Expected file {expected_file} not found in corpus directory"

    def test_corpus_json_file_readable(self):
        """Test that the JSON dictionary file is readable"""
        corpus_dir = os.path.dirname(openodia.corpus.__file__)
        json_file = os.path.join(corpus_dir, 'En-Or_word_pairs_v3.json')
        
        # Test file can be opened and read
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read(100)  # Read first 100 chars
            assert len(content) > 0

    def test_corpus_embeddings_file_readable(self):
        """Test that the embeddings file is readable"""
        corpus_dir = os.path.dirname(openodia.corpus.__file__)
        embeddings_file = os.path.join(corpus_dir, 'embeddings.txt')
        
        # Test file can be opened and read
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            content = f.read(100)  # Read first 100 chars
            assert len(content) > 0
