"""Tests for corpus loader helper functions."""

import openodia.corpus as corpus


class TestCorpusLoaders:
    def test_load_parallel_corpus(self):
        data = corpus.load_parallel_corpus()
        assert isinstance(data, list)
        assert data[0] == ("Hello", "ନମସ୍କାର")

    def test_load_monolingual_corpus(self):
        data = corpus.load_monolingual_corpus()
        assert isinstance(data, list)
        assert data[0] == "ନମସ୍କାର କେମିତି ଅଛନ୍ତି?"
