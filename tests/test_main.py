"""
Test cases for __main__ module (``python -m openodia`` runs the CLI)
"""

import pytest

from openodia import cli
from openodia.__main__ import main


class TestMain:
    """Test main module functionality"""

    def test_main_is_the_cli_entry_point(self):
        assert main is cli.main

    def test_main_with_no_args_requires_a_command(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2
        assert "COMMAND" in capsys.readouterr().err

    def test_main_with_args(self, capsys):
        assert main(["tokenize", "ରାମ ସୀତା"]) == 0
        assert "ରାମ" in capsys.readouterr().out
