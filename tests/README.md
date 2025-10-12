# Test Suite README

## Quick Start

### In VSCode (Recommended)

1. **Open Test Explorer:**
   - Click 🧪 icon in left sidebar
   - Or `Cmd+Shift+P` → "Test: Focus on Test Explorer View"

2. **Run Tests:**
   - Click ▶️ icons next to tests
   - All 148 tests appear automatically

3. **Debug Tests:**
   - Click 🐛 icons next to tests
   - Set breakpoints and step through

📖 **Full Guide:** [VSCODE_TEST_GUIDE.md](../docs/VSCODE_TEST_GUIDE.md)

### In Terminal

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_config.py

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run specific test
pytest tests/test_config.py::TestConfigurationLoading::test_config_constants
```

---

## Test Files (148 tests)

| File | Tests | Focus Area |
|------|-------|------------|
| `test_api_integration.py` | 10 | Anthropic API errors & timeouts |
| `test_search_providers.py` | 23 | Search fallback & caching |
| `test_file_operations.py` | 18 | File I/O & data persistence |
| `test_json_parsing.py` | 17 | JSON parsing resilience |
| `test_date_logic.py` | 24 | Date calculations & boundaries |
| `test_config.py` | 22 | Configuration & env vars |
| `test_conversation_flow.py` | 14 | Tool call handling |
| `test_web_scraping.py` | 20 | Web scraping resilience |
| `conftest.py` | - | Shared fixtures |

---

## Test Structure

```python
# Example test structure
class TestFeatureName:
    """Test description"""

    def test_specific_behavior(self, fixture1, fixture2):
        """Test a specific behavior."""
        # Arrange
        setup_data = create_test_data()

        # Act
        result = function_to_test(setup_data)

        # Assert
        assert result == expected_value
```

---

## Available Fixtures (from conftest.py)

### File System
- `temp_dir` - Temporary directory
- `mock_data_dir` - Mock data directory with cache
- `previous_guests_file` - Sample previous guests JSON
- `malformed_json_file` - Corrupted JSON

### API Responses
- `mock_anthropic_planning_response` - Valid planning response
- `mock_anthropic_search_response` - Search with tool calls
- `mock_anthropic_report_response` - Report generation
- `mock_anthropic_malformed_json_response` - Invalid JSON

### Search Results
- `mock_search_results` - Standard search results
- `mock_serper_response` - Serper API format
- `mock_searxng_response` - SearXNG format
- `mock_brave_response` - Brave Search format

### Configuration
- `mock_env_vars` - Mock environment variables
- `mock_missing_api_key` - Missing API key scenario

### Time
- `fixed_datetime` - Fixed date for tests
- `date_8_weeks_ago` - Exclusion boundary testing

---

## Writing New Tests

### 1. Create Test File

```bash
# Create new test file
touch tests/test_myfeature.py
```

### 2. Use Template

```python
"""Tests for my feature."""

from unittest.mock import patch
import pytest


class TestMyFeature:
    """Test my feature functionality."""

    def test_basic_functionality(self):
        """Test that basic feature works."""
        result = my_function()
        assert result is not None

    @patch("module.external_call")
    def test_with_mock(self, mock_call):
        """Test with mocked external dependency."""
        mock_call.return_value = "mocked"
        result = my_function()
        assert result == "expected"

    def test_with_fixture(self, temp_dir):
        """Test using fixture from conftest.py."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        assert test_file.exists()
```

### 3. Run Your Test

```bash
# Run new test file
pytest tests/test_myfeature.py -v

# Or in VSCode: Click ▶️ in Test Explorer
```

---

## Test Patterns

### Pattern 1: Mock External API

```python
@patch("src.guest_search.agent.Anthropic")
def test_api_call(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    # Test code here
```

### Pattern 2: Test File Operations

```python
def test_file_operation(temp_dir):
    test_file = temp_dir / "data.json"
    data = {"key": "value"}

    # Write
    test_file.write_text(json.dumps(data))

    # Read and verify
    loaded = json.loads(test_file.read_text())
    assert loaded == data
```

### Pattern 3: Test Date Logic

```python
from freezegun import freeze_time
from datetime import datetime

@freeze_time("2024-10-12 10:00:00")
def test_date_calculation():
    now = datetime.now()
    assert now.day == 12
```

### Pattern 4: Test Error Handling

```python
def test_handles_missing_file():
    with pytest.raises(FileNotFoundError):
        load_nonexistent_file()
```

---

## Common Tasks

### Run Specific Test Type

```bash
# Run only unit tests (if marked)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Debug Failed Test

```bash
# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Show full traceback
pytest --tb=long
```

### Check Coverage

```bash
# Install coverage first
pip install pytest-cov

# Run with coverage
pytest --cov=guest_search --cov-report=html

# Open report
open htmlcov/index.html
```

---

## Test Markers

Add markers to tests:

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """This test takes a while."""
    pass

@pytest.mark.integration
def test_api_integration():
    """This test calls external APIs."""
    pass
```

Run marked tests:

```bash
pytest -m slow          # Run only slow tests
pytest -m "not slow"    # Skip slow tests
pytest -m integration   # Run only integration tests
```

---

## Troubleshooting

### Import Errors

```bash
# Install package in dev mode
pip install -e .
```

### Tests Not Found

```bash
# Check test discovery
pytest --collect-only

# Should show: 148 tests collected
```

### Mock Not Working

```python
# Make sure to patch the right location
# ❌ Wrong: @patch("anthropic.Anthropic")
# ✅ Right: @patch("src.guest_search.agent.Anthropic")
```

### Fixture Not Found

- Check if fixture is in `conftest.py`
- Check function signature: `def test_func(fixture_name):`
- Fixture name must match exactly

---

## Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** that describe what is tested
3. **Arrange-Act-Assert** pattern
4. **Use fixtures** for common setup
5. **Mock external dependencies** (APIs, files, time)
6. **Test edge cases** (empty, null, boundaries)
7. **Keep tests fast** (< 1 second per test)
8. **Independent tests** (no shared state)

---

## Resources

- **Detailed Coverage Report:** [TEST_COVERAGE_SUMMARY.md](../docs/TEST_COVERAGE_SUMMARY.md)
- **VSCode Integration:** [VSCODE_TEST_GUIDE.md](../docs/VSCODE_TEST_GUIDE.md)
- **Quick Reference:** [QUICK_TEST_REFERENCE.md](../docs/QUICK_TEST_REFERENCE.md)
- **pytest Docs:** https://docs.pytest.org/
- **pytest-mock Docs:** https://pytest-mock.readthedocs.io/

---

## Statistics

- **Total Tests:** 148
- **Test Files:** 8
- **Fixtures:** 20+
- **Coverage Target:** 80%+
- **Expected Runtime:** ~10-15 seconds (full suite)

---

**Need Help?**

1. Check documentation in `docs/` folder
2. Look at existing tests for patterns
3. Run `pytest --help` for options
4. Use VSCode Test Explorer for visual interface

---

**Last Updated:** 2024-10-12
