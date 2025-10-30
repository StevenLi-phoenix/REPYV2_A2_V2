# Test Results Visualizer - Complete Feature Summary

## 🎯 Core Features

### 1. **Full Matrix Display**
- Shows ALL monitors × ALL tests in one view
- ✓ Green = PASS
- ✗ Red = FAIL/TIMEOUT
- Compact, information-dense layout

### 2. **Triple-Level Hover System** 💡

#### Level 1: Monitor NetID Hover
Hover over any monitor name to see:
- ✓ Pass: X tests
- ✗ Fail: X tests
- ⏱ Timeout: X tests
- Total: X tests

#### Level 2: Test Header Hover
Hover over any test column header to see:
- Test full name
- Pass: X monitors
- Fail: X monitors
- Timeout: X monitors
- Total: X monitors

#### Level 3: Result Cell Hover
Hover over any ✓/✗ cell to see:
- Test name
- Status (PASS/FAIL/TIMEOUT)
- Execution duration (seconds)
- Exit code
- Error message (first 100 chars)
- Standard output (first 100 chars)

### 3. **Advanced Sorting**

#### Sort Monitors By:
- **NetID (A-Z)**: Alphabetical order
- **Pass Count**: Monitors with most passes
- **Fail Count**: Monitors with most failures
- **Timeout Count**: Monitors with most timeouts

#### Sort Tests By:
- **Test Name**: Alphabetical order
- **Most Failed**: Tests that fail most often (find problematic tests!)
- **Most Passed**: Tests that pass most often
- **Most Timeouts**: Tests that timeout most often

#### Order:
- Ascending or Descending
- Applies to both monitor and test sorting

### 4. **Filtering**

#### Filter by Monitor (NetID):
- Type any part of a NetID
- Example: "aa11" shows aa11931, aa11xxx, etc.
- Case-insensitive

#### Filter by Test:
- Type any part of a test name
- Example: "extreme" shows all extreme tests
- Example: "test01" shows test01_xxx tests
- Case-insensitive

### 5. **Summary Statistics**
Top cards showing:
- 🔵 Total Monitors
- 🟢 Total Passes (across all executions)
- 🔴 Total Failures (across all executions)
- 🟠 Total Timeouts (across all executions)

### 6. **Interactive Detail Modal** 👆
- **Click any test cell** to open detailed view
- Full execution information in a beautiful modal
- Complete error messages and output (not truncated)
- Color-coded status banners
- Close with Escape, X button, or click outside

### 7. **Clean Design**
- No cluttered summary columns
- All stats accessible via hover
- Maximum space for the matrix
- Responsive layout

## 🎨 User Interface

### Layout Structure
```
┌─────────────────────────────────────────────┐
│  Header: Test Results Data Visualizer      │
├─────────────────────────────────────────────┤
│  Controls:                                  │
│  [Monitor Filter] [Test Filter]            │
│  [Sort Monitors] [Sort Tests] [Order]      │
├─────────────────────────────────────────────┤
│  Stats: [Monitors] [Passes] [Fails] [TO]  │
├─────────────────────────────────────────────┤
│  Legend: ✓ Pass  ✗ Fail  💡 Hover tips    │
├─────────────────────────────────────────────┤
│  Matrix:                                    │
│  NetID(*)│ t01│ t02│ t03│...              │
│  ──────────────────────────────────────────│
│  aa11931│  ✓ │  ✗ │  ✓ │...              │
│  aa12037│  ✓ │  ✓ │  ✓ │...              │
│  ...                                        │
└─────────────────────────────────────────────┘

(*) = Hover for details
```

### Visual Cues
- **Purple gradient** header
- **Green (✓)** for passing tests
- **Red (✗)** for failing/timeout tests
- **Dark tooltips** on hover with white text
- **Sticky header** when scrolling

## 🚀 Use Cases

### 1. Find Problematic Monitors
```
1. Sort Monitors By: "Fail Count"
2. Order: "Descending"
3. Result: Worst monitors at top
```

### 2. Find Problematic Tests
```
1. Sort Tests By: "Most Failed"
2. Order: "Descending"
3. Result: Tests that fail most often appear first
```

### 3. Investigate a Specific Monitor
```
1. Filter by Monitor: "aa11931"
2. Hover over NetID for summary
3. Hover over ✗ cells to see why tests failed
```

### 4. Investigate a Specific Test
```
1. Filter by Test: "test01"
2. Hover over test header to see pass/fail counts
3. Hover over ✗ cells to see which monitors failed
```

### 5. Find Timeout Issues
```
1. Sort Tests By: "Most Timeouts"
2. Or Sort Monitors By: "Timeout Count"
3. Hover over cells to see timeout details
```

### 6. Compare Monitor Performance
```
1. No filters
2. Sort Monitors By: "Pass Count" (Descending)
3. Scroll through to compare
4. Hover over NetIDs for exact stats
```

## 📊 Data Sources

### Input Files:
1. **`submit/result/test_results_matrix.csv`**
   - Matrix of PASS/FAIL/TIMEOUT status
   - One row per monitor
   - One column per test

2. **`submit/result/test_execution_logs.json`**
   - Detailed execution metadata
   - Duration, exit codes, errors, output
   - Used for hover tooltips

### Generated By:
```bash
python3 run_all_tests.py
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3)
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Server**: Uvicorn (ASGI)
- **Data Format**: CSV + JSON
- **Styling**: Tailwind CSS via CDN

## 📖 Quick Reference

### Keyboard/Mouse Actions
- **Scroll Horizontal**: View all tests
- **Scroll Vertical**: View all monitors
- **Hover**: See detailed information
- **Type in filters**: Filter in real-time
- **Click dropdowns**: Change sorting

### Default Settings
- Monitors: Sorted by NetID (A-Z)
- Tests: Sorted by name (alphabetical)
- Order: Descending
- No filters applied

### Best Practices
1. Start with "Most Failed" test sort to identify issues
2. Use monitor filter to focus on specific students
3. Hover everywhere - tons of info in tooltips
4. Sort monitors by fail count to find worst performers
5. Use test filter for specific test families (e.g., "extreme")

## 🎓 Educational Value

This visualizer helps instructors:
- **Quickly identify** struggling students (monitors with high fail counts)
- **Find problematic tests** (tests that fail across many monitors)
- **Debug issues** (hover for execution details)
- **Assess difficulty** (tests with low pass rates)
- **Compare implementations** (same test across monitors)
- **Spot timeout issues** (sort by timeouts)

Perfect for grading assignments where many students submit similar code!

