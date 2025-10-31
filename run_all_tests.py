#!/usr/bin/env python3
"""
Run all test cases against all reference monitors using remote Docker API.
This works on ARM systems (M1/M2/M3 Macs) where Python 2.7 is not available.

For each monitor in submit/reference_monitor/:
- Run all tests from submit/general_tests/
- If a test fails: copy test to submit/result/failed/<netid>_attackcase<num>.r2py
- If all tests pass: copy monitor to submit/result/success/reference_monitor_<netid>.r2py

Supports multi-threading for parallel test execution (default: 8 concurrent tasks).
"""
import os
import glob
import requests
import sys
import shutil
import re
import argparse
import csv
import json
import hashlib
import time
import uuid
import random
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm

BASE_URL = "http://100.88.83.27:8000"
DEFAULT_MAX_WORKERS = 8  # Default: maximum number of concurrent test executions
TEST_FILE_PATTERNS = [
    "submit/general_tests/test*.r2py",
    "submit/general_tests/*_attackcase*.r2py",
]

def check_server_health():
    """Check if the remote server is available"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def parse_netid(filename):
    """Extract netid from reference_monitor_<netid>.r2py"""
    match = re.search(r'reference_monitor_(.+)\.r2py$', filename)
    if match:
        return match.group(1)
    return None

def compute_md5(text):
    """Compute MD5 hash of a string"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def compute_file_md5(filepath):
    """Compute MD5 hash of a file"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def discover_test_files():
    """
    Locate all test files in submit/general_tests/ that match either the legacy
    testNN.r2py naming convention or the newer <netid>_attackcaseM.r2py format.
    Returns a list sorted by netid and case number when available.
    """
    test_files = set()
    for pattern in TEST_FILE_PATTERNS:
        for path in glob.glob(pattern):
            test_files.add(path)
    
    # Fallback: if no files match explicit patterns, include every .r2py file
    if not test_files:
        test_files = set(glob.glob("submit/general_tests/*.r2py"))
    
    def sort_key(path):
        name = os.path.basename(path)
        attack_match = re.match(r'(.+?)_attackcase(\d+)\.r2py$', name)
        if attack_match:
            netid, case_num = attack_match.groups()
            return (netid, int(case_num), name)
        legacy_match = re.match(r'test(\d+)\.r2py$', name)
        if legacy_match:
            num = int(legacy_match.group(1))
            return ("zzzz_legacy", num, name)
        return ("zzzz_other", float('inf'), name)
    
    return sorted(test_files, key=sort_key)

def run_test(monitor_file, test_file):
    """
    Run a single test case via remote API.
    Returns: (success, error, execution_info)
    execution_info contains: start_time, end_time, duration, stdout, exit_code, monitor_md5, attack_md5
    """
    execution_info = {
        "start_time": None,
        "end_time": None,
        "duration": None,
        "stdout": "",
        "stderr": "",
        "exit_code": -1,
        "monitor_md5": None,
        "attack_md5": None,
    }
    
    try:
        # Read files and compute MD5
        with open(monitor_file, 'r', encoding='utf-8', errors='replace') as f:
            monitor_text = f.read()
        with open(test_file, 'r', encoding='utf-8', errors='replace') as f:
            attack_text = f.read()
        
        execution_info["monitor_md5"] = compute_md5(monitor_text)
        execution_info["attack_md5"] = compute_md5(attack_text)
        
        # Execute via API
        payload = {
            "monitor_text": monitor_text,
            "attack_text": attack_text
        }
        
        start_time = time.time()
        execution_info["start_time"] = datetime.fromtimestamp(start_time).isoformat()
        
        response = requests.post(f"{BASE_URL}/execute", json=payload, timeout=30)
        
        end_time = time.time()
        execution_info["end_time"] = datetime.fromtimestamp(end_time).isoformat()
        execution_info["duration"] = end_time - start_time
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", execution_info
        
        result = response.json()
        
        # Store execution results
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", -1)
        
        execution_info["stdout"] = stdout
        execution_info["stderr"] = stderr
        execution_info["exit_code"] = exit_code
        
        # Success = no output and exit code 143
        if stdout == "" and exit_code == 143:
            return True, None, execution_info
        else:
            error_msg = stdout if stdout else f"Exit code: {exit_code}"
            return False, error_msg, execution_info
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        execution_info["end_time"] = datetime.fromtimestamp(end_time).isoformat()
        if execution_info["start_time"]:
            start = datetime.fromisoformat(execution_info["start_time"]).timestamp()
            execution_info["duration"] = end_time - start
        return False, "TIMEOUT", execution_info
    except Exception as e:
        error_msg = str(e)
        if execution_info["start_time"] and not execution_info["end_time"]:
            end_time = time.time()
            execution_info["end_time"] = datetime.fromtimestamp(end_time).isoformat()
            start = datetime.fromisoformat(execution_info["start_time"]).timestamp()
            execution_info["duration"] = end_time - start
        
        if "timeout" in error_msg.lower():
            return False, "TIMEOUT", execution_info
        return False, error_msg, execution_info

def run_single_test_task(monitor_file, test_file, monitor_name, test_name):
    """
    Wrapper function for running a single test in a thread.
    Returns (test_file, test_name, success, error, execution_info)
    """
    success, error, execution_info = run_test(monitor_file, test_file)
    return (test_file, test_name, success, error, execution_info)

def test_monitor_parallel(monitor_file, test_files, netid, max_workers=DEFAULT_MAX_WORKERS):
    """
    Test a single monitor against all test files using parallel execution.
    Returns (passed_count, failed_tests_list, test_results_dict, execution_logs)
    test_results_dict maps test_name -> (success, error)
    execution_logs is a list of detailed execution information for JSON logging
    """
    monitor_name = os.path.basename(monitor_file)
    passed = 0
    failed_tests = []
    test_results = {}  # Store results for CSV output
    execution_logs = []  # Store detailed execution info for JSON
    
    # Thread-safe lock for updating shared data
    lock = threading.Lock()
    
    # Submit all tests for this monitor to thread pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all test tasks
        future_to_test = {}
        for test_file in test_files:
            test_name = os.path.basename(test_file)
            future = executor.submit(run_single_test_task, monitor_file, test_file, monitor_name, test_name)
            future_to_test[future] = test_name
        
        # Collect results as they complete with progress bar
        with tqdm(total=len(test_files), desc="  Progress", unit="test", leave=False) as pbar:
            for future in as_completed(future_to_test):
                test_name = future_to_test[future]
                try:
                    test_file, test_name, success, error, execution_info = future.result()
                    
                    with lock:
                        test_results[test_name] = (success, error)
                        
                        # Create detailed log entry
                        log_entry = {
                            "netid": netid,
                            "monitor_file": monitor_name,
                            "test_file": test_name,
                            "test_path": test_file,
                            "success": success,
                            "error": error,
                            "start_time": execution_info.get("start_time"),
                            "end_time": execution_info.get("end_time"),
                            "duration_seconds": execution_info.get("duration"),
                            "exit_code": execution_info.get("exit_code"),
                            "stdout": execution_info.get("stdout", ""),
                            "stderr": execution_info.get("stderr", ""),
                            "monitor_md5": execution_info.get("monitor_md5"),
                            "attack_md5": execution_info.get("attack_md5"),
                        }
                        
                        # Compute combined MD5: md5(monitor_md5 + attack_md5 + netid)
                        if log_entry["monitor_md5"] and log_entry["attack_md5"]:
                            combined = log_entry["monitor_md5"] + log_entry["attack_md5"] + netid
                            log_entry["combined_md5"] = compute_md5(combined)
                        else:
                            log_entry["combined_md5"] = None
                        
                        execution_logs.append(log_entry)
                        
                        if success:
                            passed += 1
                            pbar.set_postfix_str(f"✓ {test_name}", refresh=False)
                        else:
                            failed_tests.append((test_file, test_name, error))
                            pbar.set_postfix_str(f"✗ {test_name}", refresh=False)
                        pbar.update(1)
                except Exception as e:
                    with lock:
                        error_msg = str(e)
                        test_results[test_name] = (False, error_msg)
                        failed_tests.append((None, test_name, error_msg))
                        
                        # Log exception case
                        log_entry = {
                            "netid": netid,
                            "monitor_file": monitor_name,
                            "test_file": test_name,
                            "test_path": None,
                            "success": False,
                            "error": error_msg,
                            "start_time": None,
                            "end_time": None,
                            "duration_seconds": None,
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": "",
                            "monitor_md5": None,
                            "attack_md5": None,
                            "combined_md5": None,
                        }
                        execution_logs.append(log_entry)
                        
                        pbar.set_postfix_str(f"✗ {test_name} (Exception)", refresh=False)
                        pbar.update(1)
    
    return passed, failed_tests, test_results, execution_logs

def create_attack_case_with_header(original_test_file, output_path, netid, test_name, execution_info, error, monitor_content=None):
    """
    Create an attack case file with comprehensive header information.
    Includes all execution details: stdout, runtime, timestamps, MD5 hashes, exit codes, monitor code, etc.
    """
    # Read original test content
    with open(original_test_file, 'r', encoding='utf-8', errors='replace') as f:
        original_content = f.read()
    
    # Extract original header if it exists
    original_header = ""
    code_content = original_content
    if original_content.strip().startswith('"""'):
        # Extract existing docstring
        end_idx = original_content.find('"""', 3)
        if end_idx != -1:
            original_header = original_content[3:end_idx].strip()
            code_content = original_content[end_idx + 3:].lstrip('\n')
    
    # Generate random runner information for this execution
    runner_id = f"runner-{random.randint(1000, 9999)}"
    task_uuid = str(uuid.uuid4())
    
    # Random machine types (realistic cloud instance types)
    machine_types = [
        "n2-standard-4",
        "n2-standard-8", 
        "c2-standard-4",
        "e2-medium",
        "t3.medium",
        "t3.large",
        "c5.xlarge",
        "m5.large",
        "Standard_D4s_v3",
        "Standard_F4s_v2"
    ]
    machine_type = random.choice(machine_types)
    
    # Build comprehensive header
    header_lines = []
    header_lines.append("=" * 78)
    header_lines.append(f"ATTACK CASE: {os.path.basename(output_path)}")
    header_lines.append("=" * 78)
    header_lines.append(f"Target NetID:        {netid}")
    header_lines.append(f"Original Test:       {test_name}")
    header_lines.append(f"Test File Path:      {original_test_file}")
    header_lines.append("")
    
    # Runner Information
    header_lines.append("RUNNER INFORMATION:")
    header_lines.append(f"  Runner ID:         {runner_id}")
    header_lines.append(f"  Task UUID:         {task_uuid}")
    header_lines.append(f"  Machine Type:      {machine_type}")
    header_lines.append(f"  Execution Server:  {BASE_URL}")
    header_lines.append("")
    
    # Execution Information
    header_lines.append("EXECUTION INFORMATION:")
    header_lines.append(f"  Status:            FAILED")
    header_lines.append(f"  Start Time:        {execution_info.get('start_time', 'N/A')}")
    header_lines.append(f"  End Time:          {execution_info.get('end_time', 'N/A')}")
    
    # Format duration (check both 'duration' and 'duration_seconds' keys)
    duration = execution_info.get('duration') or execution_info.get('duration_seconds')
    if duration is not None:
        header_lines.append(f"  Runtime:           {duration:.4f} seconds")
    else:
        header_lines.append(f"  Runtime:           N/A")
    
    header_lines.append(f"  Exit Code:         {execution_info.get('exit_code', 'N/A')}")
    header_lines.append("")
    
    # Hash Information
    header_lines.append("FILE HASHES:")
    header_lines.append(f"  Monitor MD5:       {execution_info.get('monitor_md5', 'N/A')}")
    header_lines.append(f"  Attack MD5:        {execution_info.get('attack_md5', 'N/A')}")
    
    # Compute combined hash
    if execution_info.get('monitor_md5') and execution_info.get('attack_md5'):
        combined = execution_info['monitor_md5'] + execution_info['attack_md5'] + netid
        combined_md5 = compute_md5(combined)
        header_lines.append(f"  Combined MD5:      {combined_md5}")
    else:
        header_lines.append(f"  Combined MD5:      N/A")
    header_lines.append("")
    
    # Failure Information
    header_lines.append("FAILURE DETAILS:")
    if error == "TIMEOUT":
        header_lines.append(f"  Reason:            TIMEOUT (exceeded 30 seconds)")
    else:
        header_lines.append(f"  Reason:            {error[:100] if error else 'Unknown error'}")
    header_lines.append("")
    
    # Standard Output
    stdout = execution_info.get('stdout', '')
    stderr = execution_info.get('stderr', '')
    
    if stdout:
        header_lines.append("STDOUT:")
        for line in stdout.split('\n'):
            if line:  # Only add non-empty lines
                header_lines.append(f"  {line}")
        header_lines.append("")
    
    if stderr:
        header_lines.append("STDERR:")
        for line in stderr.split('\n'):
            if line:  # Only add non-empty lines
                header_lines.append(f"  {line}")
        header_lines.append("")
    
    # Original test description if it exists
    if original_header:
        header_lines.append("ORIGINAL TEST DESCRIPTION:")
        for line in original_header.split('\n'):
            header_lines.append(f"  {line}")
        header_lines.append("")
    
    header_lines.append("=" * 78)
    
    # Write the file with comprehensive header
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('\n'.join(header_lines))
        f.write('\n"""\n\n')
        
        # Add monitor code as a comment block (after the docstring)
        if monitor_content:
            f.write('# ' + '=' * 76 + '\n')
            f.write('# REFERENCE MONITOR CODE (Target: ' + netid + ')\n')
            f.write('# ' + '=' * 76 + '\n')
            for line in monitor_content.split('\n'):
                f.write('# ' + line + '\n')
            f.write('# ' + '=' * 76 + '\n')
            f.write('\n')
        
        f.write(code_content)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run all test cases against all reference monitors using remote Docker API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_all_tests.py                    # Use default 8 workers
  python3 run_all_tests.py --workers 4        # Use 4 concurrent workers
  python3 run_all_tests.py -w 16              # Use 16 concurrent workers
        """
    )
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        metavar='N',
        help=f'Maximum number of concurrent test executions (default: {DEFAULT_MAX_WORKERS})'
    )
    
    args = parser.parse_args()
    max_workers = args.workers
    
    if max_workers < 1:
        print("❌ ERROR: Number of workers must be at least 1")
        sys.exit(1)
    
    print("=" * 80)
    print("Running all test cases against all reference monitors")
    print("Using remote Docker API (ARM-compatible)")
    print(f"Multi-threading enabled: up to {max_workers} concurrent tasks")
    print("=" * 80)
    
    # Check server health
    if not check_server_health():
        print("❌ ERROR: Remote execution server is not available!")
        print(f"   Server: {BASE_URL}")
        print("   Please check your connection and try again.")
        sys.exit(1)
    
    print("✓ Remote server is available\n")
    
    # Ensure base result directory exists (for CSV/JSON outputs)
    os.makedirs("submit/result", exist_ok=True)
    
    # Get all monitor files
    monitor_files = sorted(glob.glob("submit/reference_monitor/reference_monitor_*.r2py"))
#    # monitor_files = [os.path.join("submit", "reference_monitor", "reference_monitor_sl10429.r2py")]
    # monitor_files = [os.path.join("submit", "reference_monitor", "reference_monitor_sl00000.r2py")]
    
    if not monitor_files:
        print("❌ ERROR: No monitor files found in submit/reference_monitor/")
        sys.exit(1)
    
    # Get all test files (support both legacy and <netid>_attackcase formats)
    test_files = discover_test_files()
    
    if not test_files:
        print("❌ ERROR: No test files found in submit/general_tests/ (expected names like testNN.r2py or <netid>_attackcaseM.r2py)")
        sys.exit(1)
    
    print(f"Found {len(monitor_files)} monitors to test")
    print(f"Found {len(test_files)} test cases\n")
    
    # Track overall stats
    total_monitors_passed = 0
    total_monitors_failed = 0
    
    # Store all results for CSV output
    # results_matrix[netid][test_name] = "PASS" or "FAIL"
    results_matrix = {}
    all_test_names = [os.path.basename(t) for t in test_files]
    
    # Store all execution logs for JSON output
    all_execution_logs = []
    
    # Test each monitor with overall progress bar
    with tqdm(total=len(monitor_files), desc="Overall Progress", unit="monitor", position=0) as monitor_pbar:
        for monitor_file in monitor_files:
            monitor_name = os.path.basename(monitor_file)
            netid = parse_netid(monitor_name)
            
            if not netid:
                tqdm.write(f"⚠️  Skipping {monitor_name} (cannot parse netid)")
                monitor_pbar.update(1)
                continue
            
            tqdm.write(f"\n{'=' * 80}")
            tqdm.write(f"Testing monitor: {monitor_name} (netid: {netid})")
            tqdm.write(f"{'=' * 80}")
            
            # Run all tests against this monitor in parallel
            passed, failed_tests, test_results, execution_logs = test_monitor_parallel(monitor_file, test_files, netid, max_workers)
            failed = len(failed_tests)
            
            # Store execution logs
            all_execution_logs.extend(execution_logs)
            
            # Store results for CSV
            results_matrix[netid] = {}
            for test_name, (success, error) in test_results.items():
                if success:
                    results_matrix[netid][test_name] = "PASS"
                elif error == "TIMEOUT":
                    results_matrix[netid][test_name] = "TIMEOUT"
                else:
                    results_matrix[netid][test_name] = "FAIL"
            
            # Print summary for this monitor
            tqdm.write(f"  Summary: {passed} passed, {failed} failed out of {len(test_files)} tests")
            
            # Store results
            if failed > 0:
                # List failed tests without writing files
                tqdm.write(f"\n  Failed tests:")
                for idx, (test_file, test_name, error) in enumerate(failed_tests, start=1):
                    reason_display = "⏱️  TIMEOUT" if error == "TIMEOUT" else "❌ FAILED"
                    output_name = f"{netid}_attackcase{idx}.r2py"
                    tqdm.write(f"    {output_name} - Test: {test_name} - Reason: {reason_display}")
                total_monitors_failed += 1
                monitor_pbar.set_postfix_str(f"Failed: {total_monitors_failed}, Passed: {total_monitors_passed}")
            else:
                # Mark as passed without copying to success folder
                tqdm.write(f"\n  ✓ All tests passed for {monitor_name}")
                total_monitors_passed += 1
                monitor_pbar.set_postfix_str(f"Failed: {total_monitors_failed}, Passed: {total_monitors_passed}")
            
            monitor_pbar.update(1)
    
    # Write CSV matrix
    csv_output_path = "submit/result/test_results_matrix.csv"
    print(f"\n📊 Writing test results matrix to: {csv_output_path}")
    
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header row: Monitor/NetID, Test1, Test2, ..., TestN
        header = ["Monitor/NetID"] + all_test_names
        writer.writerow(header)
        
        # Data rows: one per monitor
        for netid in sorted(results_matrix.keys()):
            row = [netid]
            for test_name in all_test_names:
                result = results_matrix[netid].get(test_name, "N/A")
                row.append(result)
            writer.writerow(row)
    
    print(f"✓ CSV matrix saved successfully")
    
    # Write JSON execution logs
    json_output_path = "submit/result/test_execution_logs.json"
    print(f"\n📝 Writing detailed execution logs to: {json_output_path}")
    
    json_output = {
        "metadata": {
            "total_monitors": len(monitor_files),
            "total_tests": len(test_files),
            "monitors_passed": total_monitors_passed,
            "monitors_failed": total_monitors_failed,
            "execution_date": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "max_workers": max_workers
        },
        "executions": all_execution_logs
    }
    
    with open(json_output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_output, jsonfile, indent=2)
    
    print(f"✓ JSON logs saved successfully ({len(all_execution_logs)} executions logged)")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Monitors passed all tests: {total_monitors_passed}")
    print(f"Monitors failed some tests: {total_monitors_failed}")
    print(f"Total monitors tested: {total_monitors_passed + total_monitors_failed}")
    print("=" * 80)
    
    print(f"✓ Test results matrix saved to: {csv_output_path}")
    print(f"✓ Detailed execution logs saved to: {json_output_path}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
