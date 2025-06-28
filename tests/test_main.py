"""
Test cases for __main__ module
"""
import pytest
from io import StringIO
import sys
from unittest.mock import patch

from openodia.__main__ import main


class TestMain:
    """Test main module functionality"""

    def test_main_function_exists(self):
        """Test that main function exists and is callable"""
        assert callable(main)

    def test_main_with_no_args(self):
        """Test main function with no arguments"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main()
            output = mock_stdout.getvalue()
            assert "CLI building is in-progress." in output
            assert result is None

    def test_main_with_empty_args(self):
        """Test main function with empty args list"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([])
            output = mock_stdout.getvalue()
            assert "CLI building is in-progress." in output
            assert result is None

    def test_main_with_args(self):
        """Test main function with arguments"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main(['arg1', 'arg2'])
            output = mock_stdout.getvalue()
            assert "CLI building is in-progress." in output
            assert result is None

    def test_main_entry_point(self):
        """Test that the module can be run as main"""
        with patch('sys.argv', ['__main__.py']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stdout', new_callable=StringIO):
                    # Import and run the module's main block
                    import openodia.__main__
                    # The module should call sys.exit with the result of main()
                    # Since main() returns None, sys.exit should be called with None
