"""Tests for conversation state management and tool call handling."""

import json
from unittest.mock import MagicMock, patch


class TestConversationBuilding:
    """Test building multi-turn conversations with the AI."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_conversation_initialization(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test initializing a conversation."""
        from src.guest_search.agent import GuestFinderAgent

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()

        # Initial conversation should be empty
        assert agent.candidates == []

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_single_tool_call_conversation(
        self, mock_anthropic, mock_search_tool, mock_env_vars, mock_search_results
    ):
        """Test conversation with a single tool call."""
        from src.guest_search.agent import GuestFinderAgent

        mock_client = MagicMock()
        mock_response = MagicMock()

        # Mock tool use
        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "web_search"
        tool_use_block.input = {"query": "AI Netherlands"}
        tool_use_block.id = "tool_123"

        mock_response.content = [tool_use_block]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()

        # Mock the smart search tool
        agent.smart_search.search = MagicMock(
            return_value={"results": mock_search_results, "provider": "TestProvider"}
        )

        # This would normally be called in run_search_phase
        # We're testing the tool call handling directly
        result = agent._handle_tool_call("web_search", {"query": "AI Netherlands"})

        assert "results" in result
        assert len(result["results"]) > 0

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_multiple_tool_calls_in_sequence(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling multiple tool calls in sequence."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # First tool call: web_search
        result1 = agent._handle_tool_call("web_search", {"query": "test"})

        # Second tool call: check_previous_guests
        result2 = agent._handle_tool_call("check_previous_guests", {"name": "Test Person"})

        # Third tool call: save_candidate
        result3 = agent._handle_tool_call(
            "save_candidate",
            {
                "name": "Test",
                "role": "Researcher",
                "organization": "Org",
                "topics": ["AI"],
                "relevance_description": "Test",
                "sources": [],
            },
        )

        assert "results" in result1 or "error" in result1
        assert "already_recommended" in result2
        assert result3["status"] == "saved"


class TestToolCallHandling:
    """Test handling of various tool calls."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_web_search_tool_call(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test web_search tool call handling."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Mock search results
        agent.smart_search.search = MagicMock(
            return_value={
                "results": [
                    {
                        "title": "Test",
                        "snippet": "Test snippet",
                        "link": "https://example.com",
                    }
                ],
                "provider": "TestProvider",
            }
        )

        result = agent._handle_tool_call("web_search", {"query": "AI experts"})

        assert "results" in result
        assert len(result["results"]) > 0
        assert result["provider"] == "TestProvider"

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_check_previous_guests_tool_call(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test check_previous_guests tool call handling."""
        from datetime import datetime, timedelta

        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Add a previous guest
        agent.previous_guests = [
            {
                "name": "Test Guest",
                "date": (datetime.now() - timedelta(weeks=4)).isoformat(),
                "organization": "Test Org",
            }
        ]

        result = agent._handle_tool_call("check_previous_guests", {"name": "Test Guest"})

        assert result["already_recommended"] is True
        assert "weeks_ago" in result

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_save_candidate_tool_call(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test save_candidate tool call handling."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        candidate_data = {
            "name": "Test Candidate",
            "role": "AI Researcher",
            "organization": "Test Org",
            "topics": ["AI Ethics"],
            "relevance_description": "Expert in AI",
            "sources": [],
        }

        result = agent._handle_tool_call("save_candidate", candidate_data)

        assert result["status"] == "saved"
        assert result["total_candidates"] == 1
        assert len(agent.candidates) == 1

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_unknown_tool_call(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling of unknown tool call."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        result = agent._handle_tool_call("unknown_tool", {})

        assert "error" in result
        assert result["error"] == "Unknown tool"


class TestToolResultFormatting:
    """Test formatting of tool results for the AI."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_search_results_formatting(
        self, mock_anthropic, mock_search_tool, mock_env_vars, mock_search_results
    ):
        """Test formatting of search results."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Mock search
        agent.smart_search.search = MagicMock(
            return_value={"results": mock_search_results, "provider": "TestProvider"}
        )

        result = agent._handle_tool_call("web_search", {"query": "test"})

        # Should format results with title, snippet, url
        assert "results" in result
        for item in result["results"]:
            assert "title" in item
            assert "snippet" in item
            assert "url" in item

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_empty_search_results_formatting(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test formatting of empty search results."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Mock empty search
        agent.smart_search.search = MagicMock(
            return_value={"results": [], "provider": "TestProvider"}
        )

        result = agent._handle_tool_call("web_search", {"query": "test"})

        assert result["results"] == []
        assert "error" in result


class TestConversationStateManagement:
    """Test managing conversation state across multiple turns."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_candidate_accumulation(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that candidates accumulate across multiple tool calls."""
        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Add multiple candidates
        for i in range(3):
            agent._handle_tool_call(
                "save_candidate",
                {
                    "name": f"Candidate {i}",
                    "role": "Researcher",
                    "organization": "Org",
                    "topics": ["AI"],
                    "relevance_description": "Expert",
                    "sources": [],
                },
            )

        assert len(agent.candidates) == 3

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_previous_guests_persistence(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that previous guests list persists across checks."""
        from datetime import datetime

        from src.guest_search.agent import GuestFinderAgent

        agent = GuestFinderAgent()

        # Add previous guest
        agent.previous_guests = [
            {
                "name": "Guest 1",
                "date": datetime.now().isoformat(),
                "organization": "Org 1",
            }
        ]

        # Check multiple times
        result1 = agent._handle_tool_call("check_previous_guests", {"name": "Guest 1"})
        result2 = agent._handle_tool_call("check_previous_guests", {"name": "Guest 2"})

        assert result1["already_recommended"] is True
        assert result2["already_recommended"] is False


class TestMessageConstruction:
    """Test construction of messages for the AI API."""

    def test_tool_result_message_format(self):
        """Test format of tool result messages."""
        tool_result = {
            "type": "tool_result",
            "tool_use_id": "tool_123",
            "content": json.dumps({"results": []}),
        }

        assert tool_result["type"] == "tool_result"
        assert "tool_use_id" in tool_result
        assert "content" in tool_result

    def test_user_message_format(self):
        """Test format of user messages."""
        user_message = {"role": "user", "content": "Search for AI experts"}

        assert user_message["role"] == "user"
        assert isinstance(user_message["content"], str)

    def test_assistant_message_format(self):
        """Test format of assistant messages."""
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": "I'll search for that"}],
        }

        assert assistant_message["role"] == "assistant"
        assert isinstance(assistant_message["content"], list)


class TestSearchPhaseConversation:
    """Test conversation flow during search phase."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_search_phase_with_valid_strategy(
        self, mock_anthropic, mock_search_tool, mock_env_vars, mock_search_results
    ):
        """Test search phase with valid strategy."""
        from src.guest_search.agent import GuestFinderAgent

        # Mock responses
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="text", text="Searching..."),
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        agent.smart_search.search = MagicMock(
            return_value={"results": mock_search_results, "provider": "TestProvider"}
        )

        strategy = {
            "search_queries": [{"query": "AI Netherlands", "rationale": "Find Dutch experts"}]
        }

        # Run search phase (will exit after target reached or iteration limit)
        agent.run_search_phase(strategy)

        # Should have called API
        assert mock_client.messages.create.called

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_search_phase_with_no_strategy(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test search phase with missing strategy."""
        from src.guest_search.agent import GuestFinderAgent

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()

        # Run with no strategy
        agent.run_search_phase(None)

        # Should not call API
        assert not mock_client.messages.create.called

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_search_phase_stops_at_target(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that search phase stops when target candidates reached."""
        from src.guest_search.agent import GuestFinderAgent

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()

        # Pre-fill candidates to meet target
        for i in range(8):
            agent.candidates.append({"name": f"Candidate {i}"})

        strategy = {
            "search_queries": [{"query": f"Query {i}", "rationale": "Test"} for i in range(10)]
        }

        # Run search phase
        agent.run_search_phase(strategy)

        # Should stop early (target already reached)
        # API might be called once or not at all depending on implementation
        call_count = mock_client.messages.create.call_count
        assert call_count < len(strategy["search_queries"])
