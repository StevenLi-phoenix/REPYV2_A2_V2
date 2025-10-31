# Test Annotation System

## Overview
The web visualizer now includes a comprehensive annotation system to track test resolution status and mark invalid tests.

## Features

### 1. **Mark Failed Tests as Resolved**
- **Color**: Blue with checkmark (✓)
- **Use Case**: When you've fixed the issue causing a test to fail
- **Action**: Click on a failed (red) test cell → Click "Mark Resolved"
- **Effect**: Turns blue, indicating the issue has been addressed

### 2. **Mark Failed Tests as TODO**
- **Color**: Orange with pin icon (📌)
- **Use Case**: When you know about the failure and plan to fix it later
- **Action**: Click on a failed (red) test cell → Click "Mark TODO"
- **Effect**: Turns orange, indicating it's on your to-do list

### 3. **Mark Entire Test as Invalid**
- **Color**: Yellow with warning icon (⚠)
- **Use Case**: When the test itself is incorrect or doesn't align with specs
- **Action**: Click any cell for that test → Click "Mark Entire Test as Invalid" → Provide reason
- **Effect**: 
  - **ALL monitors** for that test turn yellow
  - Applies to all PASS/FAIL results
  - Reason is stored and displayed
- **Important**: This marks the TEST as invalid, not individual monitor+test combinations

## Color Legend

| Color | Symbol | Meaning |
|-------|--------|---------|
| 🟢 Green | ✓ | Test passed |
| 🔴 Red | ✗ | Test failed (needs attention) |
| 🔵 Blue | ⏱ or ✓ | Timeout (expected) OR Test failed but marked as resolved |
| 🟠 Orange | 📌 (with ring) | Test failed and marked as TODO |
| 🟡 Yellow | ⚠ | Invalid test (applies to all monitors) |

## How It Works

### Data Storage
- Annotations are stored in `test_annotations.json`
- Structure:
```json
{
  "resolved": {
    "sl00000|aa11931_attackcase15": true
  },
  "todo": {
    "sl00000|aa12037_attackcase14": true
  },
  "invalid_tests": {
    "ac12757_attackcase9": "Test violates Section G by producing unexpected output"
  }
}
```

### State Management
- **Resolved** and **TODO** are mutually exclusive
  - Marking as resolved removes TODO status
  - Marking as TODO removes resolved status
- **Invalid test** overrides PASS/FAIL colors
  - All cells for that test show yellow regardless of pass/fail status

### API Endpoints

#### Mark Resolved
```bash
POST /api/mark_resolved
{
  "netid": "sl00000",
  "test_name": "aa11931_attackcase15",
  "resolved": true
}
```

#### Mark TODO
```bash
POST /api/mark_todo
{
  "netid": "sl00000",
  "test_name": "aa12037_attackcase14",
  "todo": true
}
```

#### Mark Invalid Test
```bash
POST /api/mark_invalid_test
{
  "test_name": "ac12757_attackcase9",
  "invalid": true,
  "reason": "Test violates Section G by producing unexpected output"
}
```

#### Get All Annotations
```bash
GET /api/annotations
```

## Workflow Example

### Scenario 1: Fixing Failed Tests
1. Run tests → See red cells for failures
2. Investigate and fix the issue in your monitor
3. Click the red cell → "Mark Resolved" → Turns blue
4. Re-run tests to confirm the fix works

### Scenario 2: Prioritizing Work
1. Review all failed tests (red cells)
2. For urgent issues: Mark as TODO (turns orange)
3. Work through orange cells systematically
4. Mark as resolved when complete (turns blue)

### Scenario 3: Invalid Test Cases
1. Discover a test that doesn't follow specifications
2. Click any cell for that test
3. "Mark Entire Test as Invalid" → Provide reason
4. All cells for that test turn yellow across all monitors
5. Document the issue for the test author

## Benefits

1. **Visual Progress Tracking**: See at a glance which issues have been addressed
2. **Prioritization**: Mark TODO items to focus your efforts
3. **Test Quality**: Identify and flag invalid tests
4. **Team Collaboration**: Share annotation file to sync status across team
5. **Audit Trail**: Reasons for invalid tests are documented

## Integration with ChatGPT Verification

When ChatGPT verification results are available:
- Verification comments help identify invalid tests
- Use "Mark as Invalid" for tests flagged by ChatGPT as incorrect
- Document ChatGPT's reasoning in the invalid test reason

## File Management

### Backup
```bash
cp test_annotations.json test_annotations.backup.json
```

### Share with Team
```bash
git add test_annotations.json
git commit -m "Update test annotations"
git push
```

### Reset All Annotations
```bash
rm test_annotations.json
# Restart web server to create fresh file
```

## Tips

1. **Use Invalid Test Sparingly**: Only for tests that are genuinely incorrect
2. **Provide Detailed Reasons**: Help others understand why a test is invalid
3. **Review Regularly**: Check resolved items after re-running tests
4. **Document Patterns**: If multiple tests are invalid for the same reason, note it

## Troubleshooting

### Annotations Not Saving
- Check file permissions on `test_annotations.json`
- Ensure web server has write access to the directory

### Colors Not Updating
- Refresh the page after marking items
- Check browser console for JavaScript errors

### Invalid Test Not Affecting All Monitors
- Verify you're using "Mark Entire Test as Invalid" (not resolved/TODO)
- Check that the test name matches exactly

