"""
Tool Executor for OpenOdia

Routes tool calls to actual library functions with input validation
and structured output.

Author: Soumendra Kumar Sahoo
"""

from dataclasses import dataclass
from typing import Any

from openodia._tools import get_tool
from openodia._translate import other_lang_to_odia, odia_to_other_lang, universal_translation
from openodia._understandData import UnderstandData as ud
from openodia._summarization import WordFrequency
from openodia._odianames import Names as name


@dataclass
class ToolResult:
    """Structured result from tool execution."""
    success: bool
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        if self.success:
            return {"success": True, "result": self.result}
        return {"success": False, "error": self.error}


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


# Tool handler mapping
_TOOL_HANDLERS: dict[str, callable] = {}


def _register_handler(tool_name: str):
    """Decorator to register a tool handler."""
    def decorator(func):
        _TOOL_HANDLERS[tool_name] = func
        return func
    return decorator


@_register_handler("translate_to_odia")
def _handle_translate_to_odia(arguments: dict[str, Any]) -> Any:
    """Handle translate_to_odia tool call."""
    text = arguments["text"]
    source_language_code = arguments.get("source_language_code", "en")
    return other_lang_to_odia(text, source_language_code)


@_register_handler("translate_from_odia")
def _handle_translate_from_odia(arguments: dict[str, Any]) -> Any:
    """Handle translate_from_odia tool call."""
    text = arguments["text"]
    dest_language_code = arguments.get("dest_language_code", "en")
    return odia_to_other_lang(text, dest_language_code)


@_register_handler("universal_translate")
def _handle_universal_translate(arguments: dict[str, Any]) -> Any:
    """Handle universal_translate tool call."""
    text = arguments["text"]
    source_language_code = arguments.get("source_language_code", "en")
    dest_language_code = arguments.get("dest_language_code", "or")
    return universal_translation(text, source_language_code, dest_language_code)


@_register_handler("detect_language")
def _handle_detect_language(arguments: dict[str, Any]) -> Any:
    """Handle detect_language tool call."""
    text = arguments["text"]
    threshold = arguments.get("threshold", 0.5)
    return ud.detect_language(text, threshold)


@_register_handler("tokenize_words")
def _handle_tokenize_words(arguments: dict[str, Any]) -> Any:
    """Handle tokenize_words tool call."""
    text = arguments["text"]
    return ud.word_tokenizer(text)


@_register_handler("tokenize_sentences")
def _handle_tokenize_sentences(arguments: dict[str, Any]) -> Any:
    """Handle tokenize_sentences tool call."""
    text = arguments["text"]
    return ud.sentence_tokenizer(text)


@_register_handler("remove_stopwords")
def _handle_remove_stopwords(arguments: dict[str, Any]) -> Any:
    """Handle remove_stopwords tool call."""
    text = arguments["text"]
    return_string = arguments.get("return_string", True)
    return ud.remove_stopwords(text, get_str=return_string)


@_register_handler("summarize_text")
def _handle_summarize_text(arguments: dict[str, Any]) -> Any:
    """Handle summarize_text tool call."""
    text = arguments["text"]
    threshold = arguments.get("threshold")
    summarizer = WordFrequency(text=text)
    return summarizer.get_summary(threshold)


@_register_handler("generate_odia_names")
def _handle_generate_odia_names(arguments: dict[str, Any]) -> Any:
    """Handle generate_odia_names tool call."""
    count = arguments.get("count", 10)
    return name.generate_names(count)


@_register_handler("generate_odia_firstnames")
def _handle_generate_odia_firstnames(arguments: dict[str, Any]) -> Any:
    """Handle generate_odia_firstnames tool call."""
    count = arguments.get("count", 10)
    name_type = arguments.get("name_type", "")
    return name.generate_firstnames(count, name_type)


@_register_handler("generate_odia_surnames")
def _handle_generate_odia_surnames(arguments: dict[str, Any]) -> Any:
    """Handle generate_odia_surnames tool call."""
    count = arguments.get("count", 10)
    return name.generate_surnames(count)


def validate_arguments(tool_name: str, arguments: dict[str, Any]) -> list[str]:
    """
    Validate arguments against tool schema.
    
    Args:
        tool_name: Name of the tool
        arguments: Arguments to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    tool_def = get_tool(tool_name)
    if not tool_def:
        return [f"Unknown tool: {tool_name}"]
    
    errors = []
    params = tool_def["parameters"]
    properties = params.get("properties", {})
    required = params.get("required", [])
    
    # Check required parameters
    for req_param in required:
        if req_param not in arguments:
            errors.append(f"Missing required parameter: {req_param}")
    
    # Check parameter types (basic validation)
    for param_name, param_value in arguments.items():
        if param_name not in properties:
            errors.append(f"Unknown parameter: {param_name}")
            continue
        
        param_schema = properties[param_name]
        expected_type = param_schema.get("type")
        
        if expected_type == "string" and not isinstance(param_value, str):
            errors.append(f"Parameter '{param_name}' must be a string")
        elif expected_type == "integer" and not isinstance(param_value, int):
            errors.append(f"Parameter '{param_name}' must be an integer")
        elif expected_type == "number" and not isinstance(param_value, (int, float)):
            errors.append(f"Parameter '{param_name}' must be a number")
        elif expected_type == "boolean" and not isinstance(param_value, bool):
            errors.append(f"Parameter '{param_name}' must be a boolean")
        
        # Check enum values
        if "enum" in param_schema and param_value not in param_schema["enum"]:
            errors.append(f"Parameter '{param_name}' must be one of: {param_schema['enum']}")
    
    return errors


def execute_tool(tool_name: str, arguments: dict[str, Any], validate: bool = True) -> ToolResult:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        validate: Whether to validate arguments before execution
        
    Returns:
        ToolResult with success status and result or error
        
    Example:
        >>> result = execute_tool("translate_to_odia", {"text": "hello"})
        >>> print(result.result)
        ନମସ୍କାର
    """
    # Check if tool exists
    if tool_name not in _TOOL_HANDLERS:
        return ToolResult(
            success=False,
            error=f"Unknown tool: {tool_name}. Available tools: {list(_TOOL_HANDLERS.keys())}"
        )
    
    # Validate arguments if requested
    if validate:
        validation_errors = validate_arguments(tool_name, arguments)
        if validation_errors:
            return ToolResult(
                success=False,
                error=f"Validation failed: {'; '.join(validation_errors)}"
            )
    
    # Execute the tool
    try:
        handler = _TOOL_HANDLERS[tool_name]
        result = handler(arguments)
        return ToolResult(success=True, result=result)
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Execution failed: {type(e).__name__}: {str(e)}"
        )


def execute(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to execute a tool and return dict result.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Dictionary with 'success' and 'result' or 'error' keys
    """
    return execute_tool(tool_name, arguments).to_dict()


def list_handlers() -> list[str]:
    """List all registered tool handlers."""
    return list(_TOOL_HANDLERS.keys())
