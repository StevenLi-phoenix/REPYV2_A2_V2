#!/usr/bin/env python3
"""
MCP Server for RepyV2 Security Layer Testing
Exposes the post.py functionality as MCP tools
"""
import asyncio
import json
import sys
from typing import Any
import requests

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)


# Configuration
BASE_URL = "http://100.88.83.27:8000"

# Create MCP server instance
app = Server("repyv2-testing-server")


def health_check() -> dict[str, Any]:
    """Check if the remote RepyV2 execution server is available."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "ok", "message": "RepyV2 execution server is available"}
        else:
            return {"status": "error", "message": f"Server returned status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}


def execute_security_layer(monitor_text: str, attack_text: str) -> dict[str, Any]:
    """Execute a security layer with test cases on the remote RepyV2 server."""
    try:
        payload = {
            "monitor_text": monitor_text,
            "attack_text": attack_text
        }
        response = requests.post(f"{BASE_URL}/execute", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Exit code 143 (SIGTERM) is expected behavior for RepyV2
            # Consider it successful if we got output, even with exit code 143
            if result.get('exit_code') == 143 and result.get('stdout'):
                result['success'] = True
                result['note'] = 'Exit code 143 (SIGTERM) is expected for RepyV2 execution'
            return result
        else:
            return {
                "success": False,
                "error": f"Server returned status code {response.status_code}",
                "stdout": "",
                "stderr": response.text
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to connect: {str(e)}",
            "stdout": "",
            "stderr": ""
        }


def read_file_content(filepath: str) -> str:
    """Read content from a file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Failed to read file {filepath}: {str(e)}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="repyv2_health_check",
            description="Check if the RepyV2 execution server is available and responding",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="repyv2_execute",
            description=(
                "Execute a RepyV2 security layer with test cases. "
                "Provide the monitor (security layer) code and attack (test) code as strings. "
                "Returns execution results including stdout, stderr, and exit code. Exit code 143 (SIGTERM) is expected for RepyV2 execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor_text": {
                        "type": "string",
                        "description": "The security layer (monitor) code to test"
                    },
                    "attack_text": {
                        "type": "string",
                        "description": "The test case (attack) code to run against the monitor"
                    }
                },
                "required": ["monitor_text", "attack_text"]
            }
        ),
        Tool(
            name="repyv2_execute_files",
            description=(
                "Execute RepyV2 security layer using file paths. "
                "Reads the monitor and attack files, then executes them on the remote server. "
                "Useful when you have file paths instead of raw code strings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor_file": {
                        "type": "string",
                        "description": "Path to the monitor (security layer) file"
                    },
                    "attack_file": {
                        "type": "string",
                        "description": "Path to the attack (test case) file"
                    }
                },
                "required": ["monitor_file", "attack_file"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "repyv2_health_check":
        result = health_check()
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "repyv2_execute":
        monitor_text = arguments.get("monitor_text", "")
        attack_text = arguments.get("attack_text", "")
        
        if not monitor_text or not attack_text:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Both monitor_text and attack_text are required"
                }, indent=2)
            )]
        
        result = execute_security_layer(monitor_text, attack_text)
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "repyv2_execute_files":
        monitor_file = arguments.get("monitor_file", "")
        attack_file = arguments.get("attack_file", "")
        
        if not monitor_file or not attack_file:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Both monitor_file and attack_file are required"
                }, indent=2)
            )]
        
        try:
            monitor_text = read_file_content(monitor_file)
            attack_text = read_file_content(attack_file)
            result = execute_security_layer(monitor_text, attack_text)
            
            # Add file information to result
            result["monitor_file"] = monitor_file
            result["attack_file"] = attack_file
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                }, indent=2)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Unknown tool: {name}"
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

