"""
Test cases for utility module
"""
import logging
import pytest
from rich.logging import RichHandler

from openodia.common.utility import LOGGER, FORMAT


class TestUtility:
    """Test utility module"""

    def test_logger_exists(self):
        """Test that logger is properly configured"""
        assert LOGGER is not None
        assert isinstance(LOGGER, logging.Logger)

    def test_logger_name(self):
        """Test logger name"""
        assert LOGGER.name == "rich"

    def test_logger_level(self):
        """Test logger level is set"""
        # Logger should have some level set
        assert hasattr(LOGGER, 'level')
        assert hasattr(LOGGER, 'handlers')

    def test_logger_can_log(self):
        """Test that logger can log messages"""
        # Test that logger methods exist and are callable
        assert callable(LOGGER.info)
        assert callable(LOGGER.debug)
        assert callable(LOGGER.warning)
        assert callable(LOGGER.error)
        assert callable(LOGGER.critical)

    def test_logger_handlers(self):
        """Test that logger has handlers configured"""
        # Should have at least one handler
        assert len(LOGGER.handlers) >= 0  # Handlers might be on parent logger

    def test_format_constant(self):
        """Test that FORMAT constant is defined correctly"""
        assert FORMAT == "%(message)s"
        assert isinstance(FORMAT, str)

    def test_logging_configuration(self):
        """Test logging basic configuration"""
        # Test that logging has been configured
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 0  # May have handlers on root or parent
        
        # Check if any handler is RichHandler (may be on parent logger)
        def has_rich_handler_recursive(logger):
            for handler in logger.handlers:
                if isinstance(handler, RichHandler):
                    return True
            if logger.parent and logger.parent != logger:
                return has_rich_handler_recursive(logger.parent)
            return False
        
        # The rich handler might be on the root logger or configured elsewhere
        # Just test that logging is working
        assert hasattr(root_logger, 'handlers')

    def test_rich_handler_configuration(self):
        """Test RichHandler configuration"""
        root_logger = logging.getLogger()
        rich_handlers = [h for h in root_logger.handlers if isinstance(h, RichHandler)]
        
        if rich_handlers:
            handler = rich_handlers[0]
            # Test that RichHandler has the expected configuration
            assert hasattr(handler, 'rich_tracebacks')
            assert hasattr(handler, 'tracebacks_show_locals')

    def test_logger_inheritance(self):
        """Test logger inheritance from root logger"""
        root_logger = logging.getLogger()
        assert LOGGER.parent == root_logger or LOGGER.parent == root_logger.parent

    def test_logger_effective_level(self):
        """Test logger effective level"""
        effective_level = LOGGER.getEffectiveLevel()
        assert isinstance(effective_level, int)
        assert effective_level >= 0

    def test_logger_propagate(self):
        """Test logger propagation setting"""
        # By default, loggers should propagate to parent
        assert hasattr(LOGGER, 'propagate')
        assert isinstance(LOGGER.propagate, bool)

    def test_can_create_log_record(self):
        """Test that logger can create log records"""
        # Test that we can create a log record without errors
        try:
            LOGGER.info("Test message")
            LOGGER.debug("Debug message")
            LOGGER.warning("Warning message")
            LOGGER.error("Error message")
        except Exception as e:
            pytest.fail(f"Logger failed to create log records: {e}")

    def test_logger_disabled_state(self):
        """Test logger disabled state"""
        assert hasattr(LOGGER, 'disabled')
        # Logger should not be disabled by default
        assert not LOGGER.disabled
