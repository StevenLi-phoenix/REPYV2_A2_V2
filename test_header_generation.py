#!/usr/bin/env python3
"""
Test script to verify the new attack case header generation.
Creates a sample attack case with comprehensive header to verify format.
"""
import sys
import os

# Add the current directory to the path to import from run_all_tests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_all_tests import create_attack_case_with_header, compute_md5

# Sample execution info
execution_info = {
    "start_time": "2025-10-27T10:30:15.123456",
    "end_time": "2025-10-27T10:30:18.456789",
    "duration": 3.333333,
    "stdout": "ERROR: Should not allow writing to old version\n",
    "stderr": "",
    "exit_code": 0,
    "monitor_md5": "abc123def456789012345678901234",
    "attack_md5": "def456789012345678901234567890",
}

# Test with an existing test file
test_file = "submit/general_tests/test04_immutable_old_versions.r2py"
output_file = "test_sample_attack_with_header.r2py"

if os.path.exists(test_file):
    create_attack_case_with_header(
        original_test_file=test_file,
        output_path=output_file,
        netid="test_netid",
        test_name="test04_immutable_old_versions.r2py",
        execution_info=execution_info,
        error="ERROR: Should not allow writing to old version"
    )
    
    print("✓ Sample attack case created successfully!")
    print(f"✓ Output file: {output_file}")
    print("\nPreview of generated header:\n")
    print("=" * 80)
    
    with open(output_file, 'r') as f:
        content = f.read()
        # Print first 50 lines or until we hit the code
        lines = content.split('\n')
        for i, line in enumerate(lines[:60]):
            print(line)
            if i > 0 and line.strip().startswith('f1 = openfile'):
                print("\n... (rest of code) ...")
                break
    
    print("\n" + "=" * 80)
else:
    print(f"❌ Test file not found: {test_file}")
    sys.exit(1)

