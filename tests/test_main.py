"""Tests for the command line interface in :mod:`openodia.__main__`."""

from io import StringIO
from unittest.mock import patch

import pytest

from openodia.__main__ import main


class TestCLI:
    """CLI behaviour tests."""

    def run(self, args):
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            main(args)
            return stdout.getvalue().strip()

    def test_tokenize_words(self):
        output = self.run(["tokenize", "words", "ଏହା ଏକ ପରୀକ୍ଷା ।"])
        assert output == "ଏହା ଏକ ପରୀକ୍ଷା ।"

    def test_tokenize_sentences(self):
        text = "ଏହା ପ୍ରଥମ ବାକ୍ୟ । ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ ।"
        output = self.run(["tokenize", "sentences", text])
        assert output == "ଏହା ପ୍ରଥମ ବାକ୍ୟ  ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ"

    def test_translate_default(self):
        output = self.run(["translate", "hello! feeling good?"])
        assert output == "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?"

    def test_summarize(self):
        text = "ଏହା ପ୍ରଥମ ବାକ୍ୟ । ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ ।"
        output = self.run(["summarize", text, "--threshold", "1"])
        assert output == "ଏହା ପ୍ରଥମ ବାକ୍ୟ  ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ"

    def test_dataset_info(self):
        output = self.run(["dataset", "info"])
        assert "dictionary" in output

    def test_entry_point(self):
        with patch("sys.argv", ["openodia", "translate", "hello! feeling good?"]):
            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_not_called()
