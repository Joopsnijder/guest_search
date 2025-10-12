# VSCode Testing Guide

## Setup Complete ✅

Your VSCode environment is now fully configured for testing! Here's how to use it.

## Test Discovery

VSCode will automatically discover all 148 tests when you open the project.

### View Tests in VSCode

1. **Open the Testing Panel:**
   - Click the flask/beaker icon in the left sidebar (🧪)
   - Or press `Cmd+Shift+P` and search for "Test: Focus on Test Explorer View"

2. **You should see:**
   ```
   📁 tests/
   ├── 📄 test_api_integration.py (10 tests)
   ├── 📄 test_config.py (22 tests)
   ├── 📄 test_conversation_flow.py (14 tests)
   ├── 📄 test_date_logic.py (24 tests)
   ├── 📄 test_file_operations.py (18 tests)
   ├── 📄 test_json_parsing.py (17 tests)
   ├── 📄 test_search_providers.py (23 tests)
   └── 📄 test_web_scraping.py (20 tests)
   ```

### Refresh Test Discovery

If tests don't appear, click the "🔄 Refresh Tests" button in the Testing panel.

---

## Running Tests

### From the Test Explorer (Recommended)

1. **Run all tests:** Click the ▶️ icon at the top of the Test Explorer
2. **Run a test file:** Hover over a file and click ▶️
3. **Run a test class:** Expand a file, hover over a class, click ▶️
4. **Run a single test:** Expand a class, hover over a test, click ▶️

### From Within a Test File

1. Open any test file (e.g., `tests/test_config.py`)
2. You'll see ▶️ icons in the gutter next to each test function
3. Click the icon to run that specific test
4. Click the 🐛 icon to debug the test

### Using Keyboard Shortcuts

- **Run test at cursor:** Place cursor in a test function, press `Cmd+Shift+P`, search "Test: Run Test at Cursor"
- **Debug test at cursor:** Place cursor in a test function, press `Cmd+Shift+P`, search "Test: Debug Test at Cursor"

### Using Tasks (Terminal-based)

Press `Cmd+Shift+P` → "Tasks: Run Task" → Choose:
- **Run All Tests** - Runs full test suite
- **Run Fast Tests** - Runs only config and date logic tests (~2 seconds)
- **Run Tests with Coverage** - Generates HTML coverage report
- **Run Current Test File** - Runs tests in the active file
- **Collect Tests** - Shows all discoverable tests
- **Run Tests (Stop on First Failure)** - Stops at first error

---

## Debugging Tests

### Method 1: Debug from Test Explorer

1. Hover over any test in the Test Explorer
2. Click the 🐛 debug icon
3. Set breakpoints in your code
4. Step through with F10/F11

### Method 2: Debug from Code

1. Open a test file
2. Set breakpoints by clicking in the gutter (red dot appears)
3. Click the 🐛 icon next to the test function
4. Or press F5 and select "Python: Current Test File"

### Method 3: Use Launch Configuration

1. Press F5 or click "Run and Debug" in sidebar
2. Select from dropdown:
   - **Python: Current Test File** - Debug all tests in current file
   - **Python: Current Test Function** - Debug selected test
   - **Python: All Tests** - Debug entire suite
   - **Python: Fast Tests Only** - Debug quick tests

### Debug Controls

- **F5** - Continue
- **F10** - Step Over
- **F11** - Step Into
- **Shift+F11** - Step Out
- **Cmd+Shift+F5** - Restart
- **Shift+F5** - Stop

---

## Test Results

### Understanding Results

- ✅ **Green checkmark** - Test passed
- ❌ **Red X** - Test failed
- ⚠️ **Yellow warning** - Test skipped or has issues
- ⏱️ **Clock icon** - Test is running

### Viewing Test Output

1. Click on a test in the Test Explorer
2. Output appears in the "Test Results" panel below
3. Failures show:
   - Error message
   - Stack trace
   - Line numbers (clickable)

### Filtering Tests

In the Test Explorer search box, you can filter:
- By name: `test_config`
- By status: `@failed`, `@passed`
- By file: `test_api`

---

## Test Coverage

### Generate Coverage Report

**Method 1: Using Task**
1. `Cmd+Shift+P` → "Tasks: Run Task" → "Run Tests with Coverage"
2. Open `htmlcov/index.html` in browser

**Method 2: Using Launch Config**
1. Press F5
2. Select "Python: Test With Coverage"
3. Check terminal for coverage summary
4. Open `htmlcov/index.html` for detailed report

### View Coverage in VSCode

Install the "Coverage Gutters" extension:
```bash
code --install-extension ryanluker.vscode-coverage-gutters
```

Then:
1. Run tests with coverage
2. Press `Cmd+Shift+P` → "Coverage Gutters: Display Coverage"
3. Green/red lines show covered/uncovered code

---

## Test Configuration

### Files

