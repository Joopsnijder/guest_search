"""Pytest configuration and fixtures."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ============================================
# FILE SYSTEM FIXTURES
# ============================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_data_dir(temp_dir):
    """Create a mock data directory with necessary subdirectories."""
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "cache").mkdir()
    return data_dir


@pytest.fixture
def mock_output_dir(temp_dir):
    """Create a mock output directory."""
    output_dir = temp_dir / "output" / "reports"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def previous_guests_file(mock_data_dir):
    """Create a previous_guests.json file."""
    file_path = mock_data_dir / "previous_guests.json"
    # Use fixed date (2024-10-12) to work with freeze_time in tests
    reference_date = datetime(2024, 10, 12, 10, 0, 0)
    guests = [
        {
            "name": "Jan Jansen",
            "date": (reference_date - timedelta(weeks=4)).isoformat(),
            "organization": "TU Delft",
        },
        {
            "name": "Marie van der Berg",
            "date": (reference_date - timedelta(weeks=10)).isoformat(),
            "organization": "TNO",
        },
    ]
    file_path.write_text(json.dumps(guests, indent=2))
    return file_path


@pytest.fixture
def malformed_json_file(mock_data_dir):
    """Create a malformed JSON file."""
    file_path = mock_data_dir / "malformed.json"
    file_path.write_text('{"name": "Test", "date": ')  # Incomplete JSON
    return file_path


@pytest.fixture
def empty_previous_guests_file(mock_data_dir):
    """Create an empty previous_guests.json file."""
    file_path = mock_data_dir / "previous_guests.json"
    file_path.write_text("[]")
    return file_path


# ============================================
# API RESPONSE FIXTURES
# ============================================


@pytest.fixture
def mock_anthropic_planning_response():
    """Mock Anthropic API response for planning phase."""
    return {
        "content": [
            {"type": "thinking", "thinking": "Let me analyze the current AI landscape..."},
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "week_focus": "Focus on AI Ethics and Green AI",
                        "search_queries": [
                            {
                                "query": "AI Act implementatie Nederland 2024",
                                "rationale": "Recent topic",
                                "expected_sources": ["AG Connect", "Computable"],
                                "priority": "high",
                            },
                            {
                                "query": "Nederlandse AI experts TU Delft",
                                "rationale": "Academic experts",
                                "expected_sources": ["University press releases"],
                                "priority": "medium",
                            },
                        ],
                        "sectors_to_prioritize": ["healthcare", "government"],
                        "topics_to_cover": ["AI Ethics", "Green AI"],
                    }
                ),
            },
        ],
        "stop_reason": "end_turn",
    }


@pytest.fixture
def mock_anthropic_search_response():
    """Mock Anthropic API response for search phase."""
    return {
        "content": [
            {
                "type": "text",
                "text": "I'll search for AI experts in the Netherlands.",
            },
            {
                "type": "tool_use",
                "id": "tool_123",
                "name": "web_search",
                "input": {"query": "AI experts Netherlands 2024"},
            },
        ],
        "stop_reason": "tool_use",
    }


@pytest.fixture
def mock_anthropic_report_response():
    """Mock Anthropic API response for report generation."""
    return {
        "content": [
            {
                "type": "text",
                "text": "# Potentiële gasten voor AIToday Live - Week 42\n\n"
                "Deze week focus op AI Ethics.\n\n"
                "## Jan Jansen - AI Researcher bij TU Delft\n\n"
                "**Mogelijke onderwerpen:**\n"
                "- AI Ethics\n"
                "- Explainable AI\n",
            }
        ],
        "stop_reason": "end_turn",
    }


@pytest.fixture
def mock_anthropic_malformed_json_response():
    """Mock Anthropic API response with malformed JSON."""
    return {
        "content": [
            {
                "type": "text",
                "text": "Here's my strategy: {week_focus: 'Test', incomplete json",
            }
        ],
        "stop_reason": "end_turn",
    }


@pytest.fixture
def mock_anthropic_client(mocker):
    """Mock Anthropic client."""
    mock_client = MagicMock()
    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    return mock_client


# ============================================
# SEARCH PROVIDER FIXTURES
# ============================================


@pytest.fixture
def mock_search_results():
    """Mock search results from any provider."""
    return [
        {
            "title": "AI Expert Jan Jansen joins TU Delft",
            "snippet": "Leading AI researcher Jan Jansen has been appointed...",
            "link": "https://tudelft.nl/news/jan-jansen",
            "source": "serper",
        },
        {
            "title": "Marie van der Berg speaks at AI Conference",
            "snippet": "TNO researcher Marie van der Berg presented...",
            "link": "https://tno.nl/news/marie",
            "source": "serper",
        },
    ]


@pytest.fixture
def mock_empty_search_results():
    """Mock empty search results."""
    return []


@pytest.fixture
def mock_serper_response():
    """Mock Serper API response."""
    return {
        "organic": [
            {
                "title": "AI Expert joins TU Delft",
                "snippet": "Leading researcher appointed",
                "link": "https://tudelft.nl/news",
            }
        ]
    }


@pytest.fixture
def mock_searxng_response():
    """Mock SearXNG API response."""
    return {
        "results": [
            {
                "title": "Dutch AI Research",
                "content": "Latest developments in AI",
                "url": "https://example.com",
            }
        ]
    }


@pytest.fixture
def mock_brave_response():
    """Mock Brave Search API response."""
    return {
        "web": {
            "results": [
                {
                    "title": "AI in Netherlands",
                    "description": "Overview of Dutch AI",
                    "url": "https://example.com",
                }
            ]
        }
    }


# ============================================
# CANDIDATE FIXTURES
# ============================================


@pytest.fixture
def sample_candidate():
    """Sample candidate data."""
    return {
        "name": "Jan Jansen",
        "role": "AI Researcher",
        "organization": "TU Delft",
        "topics": ["AI Ethics", "Explainable AI"],
        "relevance_description": "Leading researcher in AI ethics with 10+ years experience",
        "sources": [
            {
                "url": "https://tudelft.nl/jan",
                "title": "Profile at TU Delft",
                "date": "2024-01-15",
            },
            {
                "url": "https://linkedin.com/jan",
                "title": "LinkedIn Profile",
                "date": "2024-01-10",
            },
        ],
        "contact_info": {"email": "j.jansen@tudelft.nl", "linkedin": "linkedin.com/jan"},
    }


@pytest.fixture
def sample_candidates():
    """Multiple sample candidates."""
    return [
        {
            "name": "Jan Jansen",
            "role": "AI Researcher",
            "organization": "TU Delft",
            "topics": ["AI Ethics"],
            "relevance_description": "Expert in AI ethics",
            "sources": [
                {"url": "https://tudelft.nl/jan", "title": "Profile", "date": "2024-01-15"}
            ],
        },
        {
            "name": "Marie van der Berg",
            "role": "Data Scientist",
            "organization": "TNO",
            "topics": ["Green AI"],
            "relevance_description": "Specialist in sustainable AI",
            "sources": [{"url": "https://tno.nl/marie", "title": "Profile", "date": "2024-01-20"}],
        },
    ]


# ============================================
# CONFIGURATION FIXTURES
# ============================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-123")
    monkeypatch.setenv("SERPER_API_KEY", "test-serper-key")
    monkeypatch.setenv("BRAVE_API_KEY", "test-brave-key")


@pytest.fixture
def mock_missing_api_key(monkeypatch):
    """Mock missing API key."""
    # Set to empty string to simulate missing key
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")


# ============================================
# TIME FIXTURES
# ============================================


@pytest.fixture
def fixed_datetime():
    """Fixed datetime for testing."""
    return datetime(2024, 10, 12, 10, 30, 0)


@pytest.fixture
def date_8_weeks_ago():
    """Date exactly 8 weeks ago."""
    return datetime.now() - timedelta(weeks=8)


@pytest.fixture
def date_7_weeks_ago():
    """Date exactly 7 weeks ago (within exclusion window)."""
    return datetime.now() - timedelta(weeks=7)


@pytest.fixture
def date_9_weeks_ago():
    """Date exactly 9 weeks ago (outside exclusion window)."""
    return datetime.now() - timedelta(weeks=9)
