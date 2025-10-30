# RepyV2 Versioned and Immutable File Security Layer

A comprehensive defensive security system implementation for RepyV2 that enforces immutable, versioned files with tamper-proof history for auditing and recovery.

## Overview

This project implements a reference monitor (security layer) for the Seattle Testbed's RepyV2 platform. The security layer provides:

- **Immutability**: Once a file version is closed, it cannot be changed or deleted
- **Versioning**: Automatic creation of new file versions with preserved history
- **Access Control**: Read-only access to old versions, write access only to current version
- **Audit Trail**: Complete history of file modifications through version tracking

## Project Structure

```
REPYV2_A2_V2/
├── sample_monitor.py              # Correct security layer implementation
├── sample_attack.py                # Legacy comprehensive test suite
├── sample_incorrect_monitor.py     # Intentionally flawed monitor for testing
├── sample_incorrect_attack.py      # Attack cases to expose security flaws
├── general_tests/                  # Independent test cases (15 files)
│   ├── README.md                   # Test case documentation
│   ├── test01_basic_versioning.r2py
│   ├── test02_file_in_use.r2py
│   └── ... (13 more test files)
├── run_all_tests.sh                # Script to run all tests
├── post.py                         # API testing script
├── post.sh                         # Shell script for API testing
├── requirements.txt                # Python dependencies
├── instruction.md                  # Assignment instructions
├── Assignment_2.1/                 # Additional test cases (99 files)
└── mcp/                            # MCP server for AI-powered testing
    ├── mcp_server.py               # MCP server implementation
    ├── mcp_config.json             # MCP server configuration
    ├── test_mcp_direct.py          # Direct function test script
    ├── test_mcp_server.py          # JSON-RPC test script
    ├── start_mcp_server.sh         # Quick start script
    ├── MCP_SETUP.md                # Detailed setup guide
    ├── QUICK_START_MCP.md          # Quick reference
    └── MCP_IMPLEMENTATION_SUMMARY.md  # Implementation details
```

## Files Description

### Core Implementation

#### `sample_monitor.py`
The complete, secure reference monitor implementation that enforces all specifications:
- Global state tracking for open and closed files
- Automatic version numbering (v1, v2, v3, etc.)
- Immutability enforcement after file closure
- Prevention of unauthorized operations (file deletion, explicit version creation)
- Filtered file listing (hides version files)

**Key Features:**
- Prevents opening already-open files
- Blocks writing to old/closed versions
- Creates new versions automatically when reopening existing files
- Tracks file state across operations
- Enforces all error conditions correctly

#### `sample_attack.py` (Legacy)
Legacy comprehensive test suite with all 15 tests in one file. For production testing, use the independent test cases in `general_tests/` instead.

#### `general_tests/` Directory
Contains 15 independent test cases, each testing a specific aspect:
1. **test01_basic_versioning.r2py** - Basic file creation and versioning
2. **test02_file_in_use.r2py** - Preventing double-open operations
3. **test03_no_explicit_version.r2py** - Blocking explicit version file creation
4. **test04_immutable_old_versions.r2py** - Enforcing immutability on old versions
5. **test05_read_old_versions.r2py** - Allowing reads from old versions
6. **test06_no_delete.r2py** - Preventing file deletion
7. **test07_listfiles_filter.r2py** - Filtering version files from listings
8. **test08_file_not_found.r2py** - Proper error handling (FileNotFoundError)
9. **test09_multiple_versions.r2py** - Multiple version creation (v1-v5)
10. **test10_concurrent_version.r2py** - Preventing version creation while file is open
11. **test11_version_readonly.r2py** - Version files as read-only
12. **test12_dot_v_filename.r2py** - Handling files with ".v" in name
13. **test13_empty_file.r2py** - Empty file versioning
14. **test14_offset_writes.r2py** - Large offset operations
15. **test15_sequential_ops.r2py** - Sequential read/write operations

**Key Features:**
- Each test is independent (uses unique file names)
- Tests produce NO output on success (silent success)
- Only output errors if the monitor fails
- Exit code 143 is expected (RepyV2 termination)

### Testing & Validation

#### `sample_incorrect_monitor.py`
An intentionally flawed implementation demonstrating common security mistakes:
- Does not track open files properly
- Allows writing to old versions (breaks immutability)
- Permits file deletion
- Exposes version files in listings
- Only handles v1, fails with v2, v3, etc.
- Allows explicit version file creation
- Poor error handling

**Purpose:** Educational tool to understand security vulnerabilities.

