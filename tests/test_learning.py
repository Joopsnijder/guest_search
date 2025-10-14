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
