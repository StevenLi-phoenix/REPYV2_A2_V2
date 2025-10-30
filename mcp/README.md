# MCP Server for RepyV2 Testing

This folder contains the MCP (Model Context Protocol) server implementation for AI-powered RepyV2 security layer testing.

## Quick Start

### Test the Server
```bash
cd /Users/lishuyu/Codes/REPYV2_A2_V2/mcp
/Users/lishuyu/miniconda3/bin/python test_mcp_direct.py
```

Expected: **2/2 tests passed ✓**

### Start the Server
```bash
cd /Users/lishuyu/Codes/REPYV2_A2_V2/mcp
./start_mcp_server.sh
```

Or manually:
```bash
/Users/lishuyu/miniconda3/bin/python mcp_server.py
```

## Files

- **mcp_server.py** - MCP server implementation with 3 tools
- **mcp_config.json** - Configuration for Cursor/Claude Desktop
- **test_mcp_direct.py** - Direct function tests (recommended)
- **test_mcp_server.py** - JSON-RPC protocol tests
- **start_mcp_server.sh** - Quick start script
- **MCP_SETUP.md** - Detailed setup and configuration guide
- **QUICK_START_MCP.md** - Quick reference guide
- **MCP_IMPLEMENTATION_SUMMARY.md** - Complete implementation details
- **README.md** - This file

## Configuration for Cursor

Add to your Cursor MCP settings:

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

Restart Cursor after adding the configuration.

## Available Tools

1. **repyv2_health_check** - Check if the remote server is available
2. **repyv2_execute** - Execute security layer with raw code strings
3. **repyv2_execute_files** - Execute security layer using file paths (easiest)

## Usage with AI Assistant

Once configured, ask your AI assistant:
- "Check if the RepyV2 server is available"
- "Test sample_monitor.py with sample_attack.py"
- "Execute my security layer and show me the results"

## Documentation

- See [QUICK_START_MCP.md](QUICK_START_MCP.md) for quick reference
- See [MCP_SETUP.md](MCP_SETUP.md) for detailed setup instructions
- See [MCP_IMPLEMENTATION_SUMMARY.md](MCP_IMPLEMENTATION_SUMMARY.md) for complete details
- See [../README.md](../README.md) for project overview

## Dependencies

```bash
pip install requests mcp
```

Both dependencies are already installed at `/Users/lishuyu/miniconda3/bin/python`.

## Architecture

```
Cursor IDE (AI) 
    ↓ MCP Protocol (stdio)
mcp_server.py (this folder)
    ↓ HTTP POST
Docker Server (100.88.83.27:8000)
    ↓ RepyV2 Execution
Results back to AI
```

## Support

For issues or questions, refer to the documentation files in this folder or the main project README.

