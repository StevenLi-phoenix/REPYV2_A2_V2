# Quick Start - Web Visualizer

## TL;DR - Fastest Way to Start

```bash
# Make script executable (first time only)
chmod +x start_web.sh

# Start the web server
./start_web.sh
```

Then open: **http://localhost:8000**

---

## Manual Start

### Step 1: Install Dependencies

```bash
pip3 install fastapi uvicorn
```

### Step 2: Start Server

```bash
python3 web.py
```

### Step 3: Open Browser

Go to: http://localhost:8000

---

## What You'll See

### 📊 Dashboard Features

1. **Summary Cards** - Total monitors, passes, failures, timeouts
2. **Filters** - Search by monitor NetID or test name
3. **Sorting** - Sort by any column (pass/fail/timeout counts)
4. **Full Test Matrix** - Complete grid showing all monitors × all tests
5. **Hover Details** - Hover over any cell to see execution details

### 🎨 Visual Design

- **Purple gradient** background
- **Color-coded results**:
  - ✓ Green = PASS
  - ✗ Red = FAIL/TIMEOUT
- **Interactive tooltips** - Hover for duration, error messages, output
- **Responsive** - works on mobile and desktop
- **Modern UI** - built with Tailwind CSS

### 💡 Understanding the Matrix

The main table shows:
- **Left columns**: Monitor NetID and summary counts
- **Matrix cells**: Each test result (✓ or ✗)
- **Hover tooltip**: Shows execution time, error details, output
- **Vertical headers**: Test names (rotated to save space)

---

## API Access

### Get JSON Data

```bash
curl http://localhost:8000/api/data
```

### Interactive Docs

FastAPI provides automatic API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Troubleshooting

### "CSV file not found"

Run the test suite first:

```bash
python3 run_all_tests.py
```

This generates `submit/result/test_results_matrix.csv`

### Port Already in Use

Change the port in `web.py` (last line):

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
```

### Dependencies Missing

Install everything at once:

```bash
pip3 install -r requirements.txt
```

---

## Technology Stack

- **Backend**: FastAPI (modern, fast Python web framework)
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Server**: Uvicorn (ASGI server)
- **Data Source**: CSV file from test results

---

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the web server.

