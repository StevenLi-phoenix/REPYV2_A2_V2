# Testing Guide for Versioned and Immutable File Security Layer

## Overview

This guide explains how to use the independent test cases in the `general_tests/` directory.

## Test Philosophy

### Silent Success
- **Passing tests produce NO output**
- Only errors are logged
- Exit code 143 is expected (RepyV2 SIGTERM)
- This follows the principle: "No news is good news"

### Independence
- Each test uses unique file names (testfile1, testfile2, etc.)
- Tests can be run in any order
- No dependencies between tests
- Isolated test environments

## Running Tests

### Run All Tests
```bash
./run_all_tests.sh
```

Expected output:
```
Running all test cases against sample_monitor.py...
==================================================
✓ test01_basic_versioning.r2py PASSED
✓ test02_file_in_use.r2py PASSED
✓ test03_no_explicit_version.r2py PASSED
...
==================================================
Results: 15 passed, 0 failed out of 15 tests
All tests passed!
```

### Run Individual Test
```bash
python repy.py restrictions.default encasementlib.r2py sample_monitor.py general_tests/test01_basic_versioning.r2py
```

Expected: No output (silent success)

### Using Remote Docker API (RepyV2-Testing MCP)

For ARM systems or when Python 2.7 is not available:

```python
from mcp_repyv2_testing import repyv2_execute_files

result = repyv2_execute_files(
    monitor_file="sample_monitor.py",
    attack_file="general_tests/test01_basic_versioning.r2py"
)

# Result:
# {
#   "success": false,  # False means no errors (counterintuitive but correct)
#   "exit_code": 143,  # Expected
#   "stdout": "",      # No output = passing test
#   "error": null
# }
```

## Test Descriptions

### Core Functionality Tests

**test01_basic_versioning.r2py**
- Tests basic version creation: base → v1 → v2
- Verifies content copying between versions
- File: testfile1

**test09_multiple_versions.r2py**
- Creates 5 versions (v1 through v5)
- Verifies base file immutability
- Checks accumulation in latest version
- File: testfile9

**test13_empty_file.r2py**
- Tests versioning of empty files
- Verifies empty content is preserved
- File: testfile13

### Security Tests

**test02_file_in_use.r2py**
- Prevents opening already-open files
- Expects FileInUseError
- File: testfile2

**test03_no_explicit_version.r2py**
- Blocks creating files like "file.v5"
- Expects RepyArgumentError
- File: testfile3.v5

**test04_immutable_old_versions.r2py**
- Enforces immutability after close
- Cannot write to old versions
- Expects FileInUseError on write
- File: testfile4

**test06_no_delete.r2py**
- Prevents file deletion
- Expects RepyArgumentError
- File: testfile6

**test10_concurrent_version.r2py**
- Prevents version creation while file is open
- Expects FileInUseError
- File: testfile10

**test11_version_readonly.r2py**
- Version files are read-only
- Cannot write to .v1, .v2, etc.
- File: testfile11

### Access Control Tests

**test05_read_old_versions.r2py**
- Verifies old versions are readable
- Tests both base and versioned files
- File: testfile5

**test08_file_not_found.r2py**
- Proper error handling for missing files
- Expects FileNotFoundError
- File: nonexistent_file_xyz

### Feature Tests

**test07_listfiles_filter.r2py**
- Version files hidden from listfiles()
- Only base files shown
- File: testfile7

**test12_dot_v_filename.r2py**
- Files like "file.version" are allowed
- Only "file.v[number]" pattern is filtered
- File: file.version

**test14_offset_writes.r2py**
- Tests writing at large offsets
- Verifies data preservation across versions
- File: testfile14

**test15_sequential_ops.r2py**
- Sequential write operations
- Read/write in same file handle
- File: testfile15

## Interpreting Results

### Success Indicators
- **No stdout output**
- **Exit code: 143** (SIGTERM from RepyV2)
- **No error messages**

### Failure Indicators
- **"ERROR: ..." in stdout**
- **Non-143 exit code** (rare)
- **Exception traceback**

### Example: Successful Test
```bash
$ python repy.py restrictions.default encasementlib.r2py sample_monitor.py general_tests/test01_basic_versioning.r2py
$ echo $?
143
# No output = test passed
```

### Example: Failed Test
```bash
$ python repy.py restrictions.default encasementlib.r2py bad_monitor.py general_tests/test04_immutable_old_versions.r2py
ERROR: Should not allow writing to old version
$ echo $?
1
```

## Creating New Tests

When creating new attack cases, follow this template:

```python
"""
Test Description: What this test verifies
"""

# Test code here
f1 = openfile("unique_filename", True)
# ... test logic ...

# On error, log and exit
if something_wrong:
    log("ERROR: Specific error message\n")
    exitall()

# On success: Do nothing (silent success)
```

**Key Points:**
1. Use unique file names
2. No output on success
3. Log errors explicitly
4. Call exitall() on failure
5. Document what you're testing

## Troubleshooting

### Test shows output but should pass
- Check if monitor is correct
- Verify file names are unique
- Look for logic errors in test

### Test hangs
- File might be left open
- Check for proper close() calls
- Monitor might have deadlock

### All tests fail
- Monitor implementation issue
- RepyV2 not properly installed
- Wrong Python version (need 2.7)

### ARM/M1 Mac issues
- Use remote Docker API
- Python 2.7 not available on ARM
- See MCP setup guide

## Best Practices

1. **Run all tests frequently** during development
2. **Fix tests immediately** if they break
3. **Keep tests independent** - no shared state
4. **Use descriptive error messages** in log()
5. **Test edge cases** not just happy paths
6. **Document test purpose** in docstring

## Reference

For more details, see:
- `general_tests/README.md` - Test case listing
- `README.md` - Project overview
- `instruction.md` - Assignment requirements
- `mcp/MCP_SETUP.md` - Remote testing setup

