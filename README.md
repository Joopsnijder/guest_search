# Guest Search

[![Tests](https://img.shields.io/badge/tests-192%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AI-driven podcast guest finder and topic researcher with intelligent search and automatic rate limit handling.

## Features

🤖 **AI-Powered Search** - Claude Sonnet 4 agent with extended thinking for strategic guest finding
🎓 **Learning System** - Agent learns from previous searches to improve strategy over time
🔍 **Topic Research** - Separate tool to find interesting AI topics for your podcast
🔄 **Multi-Provider Fallback** - Serper → SearXNG → Brave → Google Scraper
⚡ **Smart Rate Limiting** - Automatic provider skipping on 402/429 errors
💾 **Intelligent Caching** - 1-day result cache to minimize API calls
🎯 **Interactive Selection** - Beautiful terminal UI to review and select guests
📋 **Trello Integration** - One-click export of guests to Trello boards
📝 **Rich Markdown Reports** - Beautiful terminal-rendered reports with syntax highlighting
✅ **Well Tested** - 192 tests covering 11 critical areas (guest finder + topic researcher + learning)
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

### 3. Run the Tools

#### Guest Finder

```bash
# Run the complete workflow (recommended)
python guest_search.py
```

This will:
1. **Planning Phase**: AI analyzes current trends and creates search strategy
2. **Search Phase**: AI agent finds potential guests using web search
3. **Analysis Phase**: Fetches full page content to identify specific people
4. **Report Generation**: Creates a markdown report in `output/reports/`
5. **Report Preview** (optional): View formatted report in terminal with Rich markdown
6. **Interactive Selection**: Prompts to review and select guests for Trello

**Alternative workflows:**

```bash
# View the UI without running the agent (uses existing data)
python demo_ui.py

# Run only the interactive selector (skip the agent search)
python select_guests.py
```

#### Topic Researcher

```bash
# Find interesting AI topics for your podcast
python topic_search.py
```

This will:
1. **Check for existing reports**: If a report exists for today, shows it (no duplicate searches)
2. **Topic Search Phase**: AI finds 6-8 interesting AI topics from the last 14 days
3. **Report Generation**: Creates markdown + JSON in `output/topic_reports/`
4. **Report Preview**: Beautiful Rich markdown rendering in terminal with emojis per category

**Features:**
- 📅 Automatic duplicate detection (won't search twice on same day)
- 🎯 Targeted for "Anne de Vries" persona (IT product owner, early adopter)
- 🏷️ 6 categories: Wetenschappelijk, Praktijkvoorbeeld, Informatief, Transformatie, Waarschuwend, Kans
- 📊 Each topic includes: ideal guest profile, search keywords, discussion angles
- 💾 Saves both markdown report and JSON data for easy processing

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

### 5. Markdown Report Viewing

Both tools generate beautiful markdown reports that can be viewed directly in the terminal:

**Features:**
- 📝 Rich markdown rendering with proper formatting
- 🎨 Syntax highlighting for code blocks
- 📋 Beautiful headers with borders
- 📊 Clean bullet lists and numbered lists
- 🔗 Visible URLs for easy reference
- ➖ Horizontal rules as section dividers

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    Potentiële gasten voor AIToday Live - Week 41   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Dr. Sarah Veldman - Senior AI Policy Advisor bij TNO

Mogelijke onderwerpen:
 • AI Act implementatie in Nederlandse bedrijven
 • Praktische uitdagingen bij compliance
```

The markdown rendering uses the [Rich](https://github.com/Textualize/rich) library for beautiful terminal output.

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

**📊 Test Suite: 181 tests covering 10 critical areas**

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

### Learning System
The agent automatically learns from previous search sessions to improve its strategy:
- 📈 Tracks query performance (which searches find the most candidates)
- 🎯 Identifies most productive sources and websites
- 🧠 Uses historical data to make better search strategies
- 📊 Analyzes last 4 weeks of search history
- 🔄 Improves over time without manual intervention

The agent shows learning insights during the planning phase, helping it focus on proven successful approaches.

See [LEARNING_SYSTEM.md](docs/LEARNING_SYSTEM.md) for detailed documentation.

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
├── guest_search.py                # Guest finder entry point
├── topic_search.py                # Topic researcher entry point
├── select_guests.py               # Interactive guest selector
├── demo_ui.py                     # UI demo (no Trello)
├── src/
│   └── guest_search/              # Main package
│       ├── agent.py               # Guest finder agent
│       ├── topic_agent.py         # Topic finder agent
│       ├── prompts.py             # All AI prompts
│       ├── smart_search_tool.py   # Multi-provider search
│       ├── trello_manager.py      # Trello integration
│       ├── interactive_selector.py # Terminal UI
│       └── tools.py               # Tool definitions
├── tests/                         # Test files (159 tests)
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── docs/                          # Documentation
│   ├── architecture.md            # Arc42 architecture
│   ├── RATE_LIMIT_HANDLING.md     # Rate limit docs
│   ├── VSCODE_TEST_GUIDE.md       # Testing guide
│   └── *.md                       # More documentation
├── output/
│   ├── reports/                   # Guest reports
│   └── topic_reports/             # Topic reports (MD + JSON)
├── data/
│   ├── previous_guests.json       # Deduplication database
│   └── candidates_latest.json     # Latest search results
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with [Claude Code](https://claude.com/claude-code) by Anthropic.

---

**Repository**: https://github.com/Joopsnijder/guest_search
