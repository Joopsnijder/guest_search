# Guest Search

[![Tests](https://img.shields.io/badge/tests-159%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AI-driven podcast guest finder with intelligent search and automatic rate limit handling.

## Features

🤖 **AI-Powered Search** - Claude Sonnet 4 agent with extended thinking for strategic guest finding
🔄 **Multi-Provider Fallback** - Serper → SearXNG → Brave → Google Scraper
⚡ **Smart Rate Limiting** - Automatic provider skipping on 402/429 errors
💾 **Intelligent Caching** - 1-day result cache to minimize API calls
✅ **Well Tested** - 159 tests covering 9 critical risk areas
📊 **Arc42 Documentation** - Complete architecture documentation with Mermaid diagrams

## Installation

```bash
# Install in development mode
pip install -e ".[dev]"
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Testing

**📊 Test Suite: 159 tests covering 9 critical risk areas**

#### In VSCode (Recommended)
1. Open Test Explorer (🧪 icon in sidebar)
2. Click ▶️ to run tests or 🐛 to debug
3. See [VSCODE_TEST_GUIDE.md](docs/VSCODE_TEST_GUIDE.md) for full guide

#### In Terminal
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest --cov=guest_search --cov-report=html

# Quick health check (fast tests only)
pytest tests/test_config.py tests/test_date_logic.py -v
```

#### Test Documentation
- 📖 [VSCode Testing Guide](docs/VSCODE_TEST_GUIDE.md) - Full VSCode integration guide
- 📊 [Test Coverage Summary](docs/TEST_COVERAGE_SUMMARY.md) - Detailed risk analysis
- ⚡ [Quick Reference](docs/QUICK_TEST_REFERENCE.md) - Common commands
- 📝 [Test Suite README](tests/README.md) - Writing new tests

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .

# Type checking
mypy src/
```

## Features

### Smart Search with Rate Limit Handling
The search tool automatically detects and skips rate-limited providers for the duration of the session:
- 🔄 Multi-provider fallback (Serper → SearXNG → Brave → Google Scraper)
- ⚡ Automatic provider skipping on rate limits (402/429 errors)
- 💾 1-day caching to reduce API calls
- 📊 Session tracking of rate-limited providers
- ✨ Serper primary for best quality snippets

See [RATE_LIMIT_HANDLING.md](docs/RATE_LIMIT_HANDLING.md) for details.

## Project Structure

```
guest_search/
├── src/
│   └── guest_search/      # Main package
│       └── __init__.py
├── tests/                 # Test files
│   ├── __init__.py
│   └── conftest.py
├── docs/                  # Documentation
│   ├── architecture.md    # Arc42 architecture docs
│   └── RATE_LIMIT_HANDLING.md  # Rate limit feature docs
├── scripts/               # Utility scripts
├── pyproject.toml        # Project configuration
├── README.md             # This file
└── .gitignore            # Git ignore rules
```

## License

TBD
