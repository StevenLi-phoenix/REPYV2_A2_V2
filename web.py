#!/usr/bin/env python3
"""
Data Visualizer Web Service
Reads test_results_matrix.csv and provides sorting/filtering capabilities.
Built with FastAPI and Tailwind CSS.
"""
import csv
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Test Results Data Visualizer")

CSV_PATH = "submit/result/test_results_matrix.csv"
JSON_PATH = "submit/result/test_execution_logs.json"
VERIFICATION_PATH = "verification_results.json"
ANNOTATIONS_PATH = "test_annotations.json"

def load_annotations():
    """Load test annotations (resolved, TODO, invalid tests)"""
    if not Path(ANNOTATIONS_PATH).exists():
        return {
            'resolved': {},  # {(netid, test_name): True}
            'todo': {},      # {(netid, test_name): True}
            'invalid_tests': {}  # {test_name: reason}
        }
    
    try:
        with open(ANNOTATIONS_PATH, 'r') as f:
            data = json.load(f)
            # Convert string keys back to tuples for resolved/todo
            resolved = {tuple(k.split('|')): v for k, v in data.get('resolved', {}).items()}
            todo = {tuple(k.split('|')): v for k, v in data.get('todo', {}).items()}
            return {
                'resolved': resolved,
                'todo': todo,
                'invalid_tests': data.get('invalid_tests', {})
            }
    except Exception as e:
        print(f"Warning: Could not load annotations: {e}")
        return {'resolved': {}, 'todo': {}, 'invalid_tests': {}}

