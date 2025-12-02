"""Tests for MCP Server."""

import json

from openodia.mcp_server import MCPServer


class TestMCPServer:
    """Test MCP Server functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_server_initialization(self):
        """Server initializes with tools."""
        assert len(self.server.tools) > 0
        assert "translate_to_odia" in self.server.tools

    def test_get_tool_schemas(self):
        """Tool schemas are in MCP format."""
        schemas = self.server._get_tool_schemas()
        assert len(schemas) > 0
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema


class TestMCPInitialize:
    """Test initialize request handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_initialize_response(self):
        """Initialize returns proper response."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response["result"]
        assert "serverInfo" in response["result"]


class TestMCPToolsList:
    """Test tools/list request handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_tools_list_response(self):
        """tools/list returns all tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 11


class TestMCPToolsCall:
    """Test tools/call request handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_detect_language_odia(self):
        """Call detect_language with Odia text."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "detect_language",
                "arguments": {"text": "ନମସ୍କାର"},
            },
        }
        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"].get("isError") is not True

        content = json.loads(response["result"]["content"][0]["text"])
        assert content["language"] == "odia"

    def test_tokenize_words(self):
        """Call tokenize_words."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "tokenize_words",
                "arguments": {"text": "ନମସ୍କାର ବନ୍ଧୁ"},
            },
        }
        response = self.server.handle_request(request)

        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, list)
        assert len(content) == 2

    def test_generate_odia_names(self):
        """Call generate_odia_names."""
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "generate_odia_names",
                "arguments": {"count": 3},
            },
        }
        response = self.server.handle_request(request)

        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, list)
        assert len(content) == 3

    def test_unknown_tool_error(self):
        """Call unknown tool returns error."""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {},
            },
        }
        response = self.server.handle_request(request)

        assert "result" in response
        assert response["result"]["isError"] is True

    def test_invalid_arguments_error(self):
        """Call with invalid arguments returns error."""
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "translate_to_odia",
                "arguments": {},  # Missing required 'text'
            },
        }
        response = self.server.handle_request(request)

        assert "result" in response
        assert response["result"]["isError"] is True


class TestMCPNotifications:
    """Test notification handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_initialized_notification(self):
        """Initialized notification returns None."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        response = self.server.handle_request(request)
        assert response is None

    def test_cancelled_notification(self):
        """Cancelled notification returns None."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": 1},
        }
        response = self.server.handle_request(request)
        assert response is None


class TestMCPErrors:
    """Test error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_unknown_method_error(self):
        """Unknown method returns error."""
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "unknown/method",
            "params": {},
        }
        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        assert response["error"]["code"] == -32601

    def test_ping_response(self):
        """Ping returns empty result."""
        request = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "ping",
            "params": {},
        }
        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 9
        assert response["result"] == {}
