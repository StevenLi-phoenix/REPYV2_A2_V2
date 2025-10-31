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
import uvicorn

app = FastAPI(title="Test Results Data Visualizer")

CSV_PATH = "submit/result/test_results_matrix.csv"
JSON_PATH = "submit/result/test_execution_logs.json"
VERIFICATION_PATH = "verification_results.json"

def load_verification_results():
    """Load ChatGPT verification comments from JSON"""
    if not Path(VERIFICATION_PATH).exists():
        return {}
    
    try:
        with open(VERIFICATION_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load verification results: {e}")
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
    """Load CSV data and return structured data with execution details"""
    if not Path(CSV_PATH).exists():
        return None, [], [], {}, {}
    
    # Load execution logs for detailed hover information
    execution_logs = load_execution_logs()
    
    # Load verification results from ChatGPT
    verification_results = load_verification_results()
    
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
            
            # Build results dict with execution details and verification comments
            results_dict = {}
            for test_name, result in zip(test_names, results):
                exec_info = execution_logs.get((netid, test_name), {})

                # Derive file paths
                monitor_filename = exec_info.get('monitor_file')
                test_path = exec_info.get('test_path')
                monitor_path = None
                if monitor_filename:
                    monitor_path = os.path.join('submit', 'reference_monitor', monitor_filename)

                # Read source code (UTF-8 with replacement to avoid decode errors)
                monitor_code = None
                attack_code = None
                try:
                    if monitor_path and os.path.exists(monitor_path):
                        with open(monitor_path, 'r', encoding='utf-8', errors='replace') as mf:
                            monitor_code = mf.read()
                except Exception:
                    monitor_code = None
                try:
                    if test_path and os.path.exists(test_path):
                        with open(test_path, 'r', encoding='utf-8', errors='replace') as tf:
                            attack_code = tf.read()
                except Exception:
                    attack_code = None

                # Get verification comment for this test case (matched by test_name)
                verification_comment = verification_results.get(test_name, '')
                
                results_dict[test_name] = {
                    'status': result,
                    'duration': exec_info.get('duration_seconds'),
                    'exit_code': exec_info.get('exit_code'),
                    'error': exec_info.get('error'),
                    'stdout': exec_info.get('stdout', ''),
                    'start_time': exec_info.get('start_time'),
                    'end_time': exec_info.get('end_time'),
                    'monitor_path': monitor_path,
                    'attack_path': test_path,
                    'monitor_code': monitor_code,
                    'attack_code': attack_code,
                    'verification': verification_comment
                }
            
            monitors_data.append({
                'netid': netid,
                'results': results_dict,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'timeout_count': timeout_count,
                'total': total
            })
    
    return monitors_data, test_names, headers, execution_logs, verification_results

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
            <div class="flex items-center justify-center gap-6 text-sm flex-wrap">
                <div class="flex items-center gap-2">
                    <div class="bg-green-500 text-white rounded px-3 py-1 font-bold">✓</div>
                    <span class="text-gray-700 font-medium">Pass</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="bg-red-500 text-white rounded px-3 py-1 font-bold">✗</div>
                    <span class="text-gray-700 font-medium">Fail / Timeout</span>
                </div>
                <div class="h-6 w-px bg-gray-300"></div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-600 italic">💡 Hover NetID for stats</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-600 italic">💡 Hover headers for counts</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-600 italic">💡 Hover cells for preview</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-purple-600 font-semibold italic">👆 Click cells for full details</span>
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
        
        function openDetailModal(netid, testName, resultData) {
            const modal = document.getElementById('detailModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalContent = document.getElementById('modalContent');
            
            // Set title
            modalTitle.textContent = `${netid} - ${testName}`;
            
            // Build content
            const status = resultData ? resultData.status : 'N/A';
            const duration = resultData && resultData.duration ? resultData.duration.toFixed(3) : 'N/A';
            const exitCode = resultData && resultData.exit_code !== null ? resultData.exit_code : 'N/A';
            const error = resultData && resultData.error ? resultData.error : 'None';
            const stdout = resultData && resultData.stdout ? resultData.stdout : '(empty)';
            const startTime = resultData && resultData.start_time ? formatTime(resultData.start_time) : 'N/A';
            const endTime = resultData && resultData.end_time ? formatTime(resultData.end_time) : 'N/A';
            const verification = resultData && resultData.verification ? resultData.verification : '';
            
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
                        <div class="text-xs text-gray-500 mb-2">${resultData && resultData.monitor_path ? escapeHtml(resultData.monitor_path) : 'Path: N/A'}</div>
                        <pre class="text-xs text-gray-800 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto max-h-96">${escapeHtml(resultData && resultData.monitor_code ? resultData.monitor_code : 'N/A')}</pre>
                    </div>

                    <!-- Attack Test Source -->
                    <div class="bg-gray-50 border-l-4 border-gray-500 rounded-lg p-4">
                        <h4 class="text-sm font-semibold text-gray-700 uppercase mb-2">Attack Test Source</h4>
                        <div class="text-xs text-gray-500 mb-2">${resultData && resultData.attack_path ? escapeHtml(resultData.attack_path) : 'Path: N/A'}</div>
                        <pre class="text-xs text-gray-800 whitespace-pre-wrap font-mono bg-white rounded p-3 overflow-x-auto max-h-96">${escapeHtml(resultData && resultData.attack_code ? resultData.attack_code : 'N/A')}</pre>
                    </div>
                    
                    <!-- Actions -->
                    <div class="flex justify-end gap-3">
                        <button onclick="closeDetailModal()" class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-lg transition">
                            Close
                        </button>
                    </div>
                </div>
            `;
            
            // Show modal
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
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
                    
                    // Determine colors: green for PASS, red for FAIL/TIMEOUT
                    let bgClass = 'bg-gray-200';
                    let textClass = 'text-gray-600';
                    let symbol = '?';
                    
                    if (status === 'PASS') {
                        bgClass = 'bg-green-500 hover:bg-green-600';
                        textClass = 'text-white';
                        symbol = '✓';
                    } else if (status === 'FAIL' || status === 'TIMEOUT') {
                        bgClass = 'bg-red-500 hover:bg-red-600';
                        textClass = 'text-white';
                        symbol = '✗';
                    }
                    
                    // Build tooltip content
                    let tooltipHTML = '';
                    if (resultData) {
                        tooltipHTML = `<strong>${test}</strong><br>`;
                        tooltipHTML += `Status: <strong>${status}</strong><br>`;
                        tooltipHTML += `Duration: ${formatDuration(resultData.duration)}<br>`;
                        tooltipHTML += `Exit Code: ${resultData.exit_code !== null ? resultData.exit_code : 'N/A'}<br>`;
                        if (resultData.error) {
                            tooltipHTML += `Error: ${escapeHtml(resultData.error).substring(0, 100)}...<br>`;
                        }
                        if (resultData.stdout && resultData.stdout.length > 0) {
                            tooltipHTML += `Output: ${escapeHtml(resultData.stdout).substring(0, 100)}...<br>`;
                        }
                    } else {
                        tooltipHTML = `${test}<br>No data available`;
                    }
                    
                    // Create a unique ID for this cell to store data
                    const cellId = `cell_${monitor.netid}_${test}`.replace(/[^a-zA-Z0-9_]/g, '_');
                    
                    // Store result data in a data attribute
                    if (resultData) {
                        window[cellId] = resultData;
                    }
                    
                    bodyHTML += `<td class="px-1 py-2 text-center border-r border-gray-200">
                        <div class="${bgClass} ${textClass} rounded px-2 py-1 cursor-pointer transition font-bold relative group"
                             title="${status} (click for details)"
                             onclick='openDetailModal("${monitor.netid}", "${test}", window["${cellId}"])'>
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
        
        // Initial render
        applyFilters();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page showing the data table"""
    monitors_data, test_names, headers, execution_logs, verification_results = load_data()
    
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
    monitors_data, test_names, headers, execution_logs, verification_results = load_data()
    
    if monitors_data is None:
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    return {
        'monitors': monitors_data,
        'test_names': test_names
    }

if __name__ == '__main__':
    print("=" * 80)
    print("Test Results Data Visualizer (FastAPI + Tailwind CSS)")
    print("=" * 80)
    print(f"CSV Source: {CSV_PATH}")
    print("Starting web server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8001)

