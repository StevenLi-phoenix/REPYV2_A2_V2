#!/bin/bash
# Start the MCP server for RepyV2 testing

PYTHON_PATH="/Users/lishuyu/miniconda3/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER="${SCRIPT_DIR}/mcp_server.py"

echo "Starting RepyV2 MCP Server..."
echo "Python: ${PYTHON_PATH}"
echo "Script: ${MCP_SERVER}"
echo ""
echo "The server is running and waiting for MCP client connections via stdio."
echo "Press Ctrl+C to stop."
echo ""

exec "${PYTHON_PATH}" "${MCP_SERVER}"

