# Quick Start Guide - MCP Server

## What Was Added

An MCP (Model Context Protocol) server has been added to this project, enabling AI assistants like Claude and Cursor to test RepyV2 security layers through natural language commands.

## Files in mcp/ Folder

- `mcp_server.py` - The MCP server implementation
- `mcp_config.json` - Configuration for Cursor/Claude Desktop
- `test_mcp_direct.py` - Direct function test script
- `test_mcp_server.py` - JSON-RPC test script
- `start_mcp_server.sh` - Quick start shell script
- `MCP_SETUP.md` - Detailed setup instructions
- `QUICK_START_MCP.md` - This file
- `MCP_IMPLEMENTATION_SUMMARY.md` - Complete implementation details

## Quick Test

Verify the MCP server works:

```bash
cd /Users/lishuyu/Codes/REPYV2_A2_V2/mcp
/Users/lishuyu/miniconda3/bin/python test_mcp_direct.py
```

Expected output:
```
======================================================================
MCP Server Direct Function Test
======================================================================
Testing health_check()...
  Status: ok
  Message: RepyV2 execution server is available

Testing execute_security_layer with files...
  Monitor file: sample_monitor.py (7609 chars)
  Attack file: sample_attack.py (7174 chars)
  Executing...
  Exit code: 143
  Stdout length: 6584 chars
  Note: Exit code 143 (SIGTERM) is expected for RepyV2 execution
  ✓ Execution successful!
    Exit code: 143
    Execution time: N/As
    Output lines: 72
    Status: All tests PASSED ✓

======================================================================
Test Summary
======================================================================
  Health Check: ✓ PASSED
  Execute Files: ✓ PASSED

Total: 2/2 tests passed
```

## Setup for Cursor IDE

1. **Verify dependencies are installed:**
   ```bash
   /Users/lishuyu/miniconda3/bin/python -m pip install requests mcp
   ```

2. **Add MCP server to Cursor settings:**
   
   Open Cursor settings and add this MCP server configuration:
   
   ```json
   {
     "mcpServers": {
       "repyv2-testing": {
         "command": "/Users/lishuyu/miniconda3/bin/python",
         "args": [
           "/Users/lishuyu/Codes/REPYV2_A2_V2/mcp/mcp_server.py"
         ],
         "env": {}
       }
     }
   }
   ```

3. **Restart Cursor** to load the MCP server

4. **Test it by asking Cursor:**
   - "Check if the RepyV2 server is available"
   - "Test sample_monitor.py with sample_attack.py"
   - "Execute the security layer and show me the results"

## Available MCP Tools

### 1. `repyv2_health_check`
Check if the remote RepyV2 execution server is available.

**No parameters required**

### 2. `repyv2_execute`
Execute security layer code directly (provide code as strings).

**Parameters:**
- `monitor_text` - The security layer code
- `attack_text` - The test case code

### 3. `repyv2_execute_files`
Execute security layer using file paths (easiest to use).

**Parameters:**
- `monitor_file` - Path to monitor file (e.g., "sample_monitor.py")
- `attack_file` - Path to attack file (e.g., "sample_attack.py")

## Usage Examples with AI Assistant

Once configured, you can interact with the MCP server through natural language:

**Example 1: Health Check**
```
You: "Is the RepyV2 server available?"
AI: [Calls repyv2_health_check] "Yes, the server is available and responding."
```

**Example 2: Test Security Layer**
```
You: "Test sample_monitor.py against sample_attack.py"
AI: [Calls repyv2_execute_files] "All tests passed! The security layer correctly..."
```

**Example 3: Debug Failures**
```
You: "What's wrong with my monitor? Test it with the attack file."
AI: [Calls repyv2_execute_files] "Test 5 failed because..."
```

## Architecture

```
┌─────────────────────┐
│   Cursor IDE        │
│   (Your AI)         │
└──────────┬──────────┘
           │ MCP Protocol
           │ (stdio/JSON-RPC)
           │
┌──────────▼──────────┐
│   mcp_server.py     │
│  (This computer)    │
└──────────┬──────────┘
           │ HTTP POST
           │
┌──────────▼──────────┐
│  Docker Server      │
│  100.88.83.27:8000  │
│  RepyV2 + Python2.7 │
└─────────────────────┘
```

## Important Notes

1. **Exit Code 143 is Normal**: RepyV2 execution returns exit code 143 (SIGTERM), which is expected behavior. The MCP server handles this correctly.

2. **Network Required**: The MCP server needs network access to communicate with the remote Docker execution server at `http://100.88.83.27:8000`.

3. **Python Path**: The configuration uses `/Users/lishuyu/miniconda3/bin/python`. Update this path if your Python installation is elsewhere.

4. **File Paths**: When using `repyv2_execute_files`, provide paths relative to the project directory or absolute paths.

## Troubleshooting

### "mcp module not found"
```bash
/Users/lishuyu/miniconda3/bin/python -m pip install mcp
```

### "Connection refused"
Check if the remote server is accessible:
```bash
curl http://100.88.83.27:8000/health
```

### "Tool not appearing in Cursor"
1. Check MCP configuration is correct
2. Restart Cursor completely
3. Check Cursor logs for MCP errors

## Next Steps

- See [MCP_SETUP.md](MCP_SETUP.md) for detailed configuration
- See [README.md](../README.md) for project overview
- Test with: `cd /Users/lishuyu/Codes/REPYV2_A2_V2/mcp && /Users/lishuyu/miniconda3/bin/python test_mcp_direct.py`

## Benefits

✅ Natural language testing interface  
✅ No manual API calls needed  
✅ AI-powered debugging assistance  
✅ Integrated with Cursor workflow  
✅ Instant feedback on security layers  
✅ Works on ARM (M1/M2/M3) Macs

