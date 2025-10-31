import os
import json
list_of_verify_cases = json.load(open("list_of_verify_cases.json"))
path_constructor = lambda name: os.path.join("submit", "general_tests", name + ".r2py")
assert all(os.path.exists(path_constructor(case)) for case in list_of_verify_cases), "Some files do not exist"

prompt = """# Consolidated Rules for the RepyV2 Versioned-File Reference Monitor

## A. Baseline Behavior

* All file operations behave exactly like **RepyV2** unless modified below.
* At startup, **no files exist**.

## B. File Identity and Versioning

* The **original file** (head lineage) is referred to by `filename` (this is **v0**).
* A new version is named `filename + '.v' + str(num)` where `num ≥ 1`.
* **Clarification:** `openfile("attack3", False)` means open the **original file (v0)**.

## C. Creating and Opening

* `openfile(filename, True)`:

  * If `filename` doesn’t exist, create **v0** (original file) as in RepyV2.
  * If `filename` already exists, create a **new version (next vN)** initialized with the **latest version’s contents**.
  * **Constraint:** A **new version cannot be created while the latest version is open**.
* `openfile(filename, False)` opens **v0** only if it exists, else raise **`FileNotFoundError`**.
* `openfile(filename + '.v' + num, create)`:

  * If `create=True` → raise **`RepyArgumentError("Cannot create explicit version files")`**.
  * If `create=False` → open only if that exact version exists; else **`FileNotFoundError`**.

## D. Concurrency & Access Modes

* **Older versions (v1, v2, …) are immutable snapshots.**

  * **Concurrent reading is allowed.** Multiple simultaneous opens of the **same** older version for reading are permitted.
  * Reading older versions is always allowed, regardless of the head’s open/closed state.
  * **Writing to any older version is permanently disallowed**; any write attempt (via a handle to an older version) must raise **`FileInUseError`**.
* **Latest version (current head in the lineage)**

  * Follows RepyV2 single-open exclusivity: opening a file that is already open (the **same version**) must raise **`FileInUseError`**.
  * Opening the head while any number of old-version readers are open is allowed (old-version readers don’t block).
  * Opening additional handles to the head concurrently (same version) is **not** allowed (per RepyV2), and must raise **`FileInUseError`**.

## E. Deletion & Listing

* **Deletion is disallowed** for all files/versions: any `removefile` must raise **`RepyArgumentError`**.
* `listfiles()` **must not expose versioned paths**. It lists only the set of **original filenames** that have been created (one entry per logical file), regardless of how many versions exist.

## F. Error Semantics

* If `openfile()` targets an **already open same-version file** (per RepyV2 semantics), raise **`FileInUseError`**.
* Use **`FileNotFoundError`** when opening non-existent (head or explicit version) with `create=False`.
* Use **`RepyArgumentError`** when attempting to create explicit versions (`"name.vN", True`) or delete any file.

## G. Requirements for the Attack/Test Case

* **Never produce unexpected errors or any output.** A correct monitor yields **no output** from the attack case.
* You **may** test for expected errors, but:

  * **Catch and suppress** them if correctly raised.
  * **Do not** check error **messages**; only check the **exception class** (e.g., `FileInUseError`).
"""

from openai import OpenAI
import time
import requests

client = OpenAI()

# Notification URL
NOTIFICATION_URL = "https://api.day.app/TwwEUMR9QCUU4jmFXnoFKK/Critical%20Alert?level=critical&volume=5"

def send_notification(title, message):
    """Send notification to the specified URL"""
    try:
        # Update the notification URL with custom title and message
        base_url = "https://api.day.app/TwwEUMR9QCUU4jmFXnoFKK"
        full_url = f"{base_url}/{requests.utils.quote(title)}?body={requests.utils.quote(message)}&level=critical&volume=5"
        response = requests.get(full_url)
        if response.status_code == 200:
            print(f"✓ Notification sent successfully")
        else:
            print(f"⚠ Notification failed: {response.status_code}")
    except Exception as e:
        print(f"⚠ Failed to send notification: {e}")

# System prompt for verification
system_prompt = """You are a RepyV2 security specification verifier. Your task is to analyze test cases and determine if they align with the specification provided."""

