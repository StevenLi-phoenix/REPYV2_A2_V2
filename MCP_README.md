# MCP Server - Quick Reference

All MCP-related files have been organized in the `mcp/` folder.

## Quick Test

```bash
cd mcp
/Users/lishuyu/miniconda3/bin/python test_mcp_direct.py
```

Expected: **2/2 tests passed ✓**

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

Then restart Cursor.

## Usage

Ask your AI assistant:
- "Check if the RepyV2 server is available"
- "Test sample_monitor.py with sample_attack.py"

## Documentation

- See [mcp/README.md](mcp/README.md) for MCP folder overview
- See [mcp/QUICK_START_MCP.md](mcp/QUICK_START_MCP.md) for quick start guide
- See [mcp/MCP_SETUP.md](mcp/MCP_SETUP.md) for detailed setup
- See [mcp/MCP_IMPLEMENTATION_SUMMARY.md](mcp/MCP_IMPLEMENTATION_SUMMARY.md) for complete details

