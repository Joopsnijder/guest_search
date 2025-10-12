# Integration Tests

## Trello Integration Tests

The Trello integration tests verify that the TrelloManager can connect to Trello and perform basic operations.

### Prerequisites

1. **Trello Credentials**: You need valid Trello API credentials in your `.env` file:
   ```bash
   TRELLO_API_KEY=your_api_key
   TRELLO_TOKEN=your_token
   ```

2. **Trello Board**: You need a board named "AIToday Live" with a list named "Spot"

### Running Integration Tests

```bash
# Run only integration tests
pytest -m integration -v

# Skip integration tests (run only unit tests)
pytest -m "not integration" -v

# Run all tests including integration
pytest -v
```

### Test Coverage

The integration tests cover:

- ✅ TrelloManager initialization
- ✅ Credential validation
- ✅ Board and list connection
- ✅ Card existence checking
- ✅ Card creation with minimal data
- ✅ Card creation with full guest data

### Manual Cleanup

⚠️ **Note**: Some tests create actual cards in your Trello board. You'll need to manually delete these test cards after running the tests. The test output will show URLs for cleanup.

Test cards are named:
- "Test Guest (Pytest)"
- "Complete Test Guest (Pytest)"

### Skipped Tests

If Trello credentials are not available, the integration tests will be automatically skipped with a message:
```
SKIPPED [1] tests/test_trello_integration.py: Trello credentials not available
```

This allows CI/CD pipelines to run without Trello credentials.

### CI/CD Considerations

For CI/CD pipelines:

1. **With Trello credentials**: Set `TRELLO_API_KEY` and `TRELLO_TOKEN` as secrets
2. **Without Trello credentials**: Tests will be skipped automatically

Example GitHub Actions:
```yaml
- name: Run tests
  env:
    TRELLO_API_KEY: ${{ secrets.TRELLO_API_KEY }}
    TRELLO_TOKEN: ${{ secrets.TRELLO_TOKEN }}
  run: pytest -v
```
