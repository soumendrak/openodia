"""Tests for Tool Executor."""

import pytest

from openodia._tool_executor import (
    ToolResult,
    execute_tool,
    execute,
    validate_arguments,
    list_handlers,
)


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_success_result_to_dict(self):
        """Success result converts to dict correctly."""
        result = ToolResult(success=True, result="test_value")
        d = result.to_dict()
        assert d["success"] is True
        assert d["result"] == "test_value"
        assert "error" not in d

    def test_error_result_to_dict(self):
        """Error result converts to dict correctly."""
        result = ToolResult(success=False, error="Something went wrong")
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Something went wrong"
        assert "result" not in d


class TestValidateArguments:
    """Test argument validation."""

    def test_valid_arguments(self):
        """Valid arguments pass validation."""
        errors = validate_arguments("translate_to_odia", {"text": "hello"})
        assert len(errors) == 0

    def test_missing_required_parameter(self):
        """Missing required parameter fails validation."""
        errors = validate_arguments("translate_to_odia", {})
        assert len(errors) > 0
        assert any("Missing required parameter" in e for e in errors)

    def test_unknown_tool(self):
        """Unknown tool fails validation."""
        errors = validate_arguments("nonexistent_tool", {"text": "hello"})
        assert len(errors) > 0
        assert any("Unknown tool" in e for e in errors)

    def test_wrong_type_string(self):
        """Wrong type for string parameter fails validation."""
        errors = validate_arguments("translate_to_odia", {"text": 123})
        assert len(errors) > 0
        assert any("must be a string" in e for e in errors)

    def test_wrong_type_integer(self):
        """Wrong type for integer parameter fails validation."""
        errors = validate_arguments("generate_odia_names", {"count": "ten"})
        assert len(errors) > 0
        assert any("must be an integer" in e for e in errors)

    def test_invalid_enum_value(self):
        """Invalid enum value fails validation."""
        errors = validate_arguments(
            "generate_odia_firstnames",
            {"count": 5, "name_type": "invalid_type"}
        )
        assert len(errors) > 0
        assert any("must be one of" in e for e in errors)


class TestExecuteTool:
    """Test tool execution."""

    def test_execute_unknown_tool(self):
        """Executing unknown tool returns error."""
        result = execute_tool("nonexistent_tool", {})
        assert result.success is False
        assert "Unknown tool" in result.error

    def test_execute_detect_language_odia(self):
        """Execute detect_language with Odia text."""
        result = execute_tool("detect_language", {"text": "ନମସ୍କାର"})
        assert result.success is True
        assert result.result["language"] == "odia"

    def test_execute_detect_language_english(self):
        """Execute detect_language with English text."""
        result = execute_tool("detect_language", {"text": "hello world"})
        assert result.success is True
        assert result.result["language"] == "non-odia"

    def test_execute_tokenize_words(self):
        """Execute tokenize_words."""
        result = execute_tool("tokenize_words", {"text": "ନମସ୍କାର ବନ୍ଧୁ"})
        assert result.success is True
        assert isinstance(result.result, list)
        assert len(result.result) == 2

    def test_execute_tokenize_sentences(self):
        """Execute tokenize_sentences."""
        result = execute_tool(
            "tokenize_sentences",
            {"text": "ନମସ୍କାର । କେମିତି ଅଛ"}
        )
        assert result.success is True
        assert isinstance(result.result, list)

    def test_execute_remove_stopwords_string(self):
        """Execute remove_stopwords returning string."""
        result = execute_tool(
            "remove_stopwords",
            {"text": "ଏହା ଏକ ପରୀକ୍ଷା", "return_string": True}
        )
        assert result.success is True
        assert isinstance(result.result, str)

    def test_execute_remove_stopwords_list(self):
        """Execute remove_stopwords returning list."""
        result = execute_tool(
            "remove_stopwords",
            {"text": "ଏହା ଏକ ପରୀକ୍ଷା", "return_string": False}
        )
        assert result.success is True
        assert isinstance(result.result, list)

    def test_execute_generate_odia_names(self):
        """Execute generate_odia_names."""
        result = execute_tool("generate_odia_names", {"count": 3})
        assert result.success is True
        assert isinstance(result.result, list)
        assert len(result.result) == 3

    def test_execute_generate_odia_firstnames(self):
        """Execute generate_odia_firstnames."""
        result = execute_tool(
            "generate_odia_firstnames",
            {"count": 5, "name_type": "male"}
        )
        assert result.success is True
        assert isinstance(result.result, list)
        assert len(result.result) == 5

    def test_execute_generate_odia_surnames(self):
        """Execute generate_odia_surnames."""
        result = execute_tool("generate_odia_surnames", {"count": 4})
        assert result.success is True
        assert isinstance(result.result, list)
        assert len(result.result) == 4

    def test_execute_summarize_text(self):
        """Execute summarize_text."""
        odia_text = "ଓଡ଼ିଶା ଭାରତର ଏକ ରାଜ୍ୟ । ଓଡ଼ିଶାର ରାଜଧାନୀ ଭୁବନେଶ୍ୱର । ଓଡ଼ିଶା ପୂର୍ବ ଭାରତରେ ଅବସ୍ଥିତ ।"
        result = execute_tool("summarize_text", {"text": odia_text})
        assert result.success is True
        assert isinstance(result.result, str)

    def test_execute_with_validation_disabled(self):
        """Execute with validation disabled still works."""
        result = execute_tool(
            "detect_language",
            {"text": "hello"},
            validate=False
        )
        assert result.success is True

    def test_execute_with_invalid_args_and_validation(self):
        """Execute with invalid args and validation enabled fails."""
        result = execute_tool(
            "translate_to_odia",
            {},  # Missing required 'text'
            validate=True
        )
        assert result.success is False
        assert "Validation failed" in result.error


class TestExecuteConvenience:
    """Test execute() convenience function."""

    def test_execute_returns_dict(self):
        """execute() returns a dictionary."""
        result = execute("detect_language", {"text": "hello"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_success(self):
        """execute() success case."""
        result = execute("detect_language", {"text": "ନମସ୍କାର"})
        assert result["success"] is True
        assert "result" in result

    def test_execute_error(self):
        """execute() error case."""
        result = execute("nonexistent_tool", {})
        assert result["success"] is False
        assert "error" in result


class TestListHandlers:
    """Test list_handlers function."""

    def test_list_handlers_not_empty(self):
        """list_handlers returns non-empty list."""
        handlers = list_handlers()
        assert len(handlers) > 0

    def test_list_handlers_contains_expected(self):
        """list_handlers contains expected tools."""
        handlers = list_handlers()
        expected = [
            "translate_to_odia",
            "translate_from_odia",
            "detect_language",
            "tokenize_words",
            "generate_odia_names",
        ]
        for tool in expected:
            assert tool in handlers
