"""
MCP Server for OpenOdia

Exposes OpenOdia NLP tools via Model Context Protocol (MCP).
Supports stdio transport for IDE integration.

Author: Soumendra Kumar Sahoo

Usage:
    python -m openodia.mcp_server

MCP Client Configuration:
    {
        "mcpServers": {
            "openodia": {
                "command": "python",
                "args": ["-m", "openodia.mcp_server"]
            }
        }
    }
"""

import asyncio
import json
import logging
import sys
from typing import Any

from openodia._tools import TOOL_DEFINITIONS
from openodia._tool_executor import execute_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("openodia.mcp")


class MCPServer:
    """
    MCP Server implementation for OpenOdia.
    
    Implements the Model Context Protocol over stdio transport.
    """

    def __init__(self):
        self.tools = {tool["name"]: tool for tool in TOOL_DEFINITIONS}
        self._request_id = 0

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas in MCP format."""
        mcp_tools = []
        for tool in TOOL_DEFINITIONS:
            mcp_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["parameters"],
            })
        return mcp_tools

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        logger.info(f"Client initialized: {params.get('clientInfo', {})}")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "openodia",
                "version": "0.1.12",
            },
        }

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list request."""
        return {"tools": self._get_tool_schemas()}

    def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        logger.info(f"Tool call: {tool_name} with args: {arguments}")

        if tool_name not in self.tools:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "error": f"Unknown tool: {tool_name}",
                            "available_tools": list(self.tools.keys()),
                        }),
                    }
                ],
                "isError": True,
            }

        result = execute_tool(tool_name, arguments)

        if result.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result.result, ensure_ascii=False),
                    }
                ],
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"error": result.error}),
                    }
                ],
                "isError": True,
            }

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """
        Handle an incoming JSON-RPC request.
        
        Args:
            request: JSON-RPC request object
            
        Returns:
            JSON-RPC response object or None for notifications
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.debug(f"Received request: {method}")

        # Handle notifications (no id)
        if request_id is None:
            if method == "notifications/initialized":
                logger.info("Client sent initialized notification")
            elif method == "notifications/cancelled":
                logger.info(f"Request cancelled: {params}")
            return None

        # Handle requests
        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "ping":
                result = {}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }

        except Exception as e:
            logger.exception(f"Error handling request: {method}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }

    async def run_stdio(self):
        """Run the MCP server over stdio transport."""
        logger.info("OpenOdia MCP Server starting on stdio...")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        logger.info("OpenOdia MCP Server ready")

        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    logger.info("EOF received, shutting down")
                    break

                line = line.decode("utf-8").strip()
                if not line:
                    continue

                logger.debug(f"Received: {line}")

                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                        },
                    }
                    writer.write((json.dumps(error_response) + "\n").encode("utf-8"))
                    await writer.drain()
                    continue

                # Handle request
                response = self.handle_request(request)

                # Send response (if not a notification)
                if response is not None:
                    response_json = json.dumps(response, ensure_ascii=False)
                    logger.debug(f"Sending: {response_json}")
                    writer.write((response_json + "\n").encode("utf-8"))
                    await writer.drain()

            except Exception as e:
                logger.exception(f"Error in main loop: {e}")
                break

        logger.info("OpenOdia MCP Server stopped")


def main():
    """Entry point for the MCP server."""
    server = MCPServer()
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
