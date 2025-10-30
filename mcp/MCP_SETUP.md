# MCP Server Setup Guide

This document explains how to set up and use the MCP (Model Context Protocol) server for RepyV2 security layer testing.

## What is MCP?

MCP (Model Context Protocol) is a standard protocol that allows AI assistants to interact with external tools and services. This MCP server exposes the RepyV2 testing functionality from `post.py` as tools that can be called by AI assistants like Claude.

## Installation

### 1. Install Dependencies

```bash
/Users/lishuyu/miniconda3/bin/python -m pip install -r requirements.txt
```

Or install individually:
```bash
/Users/lishuyu/miniconda3/bin/python -m pip install requests mcp
```

### 2. Test the MCP Server

Run the server directly to ensure it works:

```bash
/Users/lishuyu/miniconda3/bin/python mcp_server.py
```

The server should start and wait for input via stdio. Press Ctrl+C to stop.

## Configuration for Cursor/Claude Desktop

### For Cursor IDE

Add this to your Cursor MCP settings (usually in `~/.cursor/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "repyv2-testing": {
      "command": "/Users/lishuyu/miniconda3/bin/python",
      "args": [
        "/Users/lishuyu/Codes/REPYV2_A2_V2/mcp_server.py"
      ],
      "env": {},
      "description": "RepyV2 Security Layer Testing Server"
    }
  }
}
```

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "repyv2-testing": {
      "command": "/Users/lishuyu/miniconda3/bin/python",
      "args": [
        "/Users/lishuyu/Codes/REPYV2_A2_V2/mcp/mcp_server.py"
      ]
    }
  }
}
```

## Available Tools

The MCP server provides three tools:

### 1. `repyv2_health_check`

Check if the RepyV2 execution server is available.

**Parameters:** None

**Example:**
```json
{
  "name": "repyv2_health_check",
  "arguments": {}
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "RepyV2 execution server is available"
}
```

### 2. `repyv2_execute`

Execute RepyV2 security layer with raw code strings.

**Parameters:**
- `monitor_text` (required): The security layer code as a string
- `attack_text` (required): The test case code as a string

**Example:**
```json
{
  "name": "repyv2_execute",
  "arguments": {
    "monitor_text": "# security layer code here...",
    "attack_text": "# test case code here..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "stdout": "Test 1 PASSED\nTest 2 PASSED\n...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.234
}
```

### 3. `repyv2_execute_files`

Execute RepyV2 security layer using file paths.

**Parameters:**
- `monitor_file` (required): Path to the monitor (security layer) file
- `attack_file` (required): Path to the attack (test case) file

**Example:**
```json
{
  "name": "repyv2_execute_files",
  "arguments": {
    "monitor_file": "/Users/lishuyu/Codes/REPYV2_A2_V2/sample_monitor.py",
    "attack_file": "/Users/lishuyu/Codes/REPYV2_A2_V2/sample_attack.py"
  }
}
```

**Response:**
```json
{
  "success": true,
  "stdout": "Test 1 PASSED\nTest 2 PASSED\n...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.234,
  "monitor_file": "/Users/lishuyu/Codes/REPYV2_A2_V2/sample_monitor.py",
  "attack_file": "/Users/lishuyu/Codes/REPYV2_A2_V2/sample_attack.py"
}
```

## Usage Examples

### From AI Assistant (Claude/Cursor)

Once configured, you can ask the AI assistant to:

1. **Check server health:**
   > "Check if the RepyV2 server is available"

2. **Test a security layer:**
   > "Test the sample_monitor.py with sample_attack.py"

3. **Test custom code:**
   > "Execute this security layer code with these test cases"

### Manual Testing with stdio

You can also manually test the MCP server by sending JSON-RPC messages:

```bash
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | /Users/lishuyu/miniconda3/bin/python mcp_server.py
```

## Architecture

```
┌─────────────────────┐
│   AI Assistant      │
│  (Claude/Cursor)    │
└──────────┬──────────┘
           │ MCP Protocol (stdio)
           │
┌──────────▼──────────┐
│   mcp_server.py     │
│  (This MCP Server)  │
└──────────┬──────────┘
           │ HTTP POST
           │
┌──────────▼──────────┐
│  Docker Server      │
│  (100.88.83.27:8000)│
│  RepyV2 + Python2.7 │
└─────────────────────┘
```

## Troubleshooting

### MCP Module Not Found

```bash
/Users/lishuyu/miniconda3/bin/python -m pip install mcp
```

### Server Not Responding

Check if the remote Docker server is accessible:
```bash
curl http://100.88.83.27:8000/health
```

### Permission Denied

Make sure the MCP server script is executable:
```bash
chmod +x /Users/lishuyu/Codes/REPYV2_A2_V2/mcp_server.py
```

### Python Path Issues

Ensure you're using the correct Python interpreter:
```bash
which /Users/lishuyu/miniconda3/bin/python
/Users/lishuyu/miniconda3/bin/python --version
```

## Benefits

✅ **AI-Powered Testing** - Use AI assistants to test and debug security layers  
✅ **Natural Language** - Ask questions in plain English  
✅ **Automated Workflows** - Chain multiple tests together  
✅ **Interactive Debugging** - Get immediate feedback on code changes  
✅ **No Manual API Calls** - AI handles the HTTP requests  

## Related Files

- `post.py` - Original HTTP client for manual testing
- `mcp_server.py` - MCP server implementation
- `mcp_config.json` - Sample MCP configuration
- `requirements.txt` - Python dependencies

## References

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [RepyV2 Documentation](https://github.com/SeattleTestbed/docs)