#### `sample_incorrect_attack.py`
Attack test cases that expose security flaws:
1. Opening already-open files
2. Writing to old versions
3. Deleting files
4. Information leaks (version files visible)
5. Version confusion attacks
6. Version tracking failures
7. Race conditions
8. History tampering
9. Error handling exploits

**Usage:**
- Run against `sample_incorrect_monitor.py`: See "SUCCESS" (flaws exposed)
- Run against `sample_monitor.py`: See "BLOCKED" (secure implementation)

### API Testing

#### `post.py`
Python script for testing the security layer via FastAPI:
```python
# Tests the monitor by sending it to a remote API
base_url = "http://100.88.83.27:8000"
```

**Features:**
- Health check endpoint testing
- Execute endpoint with monitor and attack code
- Pretty-printed JSON responses
- Error handling for connection issues

**Requirements:**
```bash
pip install requests
```

**Usage:**
```bash
python3 post.py
```

### MCP Server (AI-Powered Testing)

#### `mcp/` folder
MCP (Model Context Protocol) server that exposes RepyV2 testing functionality as tools for AI assistants.

**Features:**
- Three MCP tools: `repyv2_health_check`, `repyv2_execute`, `repyv2_execute_files`
- Enables AI assistants (Claude, Cursor) to test security layers
- Natural language testing interface
- Automatic HTTP API integration

**Setup:**
```bash
pip install requests mcp
```

**Configuration:**
Add to your Cursor/Claude Desktop MCP settings:
```json
{
  "mcpServers": {
    "repyv2-testing": {
      "command": "/Users/lishuyu/miniconda3/bin/python",
      "args": ["/Users/lishuyu/Codes/REPYV2_A2_V2/mcp/mcp_server.py"]
    }
  }
}
```

**Usage:**
```bash
cd mcp

# Start manually
/Users/lishuyu/miniconda3/bin/python mcp_server.py

# Or use quick start script
./start_mcp_server.sh

# Test the server
/Users/lishuyu/miniconda3/bin/python test_mcp_direct.py
```

**AI Assistant Examples:**
- "Check if the RepyV2 server is available"
- "Test sample_monitor.py with sample_attack.py"
- "Execute this security layer code with these test cases"

For detailed setup instructions, see [mcp/MCP_SETUP.md](mcp/MCP_SETUP.md)

## How to Run

### Prerequisites