# User prompt template for verification
verification_template = """
Given the following specification and test case code, verify if the test case is correctly aligned with the spec.

{spec}

## Test Case Code:
```python
{test_code}
```

## Instructions:
1. Analyze the test case line by line
2. Determine if it follows the spec rules
3. If not aligned, provide at most 3 most significant spec violations
4. Some test cases may be correct - if so, state that clearly
5. Do NOT try to fix the code, just analyze it

## Required Output Format:
Correct: [True/False]
Reason: [Detailed explanation of why it is or isn't aligned with the spec, maximum 1000 words]
Timeline: [Step-by-step execution timeline, clearly indicating if operations are parallel or sequential]
Spec Violations: [If any, list the most significant violations with exact code snippets. If none, state "None"]

## Example Output:
Correct: False
Reason: The attack code is not aligned with the spec because it outputs a log when not supposed to.
Timeline:
1. openfile("testfile", True) - Creates v0
2. writeat("HelloWorld", 0) - Writes to v0
3. close("testfile")
4. log("Done") - VIOLATION: produces output
Spec Violations:
1. Section G: "Never produce unexpected errors or any output" - The code calls log("Done") which produces output
"""

def create_batch_input_file():
    """Create JSONL file for batch API with all verification requests"""
    batch_requests = []
    
    for idx, case_name in enumerate(list_of_verify_cases):
        file_path = path_constructor(case_name)
        with open(file_path, 'r') as f:
            test_code = f.read()
        
        user_message = verification_template.format(
            spec=prompt,
            test_code=test_code
        )
        
        batch_requests.append({
            "custom_id": case_name,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            }
        })
    
    # Write to JSONL file
    batch_file_path = "batch_verification_input.jsonl"
    with open(batch_file_path, 'w') as f:
        for request in batch_requests:
            f.write(json.dumps(request) + '\n')
    
    print(f"Created batch input file: {batch_file_path}")
    print(f"Total requests: {len(batch_requests)}")
    return batch_file_path

def submit_batch(batch_file_path):
    """Upload file and submit batch job"""
    # Upload the batch input file
    with open(batch_file_path, 'rb') as f:
        batch_input_file = client.files.create(
            file=f,
            purpose="batch"
        )
    
    print(f"Uploaded file ID: {batch_input_file.id}")
    
    # Create the batch
    batch = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": "RepyV2 test case verification"
        }
    )
    
    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.status}")
    
    # Save batch ID for later retrieval
    with open("batch_id.txt", 'w') as f:
        f.write(batch.id)
    
    return batch.id

def check_batch_status(batch_id):
    """Check the status of a batch job"""
    batch = client.batches.retrieve(batch_id)
    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.status}")
    print(f"Created at: {batch.created_at}")
    print(f"Request counts: {batch.request_counts}")
    
    if batch.status == "completed":
        print(f"Output file ID: {batch.output_file_id}")
        print(f"Error file ID: {batch.error_file_id}")
    
    return batch

