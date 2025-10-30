# Test Results Data Visualizer

A modern web service to visualize and analyze test results from the CSV matrix.  
Built with **FastAPI** and **Tailwind CSS** for a fast, beautiful user experience.

## Features

- 📊 **Summary Statistics**: See total monitors, passes, failures, and timeouts at a glance
- 🔍 **Filter by Monitor**: Search for specific monitors by NetID
- 🔍 **Filter by Test**: Search for specific test cases
- 🔄 **Sort Options**: Sort by NetID, pass count, fail count, timeout count, or total tests
- 📈 **Full Test Matrix**: See ALL test results in a comprehensive matrix view
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- ⚡ **Fast**: Built on FastAPI for high performance
- 🌈 **Color-coded Results**: ✓ Green for PASS, ✗ Red for FAIL/TIMEOUT
- 💡 **Hover Details**: Hover over any cell to see execution details (duration, error, output)
- 📝 **JSON-backed**: Uses detailed execution logs for rich hover information

## Quick Start

### 1. Install Dependencies

```bash
pip3 install fastapi uvicorn
```

Or install all requirements:

```bash
pip3 install -r requirements.txt
```

### 2. Generate Test Data (if not already done)

```bash
python3 run_all_tests.py
```

This creates `submit/result/test_results_matrix.csv`

### 3. Start the Web Server

```bash
python3 web.py
```

### 4. Open in Browser

Navigate to: **http://localhost:8000**

## Usage Examples

### Filter by Monitor
Type a NetID in the "Filter by Monitor" field to see results for specific monitors:
- Example: `aa11931`
- Example: `npj2009`

### Filter by Test
Type a test name in the "Filter by Test" field to see results for specific tests:
- Example: `test01`
- Example: `basic_versioning`
- Example: `extreme`

### Sort Results

**Sort Monitors By:**
- **NetID (A-Z)**: Alphabetically by monitor name
- **Pass Count**: Number of passed tests per monitor
- **Fail Count**: Number of failed tests per monitor
- **Timeout Count**: Number of timeout failures per monitor

**Sort Tests By:**
- **Test Name**: Alphabetically by test filename
- **Most Failed**: Tests that failed the most across all monitors
- **Most Passed**: Tests that passed the most across all monitors
- **Most Timeouts**: Tests that timed out the most

**Order:**
- Ascending or Descending

Both monitor and test sorting work independently!

### Combined Filtering
You can combine filters! For example:
- Filter by monitor `sl10429` and test `extreme` to see how that monitor performs on extreme tests
- Sort by fail count (descending) to see which monitors have the most failures

## API Endpoints

### Get Data as JSON

```bash
curl http://localhost:8000/api/data
```

Returns:
```json
{
  "monitors": [...],
  "test_names": [...]
}
```

### Interactive API Documentation

FastAPI provides automatic interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Understanding the Matrix

### Color Coding

- ✓ **Green (PASS)**: Test passed successfully
- ✗ **Red (FAIL/TIMEOUT)**: Test failed (includes both regular failures and timeouts)

### Hover Information

**Hover over Monitor NetID to see:**
- Pass count
- Fail count  
- Timeout count
- Total tests

**Hover over Test column headers to see:**
- Test filename
- How many monitors passed
- How many monitors failed
- How many monitors timed out

**Hover over test result cells to see:**
- Test Name: Full test filename
- Status: PASS, FAIL, or TIMEOUT
- Duration: Execution time in seconds
- Exit Code: Process exit code
- Error Message: Brief error description (if failed)
- Output: First 100 characters of stdout (if any)
- Hint: "Click for full details"

**Click on test result cells to open detail modal with:**
- Full status banner with large icon
- Complete execution metadata (duration, exit code, start/end times)
- Full error message (not truncated)
- Complete standard output (scrollable)
- Beautiful, responsive modal design

### Matrix Layout

- **Rows**: Each monitor (NetID with hover stats)
- **Columns**: Each test case (with hover stats)
- **No Summary Columns**: Stats are in hover tooltips for cleaner view
- **Test Headers**: Vertical text to save space (hover for full name and stats)

## Tips

1. **Click for Details**: Click any test cell to see full execution details in a modal
2. **Scroll Horizontally**: The matrix shows all tests - scroll right to see all columns
3. **Triple Hover**: Hover over NetIDs, test headers, and result cells for different stats
4. **Sort Tests by Failures**: Use "Sort Tests By: Most Failed" to see problematic tests first
5. **Sort Monitors by Failures**: Use "Sort Monitors By: Fail Count" to find worst performers
6. **Filter to Focus**: Use filters to narrow down to specific monitors or tests
7. **Real-time Updates**: Filters and sorting update instantly
8. **Sticky Header**: Table header stays visible when scrolling vertically
9. **Close Modal**: Press Escape, click X, or click outside to close detail modal
10. **Cleaner Matrix**: No summary columns cluttering the view - everything is in tooltips!

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the web server.

