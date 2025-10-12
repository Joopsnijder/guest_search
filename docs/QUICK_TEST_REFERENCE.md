# Quick Test Reference Guide

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run without coverage options (when pytest-cov not installed)
pytest --override-ini="addopts="

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_config.py

# Run specific test class
pytest tests/test_config.py::TestConfigurationLoading

# Run specific test function
pytest tests/test_config.py::TestConfigurationLoading::test_config_constants

# Stop at first failure
pytest -x

# Show local variables on failure
pytest -l

# Run tests matching a pattern
pytest -k "search" -v
```

### Installation

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or install just test dependencies
pip install pytest pytest-mock freezegun
```

## Test Files Overview

| File | Focus Area | Test Count | Run Command |
|------|------------|------------|-------------|
| `test_config.py` | Configuration & environment | 22 | `pytest tests/test_config.py -v` |
| `test_api_integration.py` | Anthropic API errors | 10 | `pytest tests/test_api_integration.py -v` |
| `test_search_providers.py` | Search fallback logic | 23 | `pytest tests/test_search_providers.py -v` |
| `test_file_operations.py` | File I/O & persistence | 18 | `pytest tests/test_file_operations.py -v` |
| `test_json_parsing.py` | JSON from AI responses | 17 | `pytest tests/test_json_parsing.py -v` |
| `test_date_logic.py` | Date calculations | 24 | `pytest tests/test_date_logic.py -v` |
| `test_conversation_flow.py` | Tool call handling | 14 | `pytest tests/test_conversation_flow.py -v` |
| `test_web_scraping.py` | Google scraper | 20 | `pytest tests/test_web_scraping.py -v` |

## Quick Verification

### Test that all tests can be collected
```bash
pytest --collect-only
# Should show: collected 148 items
```

### Run fast unit tests only
```bash
# Run config tests (fast, ~2 seconds)
pytest tests/test_config.py -v

# Run date logic tests (fast with freezegun)
pytest tests/test_date_logic.py -v --override-ini="addopts="
```

### Check test coverage
```bash
# Requires: pip install pytest-cov
pytest --cov=guest_search --cov-report=term-missing
```

## Common Issues & Solutions

### Issue: `unrecognized arguments: --cov`
**Solution:** Either install pytest-cov or use:
```bash
pytest --override-ini="addopts="
```

### Issue: Tests fail with "No module named 'src'"
**Solution:** Install the package in editable mode:
```bash
pip install -e .
```

### Issue: `freezegun` not working with `datetime.now()`
**Solution:** Some tests may need adjustments. The issue is documented.

### Issue: Tests fail due to missing API key in .env
**Solution:** This is expected for certain tests. The tests document expected behavior.

## Test Patterns

### Testing with Mocks
```python
from unittest.mock import patch, MagicMock

@patch("src.guest_search.agent.Anthropic")
def test_something(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    # ... test code
```

### Testing with Fixtures
```python
def test_with_fixture(mock_data_dir, sample_candidate):
    # mock_data_dir and sample_candidate available from conftest.py
    assert mock_data_dir.exists()
    assert sample_candidate["name"]
```

### Testing with Freezegun
```python
from freezegun import freeze_time

@freeze_time("2024-10-12 10:00:00")
def test_date_logic():
    # Time is frozen at 2024-10-12
    assert datetime.now().day == 12
```

## CI/CD Integration

### GitHub Actions Example
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

## Pre-Commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/test_config.py tests/test_date_logic.py --override-ini="addopts=" -x
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Quick Health Check

Run this command to verify test suite health:
```bash
pytest --collect-only -q | tail -1
```

Expected output:
```
148 tests collected in X.XXs
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [freezegun documentation](https://github.com/spulec/freezegun)

---

**Last Updated:** 2024-10-12
