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
🎯 **Interactive Selection** - Beautiful terminal UI to review and select guests
📋 **Trello Integration** - One-click export of guests to Trello boards
✅ **Well Tested** - 159 tests covering 9 critical risk areas
📊 **Arc42 Documentation** - Complete architecture documentation with Mermaid diagrams

## Quick Start

### 1. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

Required:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

Recommended (at least one search provider):
- `SERPER_API_KEY` - Get from https://serper.dev (2,500 free searches/month)
- `BRAVE_API_KEY` - Get from https://brave.com/search/api/

Optional (for Trello integration):
- `TRELLO_API_KEY` and `TRELLO_TOKEN` - See [TRELLO_SETUP.md](TRELLO_SETUP.md)

### 3. Run the Guest Finder

```bash
# Run the complete workflow (recommended)
python main.py
```

This will:
1. **Search Phase**: AI agent finds potential guests using web search
2. **Analysis Phase**: Fetches full page content to identify specific people
3. **Report Generation**: Creates a markdown report in `output/reports/`
4. **Interactive Selection**: Automatically prompts to review and select guests

After the search completes, you'll be asked if you want to review candidates immediately or later.

**Alternative workflows:**

```bash
# View the UI without running the agent (uses existing data)
python demo_ui.py

# Run only the interactive selector (skip the agent search)
python select_guests.py
```

### 4. Interactive Guest Selection

The interactive selector provides a beautiful terminal UI where you can:

✨ **Features:**
- 🎨 Browse all new and recent guests with full details
- 🔗 View all source URLs for easy reference and verification
- 📧 See contact information when available (email, LinkedIn)
- 📋 Export selected guests to Trello with one click
- ✓ Automatic duplicate detection before creating cards
- 📊 See guests from the last 2 weeks (yellow-highlighted)

**Available actions:**
- Type a number (e.g., `1`) to select that guest for Trello export
- Type `all` to export all new guests at once
- Type `quit` or `q` to exit

**Each guest card shows:**
- Name, role, and organization
- Topics of expertise
- Why they're relevant right now
- All source URLs (clickable in most terminals)
- Contact info if available
- Date recommended (for recent guests)

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
# Run all unit tests (skip integration tests)
pytest -m "not integration" -v

# Run all tests including integration (requires Trello credentials)
pytest -v

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest --cov=guest_search --cov-report=html

# Quick health check (fast tests only)
pytest tests/test_config.py tests/test_date_logic.py -v

# Run only integration tests (Trello)
pytest -m integration -v
```

#### Test Documentation
- 📖 [VSCode Testing Guide](docs/VSCODE_TEST_GUIDE.md) - Full VSCode integration guide
- 📊 [Test Coverage Summary](docs/TEST_COVERAGE_SUMMARY.md) - Detailed risk analysis
- ⚡ [Quick Reference](docs/QUICK_TEST_REFERENCE.md) - Common commands
- 📝 [Test Suite README](tests/README.md) - Writing new tests
- 🔗 [Integration Tests](tests/INTEGRATION_TESTS.md) - Trello integration testing

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

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with [Claude Code](https://claude.com/claude-code) by Anthropic.

---

**Repository**: https://github.com/Joopsnijder/guest_search
