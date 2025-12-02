"""Tests for LLM Tool Interface definitions."""

from openodia._tools import (
    TOOL_DEFINITIONS,
    ToolRegistry,
    get_tool,
    list_tools,
    get_all_tools,
    get_openai_tools,
    get_anthropic_tools,
    get_mcp_tools,
)


class TestToolDefinitions:
    """Test tool definition structure and content."""

    def test_tool_definitions_not_empty(self):
        """Ensure tool definitions exist."""
        assert len(TOOL_DEFINITIONS) > 0

    def test_all_tools_have_required_fields(self):
        """Each tool must have name, description, and parameters."""
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
            assert "parameters" in tool, f"Tool {tool.get('name')} missing 'parameters'"

    def test_parameters_have_valid_schema(self):
        """Parameters must follow JSON Schema structure."""
        for tool in TOOL_DEFINITIONS:
            params = tool["parameters"]
            assert params.get("type") == "object", f"Tool {tool['name']} parameters must be type 'object'"
            assert "properties" in params, f"Tool {tool['name']} missing 'properties'"
            assert "required" in params, f"Tool {tool['name']} missing 'required'"

    def test_expected_tools_exist(self):
        """Verify all expected tools are defined."""
        expected_tools = [
            "translate_to_odia",
            "translate_from_odia",
            "universal_translate",
            "detect_language",
            "tokenize_words",
            "tokenize_sentences",
            "remove_stopwords",
            "summarize_text",
            "generate_odia_names",
            "generate_odia_firstnames",
            "generate_odia_surnames",
        ]
        tool_names = [t["name"] for t in TOOL_DEFINITIONS]
        for expected in expected_tools:
            assert expected in tool_names, f"Missing expected tool: {expected}"


class TestToolRegistry:
    """Test ToolRegistry class."""

    def test_registry_initialization(self):
        """Registry should initialize with all tools."""
        registry = ToolRegistry()
        assert len(registry.list_tools()) == len(TOOL_DEFINITIONS)

    def test_get_tool_existing(self):
        """Get an existing tool by name."""
        registry = ToolRegistry()
        tool = registry.get_tool("translate_to_odia")
        assert tool is not None
        assert tool["name"] == "translate_to_odia"

    def test_get_tool_nonexistent(self):
        """Get a non-existent tool returns None."""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent_tool")
        assert tool is None

    def test_list_tools(self):
        """List tools returns all tool names."""
        registry = ToolRegistry()
        names = registry.list_tools()
        assert isinstance(names, list)
        assert "translate_to_odia" in names


class TestOpenAIFormat:
    """Test OpenAI function calling format conversion."""

    def test_openai_format_structure(self):
        """OpenAI format should have type and function keys."""
        tools = get_openai_tools()
        assert len(tools) > 0
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_openai_tool_count_matches(self):
        """OpenAI tools count should match definitions."""
        tools = get_openai_tools()
        assert len(tools) == len(TOOL_DEFINITIONS)


class TestAnthropicFormat:
    """Test Anthropic tool use format conversion."""

    def test_anthropic_format_structure(self):
        """Anthropic format should have name, description, input_schema."""
        tools = get_anthropic_tools()
        assert len(tools) > 0
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_anthropic_tool_count_matches(self):
        """Anthropic tools count should match definitions."""
        tools = get_anthropic_tools()
        assert len(tools) == len(TOOL_DEFINITIONS)


class TestMCPFormat:
    """Test MCP format conversion."""

    def test_mcp_format_structure(self):
        """MCP format should have name, description, inputSchema."""
        tools = get_mcp_tools()
        assert len(tools) > 0
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_mcp_tool_count_matches(self):
        """MCP tools count should match definitions."""
        tools = get_mcp_tools()
        assert len(tools) == len(TOOL_DEFINITIONS)


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_get_tool(self):
        """Module get_tool function works."""
        tool = get_tool("detect_language")
        assert tool is not None
        assert tool["name"] == "detect_language"

    def test_list_tools(self):
        """Module list_tools function works."""
        names = list_tools()
        assert len(names) == len(TOOL_DEFINITIONS)

    def test_get_all_tools(self):
        """Module get_all_tools function works."""
        tools = get_all_tools()
        assert len(tools) == len(TOOL_DEFINITIONS)