- **`.vscode/settings.json`** - VSCode Python test settings
- **`.vscode/launch.json`** - Debug configurations
- **`.vscode/tasks.json`** - Test runner tasks
- **`pytest.ini`** - Pytest configuration
- **`pyproject.toml`** - Python project settings

### Current Settings

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests",
    "--override-ini=addopts=",
    "-v"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

**What this means:**
- ✅ Pytest is enabled
- ✅ Tests in `tests/` directory
- ✅ Coverage options disabled by default (faster)
- ✅ Verbose output
- ✅ Auto-discover on save

---

## Common Workflows

### Workflow 1: TDD (Test-Driven Development)

1. Write a failing test in test file
2. Save file (auto-discovers test)
3. Run test (it fails - red ❌)
4. Write implementation code
5. Run test again (it passes - green ✅)
6. Refactor if needed

### Workflow 2: Fix a Bug

1. Open failing test in Test Explorer
2. Click 🐛 debug icon
3. Set breakpoints in implementation
4. Step through to find issue
5. Fix code
6. Run test again to verify

### Workflow 3: Before Commit

1. Run "Fast Tests" task (2 seconds)
2. If pass, run "All Tests"
3. If pass, run "Tests with Coverage"
4. Check coverage report
5. Commit with confidence

---

## Keyboard Shortcuts (Custom)

Add these to your `keybindings.json` (`Cmd+K Cmd+S`):

```json
[
  {
    "key": "cmd+shift+t",
    "command": "python.runAllTests"
  },
  {
    "key": "cmd+shift+r",
    "command": "python.runCurrentTestFile"
  },
  {
    "key": "cmd+shift+d",
    "command": "python.debugTestAtCursor"
  }
]
```

---

## Troubleshooting

### Tests Not Appearing

**Solution 1: Check Python Interpreter**
1. `Cmd+Shift+P` → "Python: Select Interpreter"
2. Choose `.venv/bin/python`

**Solution 2: Refresh Tests**
1. Click 🔄 in Test Explorer

**Solution 3: Check Output**
1. View → Output
2. Select "Python Test Log" from dropdown
3. Look for errors

### Tests Fail with Import Errors

**Solution:**
```bash
# Install package in development mode
pip install -e .
```

### Tests Fail with "pytest-cov" Error

**Solution:**
Tests are configured to run WITHOUT coverage by default. If you see this error:
```bash
# Install coverage support
pip install pytest-cov
```

Or use the task: "Run All Tests" (without coverage)

### Slow Test Discovery

**Solution:** Exclude large directories in `.vscode/settings.json`:
```json
{
  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/__pycache__/**": true
  }
}
```

---

## Tips & Tricks

### 1. Run Only Failed Tests

After running all tests:
```bash
.venv/bin/pytest --lf  # Last failed
```

### 2. Run Tests in Parallel

```bash
pip install pytest-xdist
.venv/bin/pytest -n auto
```

### 3. Watch Mode (Auto-run on Save)

Install pytest-watch:
```bash
pip install pytest-watch
.venv/bin/ptw
```

### 4. Generate JUnit XML (for CI)

```bash
.venv/bin/pytest --junit-xml=test-results.xml
```

### 5. View Coverage in Terminal

```bash
.venv/bin/pytest --cov=guest_search --cov-report=term-missing
```

---

## Test Organization

### Current Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_integration.py  # API error handling
├── test_config.py           # Configuration tests
├── test_conversation_flow.py # Tool call handling
├── test_date_logic.py       # Date calculations
├── test_file_operations.py  # File I/O safety
├── test_json_parsing.py     # JSON resilience
├── test_search_providers.py # Search fallback
└── test_web_scraping.py     # Web scraping
```

### Adding New Tests

1. Create new test file: `tests/test_myfeature.py`
2. Follow naming convention: `test_*` functions
3. Use existing fixtures from `conftest.py`
4. Tests auto-discover on save

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest -v
```

---

## Quick Reference

| Action | Method |
|--------|--------|
| Run all tests | Click ▶️ in Test Explorer |
| Run one test | Click ▶️ next to test in editor |
| Debug test | Click 🐛 next to test |
| View results | Click test in Test Explorer |
| See coverage | Tasks → "Run Tests with Coverage" |
| Run fast tests | Tasks → "Run Fast Tests" |
| Stop at first failure | Tasks → "Run Tests (Stop on First Failure)" |

---

## Status

✅ **Test Discovery:** Working (148 tests)
✅ **Test Execution:** Working
✅ **Debug Mode:** Configured
✅ **Coverage:** Available (install pytest-cov)
✅ **Tasks:** Configured
✅ **Launch Configs:** Configured

---

**Last Updated:** 2024-10-12

For more information, see:
- [TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)
- [QUICK_TEST_REFERENCE.md](./QUICK_TEST_REFERENCE.md)