def save_annotations(annotations):
    """Save test annotations to file"""
    try:
        # Convert tuple keys to strings for JSON serialization
        data = {
            'resolved': {f"{k[0]}|{k[1]}": v for k, v in annotations['resolved'].items()},
            'todo': {f"{k[0]}|{k[1]}": v for k, v in annotations['todo'].items()},
            'invalid_tests': annotations['invalid_tests']
        }
        with open(ANNOTATIONS_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving annotations: {e}")
        return False

def load_verification_results():
    """Load ChatGPT verification comments from JSON or JSONL"""
    # Try JSON first (old format)
    if Path(VERIFICATION_PATH).exists():
        try:
            with open(VERIFICATION_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load verification_results.json: {e}")
    
    # Try JSONL format (batch output)
    jsonl_path = "batch_verification_output.jsonl"
    if Path(jsonl_path).exists():
        try:
            results = {}
            with open(jsonl_path, 'r') as f:
                for line in f:
                    item = json.loads(line)
                    custom_id = item.get('custom_id')
                    if custom_id and item.get('response', {}).get('status_code') == 200:
                        content = item['response']['body']['choices'][0]['message']['content']
                        results[custom_id + '.r2py'] = content
            return results
        except Exception as e:
            print(f"Warning: Could not load batch_verification_output.jsonl: {e}")
    
    return {}

def load_execution_logs():
    """Load detailed execution logs from JSON"""
    if not Path(JSON_PATH).exists():
        return {}
    
    try:
        with open(JSON_PATH, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
            executions = data.get('executions', [])
            
            # Build a lookup dict: (netid, test_file) -> execution_info
            lookup = {}
            for exec_info in executions:
                key = (exec_info.get('netid'), exec_info.get('test_file'))
                lookup[key] = exec_info
            
            return lookup
    except Exception as e:
        print(f"Warning: Could not load JSON logs: {e}")
        return {}

def load_data():
    """Load CSV data and return structured data WITHOUT heavy execution details"""
    if not Path(CSV_PATH).exists():
        return None, [], [], {}
    
    # Load annotations (resolved, TODO, invalid tests)
    annotations = load_annotations()
    
    # Don't load execution logs or verification here - too heavy! Load on-demand.
    
    with open(CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        headers = next(reader)  # First row: Monitor/NetID, Test1, Test2, ...
        test_names = headers[1:]  # All test names
        
        monitors_data = []
        for row in reader:
            netid = row[0]
            results = row[1:]
            
            # Count pass/fail/timeout
            pass_count = results.count("PASS")
            fail_count = results.count("FAIL")
            timeout_count = results.count("TIMEOUT")
            total = len(results)
            
            # Build results dict with lightweight data (no logs/code/verification)
            results_dict = {}
            for test_name, result in zip(test_names, results):
                # Check annotations
                is_resolved = annotations['resolved'].get((netid, test_name), False)
                is_todo = annotations['todo'].get((netid, test_name), False)
                is_invalid_test = test_name in annotations['invalid_tests']
                invalid_reason = annotations['invalid_tests'].get(test_name, '')
                
                results_dict[test_name] = {
                    'status': result,
                    'is_resolved': is_resolved,
                    'is_todo': is_todo,
                    'is_invalid_test': is_invalid_test,
                    'invalid_reason': invalid_reason,
                    'netid': netid,
                    'test_name': test_name
                }
            
            monitors_data.append({
                'netid': netid,
                'results': results_dict,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'timeout_count': timeout_count,
                'total': total
            })
    
    return monitors_data, test_names, headers, annotations

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results Data Visualizer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#667eea',
                        secondary: '#764ba2',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-gradient-to-br from-primary via-purple-600 to-secondary min-h-screen p-4 md:p-6">
    <!-- Detail Modal -->
    <div id="detailModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onclick="closeDetailModal(event)">
        <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onclick="event.stopPropagation()">
            <!-- Modal Header -->
            <div class="bg-gradient-to-r from-primary to-secondary text-white px-6 py-4 flex justify-between items-center">
                <h2 class="text-2xl font-bold" id="modalTitle">Execution Details</h2>
                <button onclick="closeDetailModal()" class="text-white hover:text-gray-200 text-3xl font-bold leading-none">&times;</button>
            </div>
            
            <!-- Modal Content -->
            <div class="p-6 overflow-y-auto max-h-[calc(90vh-80px)]" id="modalContent">
                <!-- Content will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="max-w-7xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden">
        
        <!-- Header -->
        <div class="bg-gradient-to-r from-primary to-secondary text-white px-8 py-10 text-center">
            <h1 class="text-4xl md:text-5xl font-bold mb-3">📊 Test Results Data Visualizer</h1>
            <p class="text-lg md:text-xl text-purple-100">Sort, filter, and analyze monitor test results</p>
        </div>
        
        <!-- Controls -->
        <div class="bg-gray-50 px-8 py-6 border-b-2 border-gray-200">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div>
                    <label for="monitorFilter" class="block text-sm font-semibold text-gray-700 mb-2">
                        Filter by Monitor (NetID)
                    </label>
                    <input 
                        type="text" 
                        id="monitorFilter" 
                        placeholder="e.g., aa11931"
                        class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition duration-200 outline-none"
                    >
                </div>
                
                <div>
                    <label for="testFilter" class="block text-sm font-semibold text-gray-700 mb-2">
                        Filter by Test Name
                    </label>
                    <input 
                        type="text" 
                        id="testFilter" 
                        placeholder="e.g., test01"
                        class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition duration-200 outline-none"
                    >
                </div>
                
                <div>
                    <label for="sortMonitorsBy" class="block text-sm font-semibold text-gray-700 mb-2">
                        Sort Monitors By
                    </label>
                    <select 
                        id="sortMonitorsBy"
                        class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition duration-200 outline-none cursor-pointer bg-white"
                    >
                        <option value="netid">NetID (A-Z)</option>
                        <option value="pass_count">Pass Count</option>
                        <option value="fail_count">Fail Count</option>
                        <option value="timeout_count">Timeout Count</option>
                    </select>
                </div>
                
                <div>
                    <label for="sortTestsBy" class="block text-sm font-semibold text-gray-700 mb-2">
                        Sort Tests By
                    </label>
                    <select 
                        id="sortTestsBy"
                        class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition duration-200 outline-none cursor-pointer bg-white"
                    >
                        <option value="name">Test Name</option>
                        <option value="fail_count">Most Failed</option>
                        <option value="pass_count">Most Passed</option>
                        <option value="timeout_count">Most Timeouts</option>
                    </select>
                </div>
                
                <div>
                    <label for="sortOrder" class="block text-sm font-semibold text-gray-700 mb-2">
                        Order
                    </label>
                    <select 
                        id="sortOrder"
                        class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition duration-200 outline-none cursor-pointer bg-white"
                    >
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                    </select>
                </div>
            </div>
        </div>
        
        <!-- Stats -->
        <div id="stats" class="px-8 py-6 bg-white border-b-2 border-gray-200">
            <!-- Stats will be populated by JavaScript -->
        </div>
        
        <!-- Legend -->
        <div class="px-8 py-4 bg-gray-50 border-b-2 border-gray-200">
            <div class="flex items-center justify-center gap-4 text-sm flex-wrap">
                <div class="flex items-center gap-2">
                    <div class="bg-green-500 text-white rounded px-3 py-1 font-bold">✓</div>
                    <span class="text-gray-700 font-medium">Pass</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="bg-red-500 text-white rounded px-3 py-1 font-bold">✗</div>
                    <span class="text-gray-700 font-medium">Fail</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="bg-blue-500 text-white rounded px-3 py-1 font-bold">⏱</div>
                    <span class="text-gray-700 font-medium">Timeout / Resolved</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="bg-orange-500 text-white rounded px-3 py-1 font-bold ring-2 ring-orange-300">📌</div>
                    <span class="text-gray-700 font-medium">TODO</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="bg-yellow-400 text-gray-900 rounded px-3 py-1 font-bold">⚠</div>
                    <span class="text-gray-700 font-medium">Invalid Test</span>
                </div>
                <div class="h-6 w-px bg-gray-300"></div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-600 italic text-xs">💡 Hover for preview</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-purple-600 font-semibold italic text-xs">👆 Click for details & actions</span>
                </div>
            </div>
        </div>
        
        <!-- Table Container -->
        <div class="overflow-x-auto px-8 py-8">
            <div class="inline-block min-w-full">
                <table id="dataTable" class="border-collapse">
                    <!-- Table will be populated by JavaScript -->
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let allData = {{ data|tojson }};
        let allTests = {{ tests|tojson }};
        let currentData = [...allData];
        
        // Save/restore filter state from localStorage
        function saveFilterState() {
            const filterState = {
                monitorFilter: document.getElementById('monitorFilter').value,
                testFilter: document.getElementById('testFilter').value,
                sortMonitorsBy: document.getElementById('sortMonitorsBy').value,
                sortTestsBy: document.getElementById('sortTestsBy').value,
                sortOrder: document.getElementById('sortOrder').value
            };
            localStorage.setItem('testVisualizerFilters', JSON.stringify(filterState));
        }
        
        function restoreFilterState() {
            const saved = localStorage.getItem('testVisualizerFilters');
            if (saved) {
                try {
                    const filterState = JSON.parse(saved);
                    document.getElementById('monitorFilter').value = filterState.monitorFilter || '';
                    document.getElementById('testFilter').value = filterState.testFilter || '';
                    document.getElementById('sortMonitorsBy').value = filterState.sortMonitorsBy || 'netid';
                    document.getElementById('sortTestsBy').value = filterState.sortTestsBy || 'name';
                    document.getElementById('sortOrder').value = filterState.sortOrder || 'desc';
                } catch (e) {
                    console.error('Failed to restore filter state:', e);
                }
            }
        }
        
        async function openDetailModal(netid, testName, resultData) {
            const modal = document.getElementById('detailModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalContent = document.getElementById('modalContent');
            
            // Set title
            modalTitle.textContent = `${netid} - ${testName}`;
            
            // Show loading state
            modalContent.innerHTML = `
                <div class="flex items-center justify-center py-16">
                    <div class="text-center">
                        <div class="text-6xl mb-4">⏳</div>
                        <div class="text-xl text-gray-600">Loading details...</div>
                    </div>
                </div>
            `;
            
            // Show modal immediately
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            // Fetch detailed data from API
            try {
                const response = await fetch(`/api/test_details/${encodeURIComponent(netid)}/${encodeURIComponent(testName)}`);
                if (!response.ok) {
                    throw new Error('Failed to load details');
                }
                const details = await response.json();
                
                // Build content with loaded data
                const status = resultData ? resultData.status : 'N/A';
                const duration = details.duration ? details.duration.toFixed(3) : 'N/A';
                const exitCode = details.exit_code !== null ? details.exit_code : 'N/A';
                const error = details.error ? details.error : 'None';
                const stdout = details.stdout ? details.stdout : '(empty)';
                const startTime = details.start_time ? formatTime(details.start_time) : 'N/A';
                const endTime = details.end_time ? formatTime(details.end_time) : 'N/A';
                const verification = details.verification || '';
            
            // Determine status color and icon
            let statusClass = 'bg-gray-100 text-gray-700';
            let statusIcon = '?';
            if (status === 'PASS') {
                statusClass = 'bg-green-100 text-green-700 border-l-4 border-green-500';
                statusIcon = '✓';
            } else if (status === 'FAIL') {
                statusClass = 'bg-red-100 text-red-700 border-l-4 border-red-500';
                statusIcon = '✗';
            } else if (status === 'TIMEOUT') {
                statusClass = 'bg-orange-100 text-orange-700 border-l-4 border-orange-500';
                statusIcon = '⏱';
            }
            
            modalContent.innerHTML = `
                <div class="space-y-6">
                    <!-- Status Banner -->
                    <div class="${statusClass} rounded-lg p-4">
                        <div class="flex items-center gap-3">
                            <span class="text-4xl">${statusIcon}</span>
                            <div>
                                <h3 class="text-2xl font-bold">${status}</h3>
                                <p class="text-sm opacity-75">Test execution status</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Execution Details Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">Monitor (NetID)</h4>
                            <p class="text-lg font-mono font-bold text-primary">${netid}</p>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">Test Case</h4>
                            <p class="text-lg font-semibold text-gray-700">${testName}</p>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">Duration</h4>
                            <p class="text-2xl font-bold text-blue-600">${duration}s</p>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">Exit Code</h4>
                            <p class="text-2xl font-bold text-gray-700">${exitCode}</p>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">Start Time</h4>
                            <p class="text-sm text-gray-700">${startTime}</p>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1">End Time</h4>
                            <p class="text-sm text-gray-700">${endTime}</p>
                        </div>
                    </div>
                    
                    <!-- Error Message -->
                    ${error !== 'None' ? `
                    <div class="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
                        <h4 class="text-sm font-semibold text-red-700 uppercase mb-2">Error Message</h4>
                        <pre class="text-sm text-red-900 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto">${escapeHtml(error)}</pre>
                    </div>
                    ` : ''}
                    
                    <!-- ChatGPT Verification Comment -->
                    ${verification ? `
                    <div class="bg-purple-50 border-l-4 border-purple-500 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="text-2xl">🤖</span>
                            <h4 class="text-sm font-semibold text-purple-700 uppercase">ChatGPT Verification Analysis</h4>
                        </div>
                        <div class="text-sm text-gray-800 whitespace-pre-wrap bg-white rounded p-4 overflow-x-auto max-h-96 leading-relaxed">${escapeHtml(verification)}</div>
                    </div>
                    ` : ''}
                    
                    <!-- Standard Output -->
                    <div class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
                        <h4 class="text-sm font-semibold text-blue-700 uppercase mb-2">Standard Output</h4>
                        <pre class="text-sm text-gray-800 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto max-h-96">${escapeHtml(stdout)}</pre>
                    </div>

                    <!-- Reference Monitor Source -->
                    <div class="bg-gray-50 border-l-4 border-gray-500 rounded-lg p-4">
                        <h4 class="text-sm font-semibold text-gray-700 uppercase mb-2">Reference Monitor Source</h4>
                        <div class="text-xs text-gray-500 mb-2">${details.monitor_path ? escapeHtml(details.monitor_path) : 'Path: N/A'}</div>
                        <pre class="text-xs text-gray-800 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto max-h-96">${escapeHtml(details.monitor_code || 'N/A')}</pre>
                    </div>

                    <!-- Attack Test Source -->
                    <div class="bg-gray-50 border-l-4 border-gray-500 rounded-lg p-4">
                        <h4 class="text-sm font-semibold text-gray-700 uppercase mb-2">Attack Test Source</h4>
                        <div class="text-xs text-gray-500 mb-2">${details.attack_path ? escapeHtml(details.attack_path) : 'Path: N/A'}</div>
                        <pre class="text-xs text-gray-800 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto max-h-96">${escapeHtml(details.attack_code || 'N/A')}</pre>
                    </div>
                    
                    <!-- Actions -->
                    <div class="space-y-4">
                        <!-- Annotation Actions (only show for failed tests, not timeouts) -->
                        ${status === 'FAIL' && !resultData.is_invalid_test ? `
                        <div class="bg-gray-100 rounded-lg p-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-3">Mark as:</h4>
                            <div class="flex gap-3 flex-wrap">
                                <button onclick="markAsResolved('${netid}', '${testName}', ${!resultData.is_resolved})" 
                                        class="px-4 py-2 ${resultData.is_resolved ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'} text-white font-semibold rounded-lg transition">
                                    ${resultData.is_resolved ? '✓ Resolved' : 'Mark Resolved'}
                                </button>
                                <button onclick="markAsTodo('${netid}', '${testName}', ${!resultData.is_todo})" 
                                        class="px-4 py-2 ${resultData.is_todo ? 'bg-gray-400' : 'bg-orange-500 hover:bg-orange-600'} text-white font-semibold rounded-lg transition">
                                    ${resultData.is_todo ? '📌 TODO' : 'Mark TODO'}
                                </button>
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- Invalid Test Action -->
                        <div class="bg-gray-100 rounded-lg p-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-3">Test Validity:</h4>
                            ${resultData.is_invalid_test ? `
                                <div class="mb-3">
                                    <div class="text-sm text-yellow-700 bg-yellow-50 rounded p-3 mb-2">
                                        <strong>⚠ Invalid Test</strong><br>
                                        Reason: ${escapeHtml(resultData.invalid_reason || 'No reason provided')}
                                    </div>
                                    <button onclick="markTestAsInvalid('${testName}', false)" 
                                            class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition">
                                        Mark as Valid
                                    </button>
                                </div>
                            ` : `
                                <button onclick="promptMarkTestAsInvalid('${testName}')" 
                                        class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white font-semibold rounded-lg transition">
                                    Mark Entire Test as Invalid
                                </button>
                            `}
                        </div>
                        
                        <!-- Close Button -->
                        <div class="flex justify-end">
                            <button onclick="closeDetailModal()" class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-lg transition">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            `;
            } catch (error) {
                // Show error state
                modalContent.innerHTML = `
                    <div class="flex items-center justify-center py-16">
                        <div class="text-center">
                            <div class="text-6xl mb-4">❌</div>
                            <div class="text-xl text-red-600 mb-4">Failed to load details</div>
                            <div class="text-sm text-gray-600">${escapeHtml(error.message)}</div>
                            <button onclick="closeDetailModal()" class="mt-6 px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-lg transition">
                                Close
                            </button>
                        </div>
                    </div>
                `;
            }
        }
        
        function closeDetailModal(event) {
            // Only close if clicking outside the modal or close button
            if (!event || event.target.id === 'detailModal' || event.type === 'undefined') {
                const modal = document.getElementById('detailModal');
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeDetailModal();
            }
        });
        
        function updateStats(data) {
            const totalMonitors = data.length;
            const totalPass = data.reduce((sum, m) => sum + m.pass_count, 0);
            const totalFail = data.reduce((sum, m) => sum + m.fail_count, 0);
            const totalTimeout = data.reduce((sum, m) => sum + m.timeout_count, 0);
            
            document.getElementById('stats').innerHTML = `
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="bg-blue-50 rounded-xl p-6 border-l-4 border-blue-500 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Monitors</div>
                        <div class="text-4xl font-bold text-blue-600">${totalMonitors}</div>
                    </div>
                    <div class="bg-green-50 rounded-xl p-6 border-l-4 border-green-500 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Total Passes</div>
                        <div class="text-4xl font-bold text-green-600">${totalPass}</div>
                    </div>
                    <div class="bg-red-50 rounded-xl p-6 border-l-4 border-red-500 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Total Failures</div>
                        <div class="text-4xl font-bold text-red-600">${totalFail}</div>
                    </div>
                    <div class="bg-orange-50 rounded-xl p-6 border-l-4 border-orange-500 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Total Timeouts</div>
                        <div class="text-4xl font-bold text-orange-600">${totalTimeout}</div>
                    </div>
                </div>
            `;
        }
        
        function formatDuration(seconds) {
            if (!seconds) return 'N/A';
            return seconds.toFixed(2) + 's';
        }
        
        function formatTime(isoString) {
            if (!isoString) return 'N/A';
            const date = new Date(isoString);
            return date.toLocaleString();
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            return text.replace(/&/g, '&amp;')
                       .replace(/</g, '&lt;')
                       .replace(/>/g, '&gt;')
                       .replace(/"/g, '&quot;')
                       .replace(/'/g, '&#039;');
        }
        
        function calculateTestStats(data, testsToShow) {
            // Calculate stats for each test
            const testStats = {};
            testsToShow.forEach(test => {
                let passCount = 0;
                let failCount = 0;
                let timeoutCount = 0;
                
                data.forEach(monitor => {
                    const result = monitor.results[test];
                    if (result) {
                        if (result.status === 'PASS') passCount++;
                        else if (result.status === 'TIMEOUT') timeoutCount++;
                        else if (result.status === 'FAIL') failCount++;
                    }
                });
                
                testStats[test] = {
                    pass_count: passCount,
                    fail_count: failCount,
                    timeout_count: timeoutCount,
                    total: data.length
                };
            });
            
            return testStats;
        }
        
        function sortTests(testsToShow, data, sortBy, sortOrder) {
            const testStats = calculateTestStats(data, testsToShow);
            
            if (sortBy === 'name') {
                // Already sorted by name
                return testsToShow;
            }
            
            const sorted = [...testsToShow].sort((a, b) => {
                const statA = testStats[a][sortBy] || 0;
                const statB = testStats[b][sortBy] || 0;
                
                if (sortOrder === 'desc') {
                    return statB - statA;
                } else {
                    return statA - statB;
                }
            });
            
            return sorted;
        }
        
        function updateTable(data, testFilter = '', sortTestsBy = 'name', sortOrder = 'desc') {
            const table = document.getElementById('dataTable');
            
            if (data.length === 0) {
                table.innerHTML = '<tr><td class="text-center py-16 text-gray-400 text-xl" colspan="10">No data matches your filters</td></tr>';
                return;
            }
            
            // Filter tests if test filter is applied
            let testsToShow = allTests;
            if (testFilter) {
                testsToShow = allTests.filter(t => t.toLowerCase().includes(testFilter.toLowerCase()));
            }
            
            // Sort tests if needed
            testsToShow = sortTests(testsToShow, data, sortTestsBy, sortOrder);
            
            // Calculate test stats for tooltips
            const testStats = calculateTestStats(data, testsToShow);
            
            // Build table header - always show all tests
            let headerHTML = '<thead class="bg-gray-100 sticky top-0"><tr>';
            headerHTML += '<th class="px-3 py-3 text-left text-xs font-semibold text-gray-700 cursor-pointer hover:bg-gray-200 transition border-r-4 border-gray-400">Monitor (hover for stats)</th>';
            
            // Always show all tests
            testsToShow.forEach(test => {
                const shortName = test.replace('.r2py', '').replace('test', 't');
                const stats = testStats[test];
                headerHTML += `<th class="px-1 py-3 text-center text-xs font-medium text-gray-600 border-r border-gray-200 relative group" style="min-width: 50px; writing-mode: vertical-rl; transform: rotate(180deg);" title="${test}">
                    ${shortName}
                    <div class="hidden group-hover:block absolute z-50 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-xl" 
                         style="left: 50%; transform: translateX(-50%) rotate(180deg); writing-mode: horizontal-tb; top: 100%; margin-top: 8px; min-width: 200px;">
                        <strong>${test}</strong><br>
                        Pass: ${stats.pass_count}<br>
                        Fail: ${stats.fail_count}<br>
                        Timeout: ${stats.timeout_count}<br>
                        Total: ${stats.total}
                    </div>
                </th>`;
            });
            
            headerHTML += '</tr></thead>';
            
            // Build table body
            let bodyHTML = '<tbody class="divide-y divide-gray-200 text-xs">';
            data.forEach(monitor => {
                // Build NetID cell with hover tooltip
                const netidTooltip = `
                    <strong>Monitor: ${monitor.netid}</strong><br>
                    <span class="text-green-400">✓ Pass: ${monitor.pass_count}</span><br>
                    <span class="text-red-400">✗ Fail: ${monitor.fail_count}</span><br>
                    <span class="text-orange-400">⏱ Timeout: ${monitor.timeout_count}</span><br>
                    <strong>Total: ${monitor.total}</strong>
                `;
                
                bodyHTML += `<tr class="hover:bg-gray-50 transition">`;
                bodyHTML += `<td class="px-3 py-2 font-semibold text-primary font-mono border-r-4 border-gray-400 relative group cursor-pointer">
                    ${monitor.netid}
                    <div class="hidden group-hover:block absolute z-50 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-xl" 
                         style="left: 100%; margin-left: 8px; top: 50%; transform: translateY(-50%); min-width: 180px;">
                        ${netidTooltip}
                        <div class="absolute top-1/2 right-full transform -translate-y-1/2 border-8 border-transparent border-r-gray-900"></div>
                    </div>
                </td>`;
                
                // Show all tests as matrix cells
                testsToShow.forEach(test => {
                    const resultData = monitor.results[test];
                    const status = resultData ? resultData.status : 'N/A';
                    
                    // Check annotation states
                    const isInvalidTest = resultData && resultData.is_invalid_test;
                    const isResolved = resultData && resultData.is_resolved;
                    const isTodo = resultData && resultData.is_todo;
                    
                    // Determine colors based on status and annotations
                    let bgClass = 'bg-gray-200';
                    let textClass = 'text-gray-600';
                    let symbol = '?';
                    let borderClass = '';
                    
                    // If test is invalid, always show yellow regardless of PASS/FAIL
                    if (isInvalidTest) {
                        bgClass = 'bg-yellow-400 hover:bg-yellow-500';
                        textClass = 'text-gray-900';
                        symbol = '⚠';
                    } else if (status === 'PASS') {
                        bgClass = 'bg-green-500 hover:bg-green-600';
                        textClass = 'text-white';
                        symbol = '✓';
                    } else if (status === 'TIMEOUT') {
                        // Timeouts show blue by default (expected behavior)
                        bgClass = 'bg-blue-500 hover:bg-blue-600';
                        textClass = 'text-white';
                        symbol = '⏱';
                    } else if (status === 'FAIL') {
                        // Failed tests - check if resolved or TODO
                        if (isResolved) {
                            bgClass = 'bg-blue-500 hover:bg-blue-600';
                            textClass = 'text-white';
                            symbol = '✓';
                            borderClass = 'ring-2 ring-blue-300';
                        } else if (isTodo) {
                            bgClass = 'bg-orange-500 hover:bg-orange-600';
                            textClass = 'text-white';
                            symbol = '📌';
                            borderClass = 'ring-2 ring-orange-300';
                        } else {
                            bgClass = 'bg-red-500 hover:bg-red-600';
                            textClass = 'text-white';
                            symbol = '✗';
                        }
                    }
                    
                    // Build tooltip content with test name, monitor name, and status type
                    let tooltipHTML = '';
                    if (resultData) {
                        // Header with test and monitor info
                        tooltipHTML = `<div class="font-bold text-yellow-300 mb-2">📋 ${test}</div>`;
                        tooltipHTML += `<div class="text-xs text-gray-300 mb-2">Monitor: ${monitor.netid}</div>`;
                        tooltipHTML += `<div class="border-t border-gray-700 pt-2 mb-2"></div>`;
                        
                        // Status with color and description
                        let statusDisplay = '';
                        if (status === 'PASS') {
                            statusDisplay = '<span class="text-green-400 font-bold">✓ PASS</span>';
                        } else if (status === 'FAIL') {
                            if (isResolved) {
                                statusDisplay = '<span class="text-blue-400 font-bold">✓ FAIL (Resolved)</span>';
                            } else if (isTodo) {
                                statusDisplay = '<span class="text-orange-400 font-bold">📌 FAIL (TODO)</span>';
                            } else {
                                statusDisplay = '<span class="text-red-400 font-bold">✗ FAIL</span>';
                            }
                        } else if (status === 'TIMEOUT') {
                            statusDisplay = '<span class="text-blue-400 font-bold">⏱ TIMEOUT</span>';
                        } else {
                            statusDisplay = `<span class="text-gray-400">${status}</span>`;
                        }
                        
                        tooltipHTML += `Status: ${statusDisplay}<br>`;
                        
                        // Invalid test warning
                        if (isInvalidTest) {
                            tooltipHTML += `<div class="bg-yellow-600 text-white px-2 py-1 rounded text-xs mt-1 mb-1">⚠ Invalid Test</div>`;
                        }
                    } else {
                        tooltipHTML = `<div class="font-bold text-yellow-300">${test}</div>`;
                        tooltipHTML += `<div class="text-xs text-gray-300">Monitor: ${monitor.netid}</div>`;
                        tooltipHTML += `<div class="text-gray-400 mt-2">No data available</div>`;
                    }
                    
                    // Store minimal data as JSON string in data attribute
                    const cellData = JSON.stringify({
                        status: status,
                        is_resolved: resultData?.is_resolved || false,
                        is_todo: resultData?.is_todo || false,
                        is_invalid_test: resultData?.is_invalid_test || false,
                        invalid_reason: resultData?.invalid_reason || ''
                    });
                    
                    bodyHTML += `<td class="px-1 py-2 text-center border-r border-gray-200">
                        <div class="${bgClass} ${textClass} ${borderClass} rounded px-2 py-1 cursor-pointer transition font-bold relative group"
                             title="${status} (click for details)"
                             onclick='openDetailModal("${monitor.netid}", "${test}", ${cellData})'>
                            ${symbol}
                            <div class="hidden group-hover:block absolute z-50 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-xl pointer-events-none" 
                                 style="left: 50%; transform: translateX(-50%); bottom: 100%; margin-bottom: 8px; min-width: 250px; max-width: 350px;">
                                ${tooltipHTML}
                                <div class="text-xs mt-2 pt-2 border-t border-gray-700 text-center italic">Click for full details</div>
                                <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-8 border-transparent border-t-gray-900"></div>
                            </div>
                        </div>
                    </td>`;
                });
                
                bodyHTML += `</tr>`;
            });
            bodyHTML += '</tbody>';
            
            table.innerHTML = headerHTML + bodyHTML;
        }
        
        function applyFilters() {
            const monitorFilter = document.getElementById('monitorFilter').value.toLowerCase();
            const testFilter = document.getElementById('testFilter').value.toLowerCase();
            const sortMonitorsBy = document.getElementById('sortMonitorsBy').value;
            const sortTestsBy = document.getElementById('sortTestsBy').value;
            const sortOrder = document.getElementById('sortOrder').value;
            
            // Save filter state to localStorage
            saveFilterState();
            
            // Filter by monitor
            let filtered = allData.filter(m => {
                if (monitorFilter && !m.netid.toLowerCase().includes(monitorFilter)) {
                    return false;
                }
                
                // Filter by test (check if any test matching the filter has results)
                if (testFilter) {
                    const matchingTests = allTests.filter(t => t.toLowerCase().includes(testFilter));
                    if (matchingTests.length === 0) return false;
                }
                
                return true;
            });
            
            // Sort monitors
            filtered.sort((a, b) => {
                let valA = a[sortMonitorsBy];
                let valB = b[sortMonitorsBy];
                
                if (typeof valA === 'string') {
                    valA = valA.toLowerCase();
                    valB = valB.toLowerCase();
                }
                
                if (sortOrder === 'asc') {
                    return valA > valB ? 1 : -1;
                } else {
                    return valA < valB ? 1 : -1;
                }
            });
            
            currentData = filtered;
            updateStats(filtered);
            updateTable(filtered, testFilter, sortTestsBy, sortOrder);
        }
        
        // Event listeners
        document.getElementById('monitorFilter').addEventListener('input', applyFilters);
        document.getElementById('testFilter').addEventListener('input', applyFilters);
        document.getElementById('sortMonitorsBy').addEventListener('change', applyFilters);
        document.getElementById('sortTestsBy').addEventListener('change', applyFilters);
        document.getElementById('sortOrder').addEventListener('change', applyFilters);
        
        // Restore saved filter state on page load
        restoreFilterState();
        
        // API call functions with in-place updates (no page reload)
        async function markAsResolved(netid, testName, resolved) {
            try {
                const response = await fetch('/api/mark_resolved', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({netid, test_name: testName, resolved})
                });
                const data = await response.json();
                if (data.success) {
                    // Update in-memory data
                    const monitor = allData.find(m => m.netid === netid);
                    if (monitor && monitor.results[testName]) {
                        monitor.results[testName].is_resolved = resolved;
                        if (resolved) {
                            monitor.results[testName].is_todo = false;
                        }
                    }
                    
                    // Re-render table without page reload
                    applyFilters();
                    
                    // Close modal and show success
                    closeDetailModal();
                    showToast(data.message, 'success');
                } else {
                    showToast('Error: ' + data.message, 'error');
                }
            } catch (error) {
                showToast('Network error: ' + error, 'error');
            }
        }
        
        async function markAsTodo(netid, testName, todo) {
            try {
                const response = await fetch('/api/mark_todo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({netid, test_name: testName, todo})
                });
                const data = await response.json();
                if (data.success) {
                    // Update in-memory data
                    const monitor = allData.find(m => m.netid === netid);
                    if (monitor && monitor.results[testName]) {
                        monitor.results[testName].is_todo = todo;
                        if (todo) {
                            monitor.results[testName].is_resolved = false;
                        }
                    }
                    
                    // Re-render table without page reload
                    applyFilters();
                    
                    // Close modal and show success
                    closeDetailModal();
                    showToast(data.message, 'success');
                } else {
                    showToast('Error: ' + data.message, 'error');
                }
            } catch (error) {
                showToast('Network error: ' + error, 'error');
            }
        }
        
        function promptMarkTestAsInvalid(testName) {
            const reason = prompt(`Mark "${testName}" as invalid for ALL monitors.\\n\\nPlease provide a reason:`);
            if (reason !== null && reason.trim()) {
                markTestAsInvalid(testName, true, reason.trim());
            }
        }
        
        async function markTestAsInvalid(testName, invalid, reason = '') {
            try {
                const response = await fetch('/api/mark_invalid_test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({test_name: testName, invalid, reason})
                });
                const data = await response.json();
                if (data.success) {
                    // Update in-memory data for ALL monitors
                    allData.forEach(monitor => {
                        if (monitor.results[testName]) {
                            monitor.results[testName].is_invalid_test = invalid;
                            monitor.results[testName].invalid_reason = reason;
                        }
                    });
                    
                    // Re-render table without page reload
                    applyFilters();
                    
                    // Close modal and show success
                    closeDetailModal();
                    showToast(data.message, 'success');
                } else {
                    showToast('Error: ' + data.message, 'error');
                }
            } catch (error) {
                showToast('Network error: ' + error, 'error');
            }
        }
        
        // Toast notification system
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
            
            toast.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            // Fade out and remove after 3 seconds
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // Initial render
        applyFilters();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page showing the data table"""
    monitors_data, test_names, headers, annotations = load_data()
    
    if monitors_data is None:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-red-500 to-pink-600 min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl p-12 max-w-2xl text-center">
                <div class="text-6xl mb-4">⚠️</div>
                <h1 class="text-3xl font-bold text-gray-800 mb-4">CSV File Not Found</h1>
                <p class="text-gray-600 mb-2">Please ensure <code class="bg-gray-100 px-2 py-1 rounded">submit/result/test_results_matrix.csv</code> exists.</p>
                <p class="text-gray-600 mb-6">Run <code class="bg-gray-100 px-2 py-1 rounded">python3 run_all_tests.py</code> first to generate the data.</p>
                <a href="/" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg transition">Refresh</a>
            </div>
        </body>
        </html>
        """
    
    # Use simple string replacement for data injection
    html = HTML_TEMPLATE.replace('{{ data|tojson }}', json.dumps(monitors_data))
    html = html.replace('{{ tests|tojson }}', json.dumps(test_names))
    
    return html

@app.get("/api/data")
async def api_data():
    """API endpoint to get raw data as JSON"""
    monitors_data, test_names, headers, annotations = load_data()
    
    if monitors_data is None:
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    return {
        'monitors': monitors_data,
        'test_names': test_names
    }

class MarkResolvedRequest(BaseModel):
    netid: str
    test_name: str
    resolved: bool

class MarkTodoRequest(BaseModel):
    netid: str
    test_name: str
    todo: bool

class MarkInvalidTestRequest(BaseModel):
    test_name: str
    invalid: bool
    reason: str = ""

@app.post("/api/mark_resolved")
async def mark_resolved(request: MarkResolvedRequest):
    """Mark a test result as resolved or unresolved"""
    annotations = load_annotations()
    key = (request.netid, request.test_name)
    
    if request.resolved:
        annotations['resolved'][key] = True
        # Remove from TODO if marking as resolved
        annotations['todo'].pop(key, None)
    else:
        annotations['resolved'].pop(key, None)
    
    if save_annotations(annotations):
        return {"success": True, "message": f"Marked {request.netid}/{request.test_name} as {'resolved' if request.resolved else 'unresolved'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save annotations")

@app.post("/api/mark_todo")
async def mark_todo(request: MarkTodoRequest):
    """Mark a test result as TODO or remove TODO"""
    annotations = load_annotations()
    key = (request.netid, request.test_name)
    
    if request.todo:
        annotations['todo'][key] = True
        # Remove from resolved if marking as TODO
        annotations['resolved'].pop(key, None)
    else:
        annotations['todo'].pop(key, None)
    
    if save_annotations(annotations):
        return {"success": True, "message": f"Marked {request.netid}/{request.test_name} as {'TODO' if request.todo else 'not TODO'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save annotations")

@app.post("/api/mark_invalid_test")
async def mark_invalid_test(request: MarkInvalidTestRequest):
    """Mark an entire test as invalid (affects all monitors)"""
    annotations = load_annotations()
    
    if request.invalid:
        if not request.reason:
            raise HTTPException(status_code=400, detail="Reason is required when marking test as invalid")
        annotations['invalid_tests'][request.test_name] = request.reason
    else:
        annotations['invalid_tests'].pop(request.test_name, None)
    
    if save_annotations(annotations):
        return {"success": True, "message": f"Marked {request.test_name} as {'invalid' if request.invalid else 'valid'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save annotations")

@app.get("/api/annotations")
async def get_annotations():
    """Get all annotations"""
    annotations = load_annotations()
    # Convert tuple keys to strings for JSON
    return {
        'resolved': [f"{k[0]}|{k[1]}" for k in annotations['resolved'].keys()],
        'todo': [f"{k[0]}|{k[1]}" for k in annotations['todo'].keys()],
        'invalid_tests': annotations['invalid_tests']
    }

@app.get("/api/test_details/{netid}/{test_name}")
async def get_test_details(netid: str, test_name: str):
    """Load detailed execution info, logs, and source code on-demand"""
    # Load execution logs
    execution_logs = load_execution_logs()
    exec_info = execution_logs.get((netid, test_name), {})
    
    if not exec_info:
        raise HTTPException(status_code=404, detail="Test execution not found")
    
    # Derive file paths
    monitor_filename = exec_info.get('monitor_file')
    test_filename = exec_info.get('test_file')
    
    monitor_path = None
    test_path = None
    monitor_code = None
    attack_code = None
    
    if monitor_filename:
        monitor_path = os.path.join('submit', 'reference_monitor', monitor_filename)
        try:
            if os.path.exists(monitor_path):
                with open(monitor_path, 'r', encoding='utf-8', errors='replace') as mf:
                    monitor_code = mf.read()
        except Exception as e:
            monitor_code = f"Error reading file: {e}"
    
    if test_filename:
        test_path = os.path.join('submit', 'general_tests', test_filename)
        try:
            if os.path.exists(test_path):
                with open(test_path, 'r', encoding='utf-8', errors='replace') as tf:
                    attack_code = tf.read()
        except Exception as e:
            attack_code = f"Error reading file: {e}"
    
    # Load verification result on-demand
    verification_results = load_verification_results()
    verification = verification_results.get(test_name.rstrip('.r2py'), '')
    
    return {
        'duration': exec_info.get('duration_seconds'),
        'exit_code': exec_info.get('exit_code'),
        'error': exec_info.get('error'),
        'stdout': exec_info.get('stdout', ''),
        'stderr': exec_info.get('stderr', ''),
        'start_time': exec_info.get('start_time'),
        'end_time': exec_info.get('end_time'),
        'monitor_path': monitor_path,
        'attack_path': test_path,
        'monitor_code': monitor_code,
        'attack_code': attack_code,
        'verification': verification
    }

if __name__ == '__main__':
    HOST = "0.0.0.0"    
    PORT = 8001
    print("=" * 80)
    print("Test Results Data Visualizer (FastAPI + Tailwind CSS)")
    print("=" * 80)
    print(f"CSV Source: {CSV_PATH}")
    print(f"Starting web server on http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    uvicorn.run(app, host=HOST, port=PORT)


