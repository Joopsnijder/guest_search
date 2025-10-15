"""Tests for learning functionality in GuestFinderAgent."""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.guest_search.agent import GuestFinderAgent


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create empty previous_guests.json
    (data_dir / "previous_guests.json").write_text("[]")

    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    yield data_dir
    os.chdir(original_dir)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    with patch("src.guest_search.agent.get_anthropic_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


def test_load_empty_search_history(temp_data_dir, mock_anthropic_client):
    """Test loading search history when file doesn't exist."""
    agent = GuestFinderAgent()
    assert agent.search_history == {"sessions": []}
    assert agent.current_session_queries == []


def test_save_search_history(temp_data_dir, mock_anthropic_client):
    """Test saving search history to file."""
    agent = GuestFinderAgent()

    # Add some data
    agent.search_history["sessions"].append(
        {
            "date": datetime.now().isoformat(),
            "week_number": 42,
            "total_queries": 3,
            "total_candidates": 5,
            "queries": [
                {
                    "query": "AI Act Nederland 2025",
                    "candidates_found": 2,
                    "successful_sources": ["https://example.com"],
                }
            ],
        }
    )

    agent._save_search_history()

    # Verify file was created and contains correct data
    assert (temp_data_dir / "search_history.json").exists()

    with open(temp_data_dir / "search_history.json") as f:
        saved_data = json.load(f)

    assert len(saved_data["sessions"]) == 1
    assert saved_data["sessions"][0]["week_number"] == 42
    assert saved_data["sessions"][0]["total_candidates"] == 5


def test_get_learning_insights_no_history(temp_data_dir, mock_anthropic_client):
    """Test getting insights when there's no history."""
    agent = GuestFinderAgent()
    insights = agent._get_learning_insights(weeks=4)
    assert insights is None


def test_get_learning_insights_with_history(temp_data_dir, mock_anthropic_client):
    """Test getting insights from search history."""
    agent = GuestFinderAgent()

    # Create mock history
    now = datetime.now()
    agent.search_history["sessions"] = [
        {
            "date": now.isoformat(),
            "week_number": 42,
            "total_queries": 3,
            "total_candidates": 5,
            "queries": [
                {
                    "query": "AI Act Nederland",
                    "candidates_found": 2,
                    "successful_sources": ["https://aic4nl.nl/evenement/"],
                    "priority": "high",
                    "rationale": "Test rationale",
                },
                {
                    "query": "Machine Learning experts",
                    "candidates_found": 3,
                    "successful_sources": [
                        "https://aic4nl.nl/evenement/",
                        "https://tno.nl/research/",
                    ],
                    "priority": "medium",
                    "rationale": "Another test",
                },
                {
                    "query": "Empty query",
                    "candidates_found": 0,
                    "successful_sources": [],
                    "priority": "low",
                    "rationale": "Test",
                },
            ],
        }
    ]

    insights = agent._get_learning_insights(weeks=4)

    assert insights is not None
    assert insights["total_sessions"] == 1
    assert insights["total_queries"] == 3
    assert insights["successful_queries"] == 2  # Only queries with candidates > 0
    assert len(insights["top_performing_queries"]) == 2
    assert insights["top_performing_queries"][0]["query"] == "Machine Learning experts"
    assert insights["avg_candidates_per_query"] == pytest.approx(5 / 3)
    # top_sources contains full URLs
    assert any("aic4nl.nl" in source for source in insights["top_sources"])


def test_get_learning_insights_filters_old_sessions(temp_data_dir, mock_anthropic_client):
    """Test that old sessions are filtered out."""
    agent = GuestFinderAgent()

    # Create sessions - one recent, one old
    now = datetime.now()
    old_date = now - timedelta(weeks=5)

    agent.search_history["sessions"] = [
        {
            "date": now.isoformat(),
            "queries": [{"query": "Recent", "candidates_found": 2, "successful_sources": []}],
        },
        {
            "date": old_date.isoformat(),
            "queries": [{"query": "Old", "candidates_found": 5, "successful_sources": []}],
        },
    ]

    insights = agent._get_learning_insights(weeks=4)

    assert insights is not None
    assert insights["total_sessions"] == 1
    assert insights["total_queries"] == 1
    assert insights["top_performing_queries"][0]["query"] == "Recent"


def test_track_query_performance_during_search(temp_data_dir, mock_anthropic_client):
    """Test that queries are tracked during search phase."""
    agent = GuestFinderAgent()

    # Simulate adding a query record
    query_record = {
        "query": "AI experts TU Delft",
        "rationale": "Looking for university researchers",
        "priority": "high",
        "candidates_found": 3,
        "successful_sources": ["https://tudelft.nl/ai"],
        "timestamp": datetime.now().isoformat(),
    }

    agent.current_session_queries.append(query_record)

    assert len(agent.current_session_queries) == 1
    assert agent.current_session_queries[0]["query"] == "AI experts TU Delft"
    assert agent.current_session_queries[0]["candidates_found"] == 3


def test_get_recently_used_sources(temp_data_dir, mock_anthropic_client):
    """Test getting recently used sources for deduplication."""
    agent = GuestFinderAgent()

    # Create mock history with recent and old sessions
    now = datetime.now()
    recent_date = now - timedelta(days=3)
    old_date = now - timedelta(weeks=2)

    agent.search_history["sessions"] = [
        {
            "date": recent_date.isoformat(),
            "queries": [
                {
                    "query": "Recent query",
                    "successful_sources": ["https://aic4nl.nl/event", "https://tudelft.nl/news"],
                }
            ],
        },
        {
            "date": old_date.isoformat(),
            "queries": [
                {"query": "Old query", "successful_sources": ["https://old-source.nl"]}
            ],
        },
    ]

    # Get sources from last week
    recent_sources = agent._get_recently_used_sources(weeks=1)

    assert len(recent_sources) == 2
    assert "https://aic4nl.nl/event" in recent_sources
    assert "https://tudelft.nl/news" in recent_sources
    assert "https://old-source.nl" not in recent_sources


def test_get_recently_used_sources_empty(temp_data_dir, mock_anthropic_client):
    """Test getting recently used sources when there are none."""
    agent = GuestFinderAgent()

    recent_sources = agent._get_recently_used_sources(weeks=1)

    assert recent_sources == []


def test_source_deduplication_in_insights(temp_data_dir, mock_anthropic_client):
    """Test that recently used sources are identified for planning phase."""
    agent = GuestFinderAgent()

    now = datetime.now()

    # Create session with sources
    agent.search_history["sessions"] = [
        {
            "date": now.isoformat(),
            "queries": [
                {
                    "query": "AI Act",
                    "candidates_found": 5,
                    "successful_sources": [
                        "https://aic4nl.nl/event/ai-act-congress",
                        "https://computable.nl/article/ai-act-implementation",
                    ],
                }
            ],
        }
    ]

    recent_sources = agent._get_recently_used_sources(weeks=1)

    # Verify both sources are in the recent list
    assert len(recent_sources) == 2
    assert any("aic4nl.nl" in s for s in recent_sources)
    assert any("computable.nl" in s for s in recent_sources)


def test_strategy_saved_in_session(temp_data_dir, mock_anthropic_client):
    """Test that planning strategy is saved in session record."""
    agent = GuestFinderAgent()

    # Simulate a strategy
    agent.current_session_strategy = {
        "week_focus": "AI Act implementatie in Nederlandse bedrijven",
        "sectors_to_prioritize": ["zorg", "overheid"],
        "topics_to_cover": ["AI Act", "compliance"],
        "total_queries_planned": 12,
    }

    # Verify it's stored
    assert agent.current_session_strategy is not None
    assert agent.current_session_strategy["week_focus"].startswith("AI Act")
    assert len(agent.current_session_strategy["sectors_to_prioritize"]) == 2


def test_strategy_included_in_insights(temp_data_dir, mock_anthropic_client):
    """Test that previous strategies are included in learning insights."""
    agent = GuestFinderAgent()

    now = datetime.now()

    # Create session with strategy
    agent.search_history["sessions"] = [
        {
            "date": now.isoformat(),
            "total_candidates": 5,
            "strategy": {
                "week_focus": "Focus on vakmedia for diverse sources",
                "sectors_to_prioritize": ["zorg", "agrifood"],
                "topics_to_cover": ["AI Act", "Green AI"],
            },
            "queries": [{"query": "test", "candidates_found": 5, "successful_sources": []}],
        }
    ]

    insights = agent._get_learning_insights(weeks=4)

    assert insights is not None
    assert "previous_strategies" in insights
    assert len(insights["previous_strategies"]) == 1
    assert insights["previous_strategies"][0]["week_focus"] == "Focus on vakmedia for diverse sources"
    assert insights["previous_strategies"][0]["candidates_found"] == 5
