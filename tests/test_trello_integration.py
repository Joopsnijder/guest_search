"""
Tests for Trello integration.

These are integration tests that require actual Trello credentials.
They will be skipped if credentials are not available.
"""

import os

import pytest
from dotenv import load_dotenv

from src.guest_search.trello_manager import TrelloManager

# Load environment
load_dotenv()


@pytest.fixture
def trello_credentials():
    """Fixture to check if Trello credentials are available."""
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")

    if not api_key or not token:
        pytest.skip("Trello credentials not available")

    return {"api_key": api_key, "token": token}


@pytest.fixture
def trello_manager(trello_credentials):
    """Fixture to create a TrelloManager instance."""
    return TrelloManager(api_key=trello_credentials["api_key"], token=trello_credentials["token"])


class TestTrelloConnection:
    """Test Trello connection and basic operations."""

    def test_trello_manager_initialization(self, trello_credentials):
        """Test that TrelloManager can be initialized with credentials."""
        manager = TrelloManager(
            api_key=trello_credentials["api_key"],
            token=trello_credentials["token"],
        )
        assert manager.api_key == trello_credentials["api_key"]
        assert manager.token == trello_credentials["token"]

    def test_trello_manager_requires_credentials(self):
        """Test that TrelloManager raises error without credentials."""
        # Temporarily remove env vars
        old_key = os.environ.pop("TRELLO_API_KEY", None)
        old_token = os.environ.pop("TRELLO_TOKEN", None)

        try:
            with pytest.raises(ValueError, match="TRELLO_API_KEY and TRELLO_TOKEN"):
                TrelloManager()
        finally:
            # Restore env vars
            if old_key:
                os.environ["TRELLO_API_KEY"] = old_key
            if old_token:
                os.environ["TRELLO_TOKEN"] = old_token

    def test_connect_to_board(self, trello_manager):
        """Test connecting to AIToday Live board."""
        result = trello_manager.connect(board_name="AIToday Live", list_name="Spot")
        assert result is True
        assert trello_manager.board_id is not None
        assert trello_manager.list_id is not None

    def test_connect_invalid_board(self, trello_manager):
        """Test that connecting to non-existent board raises error."""
        with pytest.raises(ValueError, match="Board .* not found"):
            trello_manager.connect(board_name="NonExistentBoard123", list_name="Spot")


class TestTrelloCardOperations:
    """Test card creation and management."""

    @pytest.fixture
    def connected_manager(self, trello_manager):
        """Fixture for a connected TrelloManager."""
        trello_manager.connect(board_name="AIToday Live", list_name="Spot")
        return trello_manager

    @pytest.fixture
    def cleanup_test_cards(self, connected_manager):
        """Fixture to cleanup test cards after tests."""
        test_card_names = [
            "Test Guest (Pytest)",
            "Complete Test Guest (Pytest)",
        ]

        # Cleanup before test (in case of previous test failures)
        for card_name in test_card_names:
            card = connected_manager.get_card_by_name(card_name)
            if card:
                connected_manager.delete_card(card["id"])

        yield connected_manager

        # Cleanup after test
        for card_name in test_card_names:
            card = connected_manager.get_card_by_name(card_name)
            if card:
                connected_manager.delete_card(card["id"])

    def test_card_exists_check(self, connected_manager):
        """Test checking if a card exists."""
        # This should work even if no cards exist
        exists = connected_manager.card_exists("NonExistentGuest123")
        assert isinstance(exists, bool)

    def test_create_guest_card_minimal(self, cleanup_test_cards):
        """Test creating a card with minimal guest data."""
        guest = {
            "name": "Test Guest (Pytest)",
            "organization": "Test Org",
            "role": "Test Role",
        }

        # Create card
        card_info = cleanup_test_cards.create_guest_card(guest)

        assert "id" in card_info
        assert "url" in card_info
        assert card_info["name"] == "Test Guest (Pytest)"

    def test_create_guest_card_full(self, cleanup_test_cards):
        """Test creating a card with full guest data."""
        guest = {
            "name": "Complete Test Guest (Pytest)",
            "organization": "Test Organization",
            "role": "Senior Test Engineer",
            "topics": ["Testing", "Quality Assurance", "Automation"],
            "relevance_description": "Expert in testing methodologies and tools.",
            "sources": [
                {
                    "url": "https://example.com/article",
                    "title": "Test Article",
                    "date": "2025-10-12",
                }
            ],
            "contact_info": {
                "email": "test@example.com",
                "linkedin": "https://linkedin.com/in/test",
            },
            "date": "2025-10-12T12:00:00",
        }

        # Create card
        card_info = cleanup_test_cards.create_guest_card(guest)

        assert "id" in card_info
        assert "url" in card_info
        assert card_info["name"] == "Complete Test Guest (Pytest)"


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