1. **Python 2.7** (for RepyV2)
2. **RepyV2** installed from [SeattleTestbed](https://github.com/SeattleTestbed)
3. Required files: `repy.py`, `restrictions.default`, `encasementlib.r2py`

### ARM Architecture Compatibility Note

**Important:** Python 2.7 is not natively supported on modern ARM-based chips (Apple Silicon M1/M2/M3, ARM64 systems). 

To work around this limitation, this project uses a **Docker-based remote execution server** that runs on x86 architecture. The execution flow is:

1. Code runs on your ARM machine (M1/M2/M3 Mac, etc.)
2. `post.py` sends the security layer and test code to a remote Docker container
3. Docker container (x86) executes RepyV2 with Python 2.7
4. Results are sent back to your local machine

This allows seamless testing without needing to set up Python 2.7 locally on ARM systems.

### Running Tests Locally (x86 Systems Only)

**Note:** This method only works on x86 systems with Python 2.7 installed. For ARM systems, use the remote execution method below.

#### Test all independent test cases:
```bash
./run_all_tests.sh
```
**Expected:** All 15 tests pass with no output (silent success)

#### Test a single test case:
```bash
python2 repy.py restrictions.default encasementlib.r2py sample_monitor.py general_tests/test01_basic_versioning.r2py
```
**Expected:** No output (silent success), exit code 143

#### Test the legacy comprehensive suite:
```bash
python2 repy.py restrictions.default encasementlib.r2py sample_monitor.py sample_attack.py
```
**Expected:** All tests PASS (legacy version shows output)

#### Test the incorrect monitor with attack cases:
```bash
python2 repy.py restrictions.default encasementlib.r2py sample_incorrect_monitor.py sample_incorrect_attack.py
```
**Expected:** Multiple "SUCCESS" messages showing security flaws

#### Test the correct monitor against attacks:
```bash
python2 repy.py restrictions.default encasementlib.r2py sample_monitor.py sample_incorrect_attack.py
```
**Expected:** All "BLOCKED" messages showing proper security

### Testing via Remote Docker API (Recommended for ARM Systems)

Since ARM chips (Apple Silicon M1/M2/M3, ARM64) don't support Python 2.7, we use a remote Docker execution server running on x86 architecture.

#### Setup

1. Ensure you have Python 3 installed locally
2. Install required dependencies:
```bash
pip3 install requests
```

#### Running Tests

The `post.py` script automatically sends your security layer and test code to the remote Docker server for execution:

```bash
python3 post.py
```

Or use the shell script:
```bash
./post.sh
```

#### What `post.py` Does

```python
# Reads the monitor and attack files
monitor_text = open("sample_incorrect_monitor.py", "r").read()
attack_text = open("sample_attack.py", "r").read()

# Sends to remote Docker server at http://100.88.83.27:8000
response = requests.post(f"{base_url}/execute", json={
    "monitor_text": monitor_text,
    "attack_text": attack_text
})

# Displays the execution results
print(response.json().get("stdout"))
```

#### Customizing Test Execution

Edit `post.py` to test different combinations:

```python
# Test correct monitor with comprehensive tests
monitor_text = open("sample_monitor.py", "r").read()
attack_text = open("sample_attack.py", "r").read()

# Test incorrect monitor with attack cases
monitor_text = open("sample_incorrect_monitor.py", "r").read()
attack_text = open("sample_incorrect_attack.py", "r").read()
```

#### Server Response Format

```json
{
  "success": true,
  "stdout": "Test 1: PASSED\nTest 2: PASSED\n...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.234
}
```

## Security Specifications

### Enforced Rules

1. **Versioning**
   - First file: `filename`
   - Subsequent versions: `filename.v1`, `filename.v2`, `filename.v3`, etc.
   - New version created automatically when `openfile(filename, True)` on existing file

2. **Immutability**
   - Once a file is closed, it becomes permanently read-only
   - Any write attempts raise `FileInUseError`
   - Deletion attempts raise `RepyArgumentError`

3. **Access Control**
   - Cannot open already-open files → `FileInUseError`
   - Cannot create explicit version files → `RepyArgumentError`
   - Cannot create new version while latest is open → `FileInUseError`
   - Non-existent files with `create=False` → `FileNotFoundError`

4. **Information Control**
   - `listfiles()` shows only base files, not version files
   - Version files hidden to prevent information leakage

### Error Types

- `FileInUseError`: File already open, or writing to old version
- `RepyArgumentError`: Invalid operations (explicit version creation, file deletion)
- `FileNotFoundError`: Opening non-existent file with `create=False`

## Design Paradigms

### Accuracy
All unspecified actions behave exactly as in the underlying RepyV2 API. Only the specified behaviors are modified.

### Efficiency
- No unnecessary file caching
- Minimal memory usage
- Copy-on-write only when creating new versions
- Efficient state tracking with dictionaries

### Security
- Tamper-proof version history
- No bypass mechanisms
- Robust error handling
- Complete audit trail preservation

## Test Output Examples

### Successful Test (Correct Monitor)
```
Test 1: Basic file creation and versioning
Test 1 PASSED

Test 2: Cannot open already-open files
Test 2 PASSED - FileInUseError raised correctly

...

=== ALL TESTS PASSED ===
```

### Failed Test (Incorrect Monitor)
```
Attack 1: Opening already-open file
SUCCESS - Incorrect monitor allows opening already-open file (SECURITY FLAW)

Attack 2: Writing to old version
SUCCESS - Incorrect monitor allows writing to old version (IMMUTABILITY BROKEN)

...
```

## Batch Testing Multiple Monitors

### Local Testing (x86 Systems Only)

#### Linux/Mac (Bash):
```bash
for referencemonitor in reference_monitor_*; do 
    echo "$referencemonitor under test"
    for testcase in sample_attack*.py; do 
        python2 repy.py restrictions.default encasementlib.r2py $referencemonitor $testcase
    done
done
```

#### Windows (PowerShell):
```powershell
foreach ($referencemonitor in Get-ChildItem reference_monitor_*) { 
    Write-Host $referencemonitor.Name
    foreach ($testcase in Get-ChildItem sample_attack*.py) { 
        python2 repy.py restrictions.default encasementlib.r2py $referencemonitor.Name $testcase.Name 
    } 
}
```

### Remote Testing (ARM-Compatible)

Create a Python script for batch testing via the Docker API:

```python
import requests
import glob

base_url = "http://100.88.83.27:8000"

# Get all reference monitors and test cases
monitors = glob.glob("reference_monitor_*.py")
testcases = glob.glob("*_attackcase*.py")

results = []

for monitor_file in monitors:
    print(f"\nTesting {monitor_file}...")
    
    with open(monitor_file) as f:
        monitor_text = f.read()
    
    for testcase_file in testcases:
        with open(testcase_file) as f:
            attack_text = f.read()
        
        response = requests.post(
            f"{base_url}/execute",
            json={"monitor_text": monitor_text, "attack_text": attack_text}
        )
        
        result = response.json()
        if not result["success"] or result["stdout"]:
            print(f"  FAILED: {testcase_file}")
            results.append({
                "monitor": monitor_file,
                "testcase": testcase_file,
                "output": result["stdout"],
                "error": result["stderr"]
            })
        else:
            print(f"  PASSED: {testcase_file}")

print(f"\n\nSummary: {len(results)} failures found")
for r in results:
    print(f"  {r['monitor']} failed on {r['testcase']}")
```

## Docker Remote Execution Server

### Why Docker Remote Execution?

Modern ARM-based systems (Apple Silicon M1/M2/M3, ARM64 processors) cannot run Python 2.7 natively due to architecture incompatibility. The Docker remote execution server solves this by:

1. **Running on x86 architecture** in a Docker container
2. **Providing a REST API** for code submission and execution
3. **Returning results** to the ARM client machine
4. **No local Python 2.7 setup required** on ARM systems

### Server Architecture

```
┌─────────────────┐         HTTP POST          ┌──────────────────┐
│   ARM Machine   │ ────────────────────────> │  Docker Server   │
│  (M1/M2/M3 Mac) │                            │  (x86 Container) │
│                 │                            │                  │
│   post.py       │                            │  FastAPI +       │
│   (Python 3)    │                            │  RepyV2 +        │
│                 │                            │  Python 2.7      │
│                 │ <──────────────────────── │                  │
└─────────────────┘    JSON Response          └──────────────────┘
```

### API Endpoints

#### Health Check
```http
GET http://100.88.83.27:8000/health

Response:
{
  "status": "ok",
  "message": "RepyV2 execution server is running"
}
```

#### Execute Security Layer
```http
POST http://100.88.83.27:8000/execute
Content-Type: application/json

Body:
{
  "monitor_text": "<security layer code as string>",
  "attack_text": "<test case code as string>"
}

Response:
{
  "success": true,
  "stdout": "Test 1 PASSED\nTest 2 PASSED\n...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.234
}
```

### Using the API Directly

#### With curl:
```bash
curl -X POST http://100.88.83.27:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "monitor_text": "'"$(cat sample_monitor.py)"'",
    "attack_text": "'"$(cat sample_attack.py)"'"
  }'
```

#### With Python requests:
```python
import requests

with open("sample_monitor.py") as f:
    monitor = f.read()
with open("sample_attack.py") as f:
    attack = f.read()

response = requests.post(
    "http://100.88.83.27:8000/execute",
    json={"monitor_text": monitor, "attack_text": attack}
)

print(response.json()["stdout"])
```

### Benefits of This Approach

✅ **ARM Compatible** - Works on Apple Silicon and ARM64 systems  
✅ **No Local Setup** - No need to install Python 2.7 or RepyV2  
✅ **Consistent Environment** - Docker ensures reproducible execution  
✅ **Easy Testing** - Simply run `python3 post.py`  
✅ **Fast Feedback** - Get results in seconds  
✅ **Multiple Tests** - Test different monitor/attack combinations easily

## Development Notes

### Important Reminders

1. **No output in production**: Reference monitors must produce NO output when working correctly
2. **Remove debug logs**: All `log()` statements must be removed before submission
3. **Independent tests**: Each test file should be independent and self-contained
4. **Error suppression**: Expected errors should be caught and suppressed in tests

### Common Pitfalls

- Not tracking file state globally
- Allowing multiple opens of same file
- Not enforcing immutability after close
- Forgetting to handle version numbering beyond v1
- Not filtering version files from `listfiles()`
- Poor error handling and wrong exception types

## References

- [RepyV2 API Documentation](https://github.com/SeattleTestbed/docs/blob/master/Programming/RepyV2API.md)
- [Python vs RepyV2 Differences](https://github.com/SeattleTestbed/docs/blob/master/Programming/PythonVsRepyV2.md)
- [Seattle Security Layers Paper](https://ssl.engineering.nyu.edu/papers/cappos_seattle_ccs_10.pdf)
- [Build Instructions](https://github.com/SeattleTestbed/docs/blob/master/Contributing/BuildInstructions.md)

## License

This is an educational project for security layer implementation and testing.

## Author

Created for RepyV2 Security Layer Assignment - Immutable and Versioned File System

