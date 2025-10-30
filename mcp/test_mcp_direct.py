#!/usr/bin/env python3
"""
Direct test of MCP server functions (without JSON-RPC layer)
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP server functions directly
from mcp_server import health_check, execute_security_layer, read_file_content


def test_health_check():
    """Test the health check function."""
    print("Testing health_check()...")
    result = health_check()
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    return result['status'] == 'ok'


def test_execute_files():
    """Test executing security layer files."""
    print("\nTesting execute_security_layer with files...")
    
    try:
        # Read the files (from parent directory)
        monitor_text = read_file_content("../sample_monitor.py")
        attack_text = read_file_content("../sample_attack.py")
        
        print(f"  Monitor file: sample_monitor.py ({len(monitor_text)} chars)")
        print(f"  Attack file: sample_attack.py ({len(attack_text)} chars)")
        
        # Execute
        print("  Executing...")
        result = execute_security_layer(monitor_text, attack_text)
        
        # Exit code 143 is expected for RepyV2
        exit_code = result.get('exit_code')
        stdout = result.get('stdout', '')
        
        print(f"  Exit code: {exit_code}")
        print(f"  Stdout length: {len(stdout)} chars")
        
        if result.get('note'):
            print(f"  Note: {result.get('note')}")
        
        if result.get('success'):
            print(f"  ✓ Execution successful!")
            print(f"    Exit code: {result.get('exit_code')}")
            print(f"    Execution time: {result.get('execution_time', 'N/A')}s")
            
            stdout = result.get('stdout', '')
            if stdout:
                lines = stdout.strip().split('\n')
                print(f"    Output lines: {len(lines)}")
                
                # Check for test results
                if "PASSED" in stdout and "ERROR" not in stdout:
                    print(f"    Status: All tests PASSED ✓")
                    return True
                elif "ERROR" in stdout:
                    print(f"    Status: Some tests FAILED ✗")
                    print(f"    First few lines:")
                    for line in lines[:5]:
                        print(f"      {line}")
                    return False
                else:
                    print(f"    Status: Unknown")
                    print(f"    First few lines:")
                    for line in lines[:5]:
                        print(f"      {line}")
                    return True
        else:
            print(f"  ✗ Execution failed!")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            print(f"    Stderr: {result.get('stderr', '')}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False


def main():
    print("=" * 70)
    print("MCP Server Direct Function Test")
    print("=" * 70)
    
    results = []
    
    # Test 1: Health check
    try:
        results.append(("Health Check", test_health_check()))
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        results.append(("Health Check", False))
    
    # Test 2: Execute files
    try:
        results.append(("Execute Files", test_execute_files()))
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        results.append(("Execute Files", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

