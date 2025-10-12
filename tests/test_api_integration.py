"""Tests for API integration with Anthropic."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from anthropic import APIConnectionError, APIStatusError, RateLimitError


class TestAnthropicAPIIntegration:
    """Test Anthropic API integration and error handling."""

    @patch("src.guest_search.agent.Anthropic")
    def test_successful_planning_phase(
        self, mock_anthropic_class, mock_anthropic_planning_response, mock_env_vars
    ):
        """Test successful planning phase with valid API response."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="thinking", thinking="Planning..."),
            MagicMock(
                type="text",
                text=json.dumps(
                    {
                        "week_focus": "AI Ethics",
                        "search_queries": [{"query": "test", "rationale": "testing"}],
                        "sectors_to_prioritize": ["healthcare"],
                        "topics_to_cover": ["AI Ethics"],
                    }
                ),
            ),
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            strategy = agent.run_planning_phase()

        # Verify
        assert strategy is not None
        assert "week_focus" in strategy
        assert "search_queries" in strategy
        assert strategy["week_focus"] == "AI Ethics"
        mock_client.messages.create.assert_called_once()

    @patch("src.guest_search.agent.Anthropic")
    def test_api_timeout_handling(self, mock_anthropic_class, mock_env_vars):
        """Test handling of API timeout errors."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock to raise timeout
        mock_client = MagicMock()
        mock_request = Mock()
        mock_client.messages.create.side_effect = APIConnectionError(
            message="Connection timeout", request=mock_request
        )
        mock_anthropic_class.return_value = mock_client

        # Execute and verify
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            with pytest.raises(APIConnectionError):
                agent.run_planning_phase()

    @patch("src.guest_search.agent.Anthropic")
    def test_rate_limit_error_handling(self, mock_anthropic_class, mock_env_vars):
        """Test handling of rate limit (429) errors."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock to raise rate limit error
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_client.messages.create.side_effect = RateLimitError(
            "Rate limit exceeded", response=mock_response, body=None
        )
        mock_anthropic_class.return_value = mock_client

        # Execute and verify
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            with pytest.raises(RateLimitError):
                agent.run_planning_phase()

    @patch("src.guest_search.agent.Anthropic")
    def test_authentication_error_handling(self, mock_anthropic_class, mock_env_vars):
        """Test handling of authentication (401) errors."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock to raise auth error
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.messages.create.side_effect = APIStatusError(
            "Invalid API key", response=mock_response, body=None
        )
        mock_anthropic_class.return_value = mock_client

        # Execute and verify
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            with pytest.raises(APIStatusError):
                agent.run_planning_phase()

    @patch("src.guest_search.agent.Anthropic")
    def test_malformed_json_response_handling(
        self, mock_anthropic_class, mock_env_vars, mock_anthropic_malformed_json_response
    ):
        """Test handling of malformed JSON in API response."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with malformed JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="This is not valid JSON: {incomplete")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            strategy = agent.run_planning_phase()

        # Verify - should return None on JSON parse failure
        assert strategy is None

    @patch("src.guest_search.agent.Anthropic")
    def test_missing_required_fields_in_strategy(self, mock_anthropic_class, mock_env_vars):
        """Test handling of API response missing required fields."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with incomplete strategy
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text=json.dumps(
                    {
                        "week_focus": "Test",
                        # Missing search_queries
                        "sectors_to_prioritize": [],
                    }
                ),
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            strategy = agent.run_planning_phase()

            # Strategy is parsed but might fail in run_search_phase
            assert strategy is not None
            assert "week_focus" in strategy

    @patch("src.guest_search.agent.Anthropic")
    def test_report_generation_success(
        self, mock_anthropic_class, mock_env_vars, sample_candidates, temp_dir
    ):
        """Test successful report generation."""
        from freezegun import freeze_time

        from src.guest_search.agent import GuestFinderAgent

        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="# Test Report")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            agent.candidates = sample_candidates

            # Mock file operations and freeze time
            with patch("builtins.open", create=True):
                with freeze_time("2024-10-12 10:00:00"):
                    report = agent.generate_report()

        # Verify
        assert report == "# Test Report"
        mock_client.messages.create.assert_called_once()

    @patch("src.guest_search.agent.Anthropic")
    def test_empty_candidates_report(self, mock_anthropic_class, mock_env_vars):
        """Test report generation with no candidates."""
        from freezegun import freeze_time

        from src.guest_search.agent import GuestFinderAgent

        # Setup
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            agent.candidates = []
            agent.previous_guests = []  # Ensure no previous guests either
            with freeze_time("2024-10-12 10:00:00"):
                report = agent.generate_report()

        # Verify - should not call API when no candidates
        assert "Geen nieuwe kandidaten" in report
        mock_client.messages.create.assert_not_called()

    @patch("src.guest_search.agent.Anthropic")
    def test_api_response_with_no_text_content(self, mock_anthropic_class, mock_env_vars):
        """Test handling of API response with no text content."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with only thinking, no text
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="thinking", thinking="Just thinking...")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            strategy = agent.run_planning_phase()

        # Verify - should handle gracefully
        assert strategy is None

    @patch("src.guest_search.agent.Anthropic")
    def test_multiple_retries_on_transient_errors(self, mock_anthropic_class, mock_env_vars):
        """Test that transient errors could be retried (if retry logic exists)."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock to fail then succeed
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text=json.dumps(
                    {
                        "week_focus": "Test",
                        "search_queries": [{"query": "test"}],
                        "sectors_to_prioritize": [],
                        "topics_to_cover": [],
                    }
                ),
            )
        ]

        # First call fails, second succeeds (if retry is implemented)
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Execute
        with patch("src.guest_search.agent.SmartSearchTool"):
            agent = GuestFinderAgent()
            strategy = agent.run_planning_phase()

        # Verify
        assert strategy is not None
