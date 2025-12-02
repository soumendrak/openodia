"""
LLM Tool Interface for OpenOdia

This module defines tool schemas compatible with:
- OpenAI function calling
- Anthropic tool use
- MCP (Model Context Protocol)

Author: Soumendra Kumar Sahoo
"""

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable

# Tool definitions with metadata
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "translate_to_odia",
        "description": "Translate text from any language to Odia. Supports English (with offline dictionary) and other languages via Google Translate.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to translate to Odia"
                },
                "source_language_code": {
                    "type": "string",
                    "description": "ISO 639-1 language code of the source language (e.g., 'en' for English, 'hi' for Hindi)",
                    "default": "en"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "translate_from_odia",
        "description": "Translate Odia text to another language.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The Odia text to translate"
                },
                "dest_language_code": {
                    "type": "string",
                    "description": "ISO 639-1 language code of the destination language (e.g., 'en' for English, 'hi' for Hindi)",
                    "default": "en"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "universal_translate",
        "description": "Translate text between any two languages. By default translates English to Odia.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to translate"
                },
                "source_language_code": {
                    "type": "string",
                    "description": "ISO 639-1 language code of the source language",
                    "default": "en"
                },
                "dest_language_code": {
                    "type": "string",
                    "description": "ISO 639-1 language code of the destination language",
                    "default": "or"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "detect_language",
        "description": "Detect if the given text is in Odia language or not. Returns language classification and confidence score.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze for language detection"
                },
                "threshold": {
                    "type": "number",
                    "description": "Confidence threshold (0.0-1.0) for classifying as Odia. Default is 0.5",
                    "default": 0.5
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "tokenize_words",
        "description": "Split Odia text into individual word tokens. Handles Odia punctuation and Unicode characters.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The Odia text to tokenize into words"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "tokenize_sentences",
        "description": "Split Odia text into sentences. Uses Odia sentence delimiter '।' (purna viram).",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The Odia text to split into sentences"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "remove_stopwords",
        "description": "Remove common Odia stopwords from text. Returns cleaned text without frequently used words.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The Odia text to remove stopwords from"
                },
                "return_string": {
                    "type": "boolean",
                    "description": "If true, returns a string; if false, returns a list of tokens",
                    "default": True
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "summarize_text",
        "description": "Generate a summary of Odia text using word frequency analysis. Extracts sentences containing the most frequent meaningful words.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The Odia text to summarize"
                },
                "threshold": {
                    "type": "number",
                    "description": "Higher values produce shorter summaries. If not provided, an optimal threshold is calculated automatically.",
                    "default": None
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "generate_odia_names",
        "description": "Generate random Odia full names (first name + surname).",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of names to generate",
                    "default": 10
                }
            },
            "required": []
        }
    },
    {
        "name": "generate_odia_firstnames",
        "description": "Generate random Odia first names. Can filter by gender type.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of first names to generate",
                    "default": 10
                },
                "name_type": {
                    "type": "string",
                    "description": "Type of names: 'male', 'female', 'unisex', or empty for mixed",
                    "enum": ["male", "female", "unisex", ""],
                    "default": ""
                }
            },
            "required": []
        }
    },
    {
        "name": "generate_odia_surnames",
        "description": "Generate random Odia surnames/last names.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of surnames to generate",
                    "default": 10
                }
            },
            "required": []
        }
    }
]


@dataclass
class ToolDefinition:
    """Represents a single tool definition with schema and metadata."""
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any] | None = None


@dataclass
class ToolRegistry:
    """Registry of all available tools with format conversion utilities."""
    _tools: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize registry with all tool definitions."""
        for tool_def in TOOL_DEFINITIONS:
            self._tools[tool_def["name"]] = tool_def

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get a single tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all available tool names."""
        return list(self._tools.keys())

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all tool definitions."""
        return list(self._tools.values())

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions in OpenAI function calling format.

        Returns:
            List of tools in OpenAI's function format:
            {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
        """
        openai_tools = []
        for tool in self._tools.values():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return openai_tools

    def get_anthropic_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions in Anthropic tool use format.

        Returns:
            List of tools in Anthropic's format:
            {"name": ..., "description": ..., "input_schema": ...}
        """
        anthropic_tools = []
        for tool in self._tools.values():
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]
            })
        return anthropic_tools

    def get_mcp_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions in MCP format.

        Returns:
            List of tools in MCP's format:
            {"name": ..., "description": ..., "inputSchema": ...}
        """
        mcp_tools = []
        for tool in self._tools.values():
            mcp_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["parameters"]
            })
        return mcp_tools


# Global registry instance
_registry = ToolRegistry()


def get_tool(name: str) -> dict[str, Any] | None:
    """Get a single tool definition by name."""
    return _registry.get_tool(name)


def list_tools() -> list[str]:
    """List all available tool names."""
    return _registry.list_tools()


def get_all_tools() -> list[dict[str, Any]]:
    """Get all tool definitions in generic format."""
    return _registry.get_all_tools()


def get_openai_tools() -> list[dict[str, Any]]:
    """Get tool definitions in OpenAI function calling format."""
    return _registry.get_openai_tools()


def get_anthropic_tools() -> list[dict[str, Any]]:
    """Get tool definitions in Anthropic tool use format."""
    return _registry.get_anthropic_tools()


def get_mcp_tools() -> list[dict[str, Any]]:
    """Get tool definitions in MCP format."""
    return _registry.get_mcp_tools()
