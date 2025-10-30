#!/usr/bin/env python3
"""
Test script for the MCP server
Tests the MCP server functionality without needing a full MCP client
"""
import subprocess
import json
import sys


def test_mcp_server():
    """Test the MCP server by sending JSON-RPC messages via stdin."""
    
    print("Testing MCP Server...")
    print("=" * 60)
    
    # Test 1: List tools
    print("\n1. Testing tools/list...")
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    try:
        result = subprocess.run(
            ["/Users/lishuyu/miniconda3/bin/python", "mcp_server.py"],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse the response
        lines = result.stdout.strip().split('\n')
        for line in lines:
            try:
                response = json.loads(line)
                if "result" in response:
                    print("✓ Available tools:")
                    for tool in response["result"]:
                        print(f"  - {tool['name']}: {tool['description']}")
                    break
            except json.JSONDecodeError:
                continue
        
    except subprocess.TimeoutExpired:
        print("✗ Timeout waiting for response")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Health check
    print("\n2. Testing repyv2_health_check...")
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "repyv2_health_check",
            "arguments": {}
        },
        "id": 2
    }
    
    try:
        result = subprocess.run(
            ["/Users/lishuyu/miniconda3/bin/python", "mcp_server.py"],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse the response
        lines = result.stdout.strip().split('\n')
        for line in lines:
            try:
                response = json.loads(line)
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    health_data = json.loads(content)
                    if health_data["status"] == "ok":
                        print(f"✓ Server is available: {health_data['message']}")
                    else:
                        print(f"✗ Server error: {health_data['message']}")
                    break
            except (json.JSONDecodeError, KeyError):
                continue
        
    except subprocess.TimeoutExpired:
        print("✗ Timeout waiting for response")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Execute files
    print("\n3. Testing repyv2_execute_files...")
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "repyv2_execute_files",
            "arguments": {
                "monitor_file": "sample_monitor.py",
                "attack_file": "sample_attack.py"
            }
        },
        "id": 3
    }
    
    try:
        result = subprocess.run(
            ["/Users/lishuyu/miniconda3/bin/python", "mcp_server.py"],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse the response
        lines = result.stdout.strip().split('\n')
        for line in lines:
            try:
                response = json.loads(line)
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    exec_data = json.loads(content)
                    if exec_data.get("success"):
                        print(f"✓ Execution successful!")
                        print(f"  Exit code: {exec_data.get('exit_code', 'N/A')}")
                        print(f"  Execution time: {exec_data.get('execution_time', 'N/A')}s")
                        stdout = exec_data.get('stdout', '')
                        if stdout:
                            lines_count = len(stdout.strip().split('\n'))
                            print(f"  Output lines: {lines_count}")
                            if "PASSED" in stdout:
                                print(f"  Status: Tests PASSED ✓")
                            elif "ERROR" in stdout or "FAILED" in stdout:
                                print(f"  Status: Tests FAILED ✗")
                    else:
                        print(f"✗ Execution failed: {exec_data.get('error', 'Unknown error')}")
                    break
            except (json.JSONDecodeError, KeyError):
                continue
        
    except subprocess.TimeoutExpired:
        print("✗ Timeout waiting for response")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("MCP Server test complete!")


if __name__ == "__main__":
    test_mcp_server()