def download_batch_results(batch_id):
    """Download and process batch results"""
    batch = client.batches.retrieve(batch_id)
    
    if batch.status != "completed":
        print(f"Batch not completed yet. Status: {batch.status}")
        return None
    
    # Check if there are any successful completions
    if batch.request_counts.completed == 0:
        print(f"⚠ Warning: No successful completions (0/{batch.request_counts.total})")
        print(f"Failed: {batch.request_counts.failed}")
        
        # Download error file if available
        if batch.error_file_id:
            print(f"\nDownloading error file: {batch.error_file_id}")
            error_content = client.files.content(batch.error_file_id)
            error_path = "batch_verification_errors.jsonl"
            with open(error_path, 'wb') as f:
                f.write(error_content.content)
            print(f"Errors saved to: {error_path}")
            
            # Parse and display first few errors
            with open(error_path, 'r') as f:
                error_count = 0
                for line in f:
                    if error_count < 3:  # Show first 3 errors
                        error = json.loads(line)
                        print(f"\nError in {error.get('custom_id', 'unknown')}:")
                        # Error can be in two places: error field or response.body.error
                        if error.get('error'):
                            error_msg = error['error'].get('message', 'Unknown error')
                        elif error.get('response', {}).get('body', {}).get('error'):
                            error_msg = error['response']['body']['error'].get('message', 'Unknown error')
                        else:
                            error_msg = 'Unknown error structure'
                        print(f"  {error_msg}")
                        error_count += 1
            
            send_notification(
                "Batch Verification Failed",
                f"All {batch.request_counts.failed} requests failed. Check batch_verification_errors.jsonl"
            )
        return None
    
    # Download output file if available
    if not batch.output_file_id:
        print("⚠ No output file available")
        return None
    
    output_file_id = batch.output_file_id
    output_content = client.files.content(output_file_id)
    
    # Save raw output
    output_path = "batch_verification_output.jsonl"
    with open(output_path, 'wb') as f:
        f.write(output_content.content)
    
    print(f"Downloaded results to: {output_path}")
    
    # Parse results
    results = {}
    with open(output_path, 'r') as f:
        for line in f:
            result = json.loads(line)
            custom_id = result['custom_id']
            response = result['response']['body']['choices'][0]['message']['content']
            results[custom_id] = response
    
    # Save parsed results
    parsed_path = "verification_results.json"
    with open(parsed_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Parsed results saved to: {parsed_path}")
    print(f"\nSuccess: {batch.request_counts.completed}/{batch.request_counts.total}")
    if batch.request_counts.failed > 0:
        print(f"Failed: {batch.request_counts.failed}")
    
    # Send notification
    send_notification(
        "Batch Verification Complete",
        f"Completed: {batch.request_counts.completed}/{batch.request_counts.total}. Failed: {batch.request_counts.failed}"
    )
    
    return results

def wait_for_completion(batch_id, check_interval=60):
    """Poll batch status and download when complete"""
    print(f"Monitoring batch {batch_id}...")
    print(f"Checking every {check_interval} seconds")
    
    while True:
        batch = client.batches.retrieve(batch_id)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status: {batch.status}")
        
        if batch.status == "completed":
            print("\n✓ Batch completed!")
            results = download_batch_results(batch_id)
            if results:
                print(f"\nVerified {len(results)} test cases")
                print("Results saved to verification_results.json")
            return results
        
        elif batch.status == "failed" or batch.status == "expired" or batch.status == "cancelled":
            print(f"\n✗ Batch {batch.status}")
            send_notification(
                "Batch Verification Failed",
                f"Batch status: {batch.status}"
            )
            return None
        
        # Wait before next check
        time.sleep(check_interval)

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python verify.py create         - Create and submit batch job")
        print("  python verify.py status         - Check batch status")
        print("  python verify.py download       - Download completed results")
        print("  python verify.py wait           - Wait for completion and auto-download")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        batch_file = create_batch_input_file()
        batch_id = submit_batch(batch_file)
        print(f"\nBatch submitted successfully!")
        print(f"Batch ID saved to batch_id.txt")
        print(f"Run 'python verify.py status' to check progress")
        print(f"Or run 'python verify.py wait' to auto-download when complete")
        
        # Send notification
        send_notification(
            "Batch Verification Started",
            f"Submitted {len(list_of_verify_cases)} test cases for verification"
        )
        
    elif command == "status":
        if not os.path.exists("batch_id.txt"):
            print("No batch ID found. Run 'python verify.py create' first")
            return
        
        with open("batch_id.txt", 'r') as f:
            batch_id = f.read().strip()
        
        check_batch_status(batch_id)
        
    elif command == "download":
        if not os.path.exists("batch_id.txt"):
            print("No batch ID found. Run 'python verify.py create' first")
            return
        
        with open("batch_id.txt", 'r') as f:
            batch_id = f.read().strip()
        
        results = download_batch_results(batch_id)
        if results:
            print(f"\nVerified {len(results)} test cases")
            print("Results saved to verification_results.json")
    
    elif command == "wait":
        if not os.path.exists("batch_id.txt"):
            print("No batch ID found. Run 'python verify.py create' first")
            return
        
        with open("batch_id.txt", 'r') as f:
            batch_id = f.read().strip()
        
        wait_for_completion(batch_id)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()