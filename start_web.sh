#!/bin/bash
# Quick start script for the web visualizer

echo "============================================"
echo "Test Results Data Visualizer"
echo "FastAPI + Tailwind CSS"
echo "============================================"
echo ""

# Check if FastAPI is installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip3 install fastapi uvicorn
    echo ""
fi

# Check if CSV exists
if [ ! -f "submit/result/test_results_matrix.csv" ]; then
    echo "⚠️  CSV file not found: submit/result/test_results_matrix.csv"
    echo "Run 'python3 run_all_tests.py' first to generate the data."
    echo ""
    read -p "Press Enter to start the server anyway..."
fi

echo "Starting web server..."
python3 web.py

