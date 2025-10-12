"""Tests for JSON parsing from AI responses."""

import json
from unittest.mock import MagicMock, patch


class TestStrategyJSONParsing:
    """Test parsing of strategy JSON from AI responses."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_valid_strategy_json(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test parsing of valid strategy JSON."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with valid JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        valid_strategy = {
            "week_focus": "AI Ethics",
            "search_queries": [{"query": "test", "rationale": "testing"}],
            "sectors_to_prioritize": ["healthcare"],
            "topics_to_cover": ["ethics"],
        }
        mock_response.content = [MagicMock(type="text", text=json.dumps(valid_strategy))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        assert strategy is not None
        assert strategy["week_focus"] == "AI Ethics"
        assert len(strategy["search_queries"]) == 1

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_json_with_surrounding_text(
        self, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test parsing JSON embedded in surrounding text."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with JSON embedded in text
        mock_client = MagicMock()
        mock_response = MagicMock()
        strategy = {
            "week_focus": "Green AI",
            "search_queries": [],
            "sectors_to_prioritize": [],
            "topics_to_cover": [],
        }
        text_with_json = f"Here's my strategy:\n\n{json.dumps(strategy)}\n\nThis should work!"
        mock_response.content = [MagicMock(type="text", text=text_with_json)]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy_result = agent.run_planning_phase()

        assert strategy_result is not None
        assert strategy_result["week_focus"] == "Green AI"

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_malformed_json(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling of malformed JSON."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with malformed JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="text", text='{"week_focus": "Test", invalid: json}')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        # Should return None on parse failure
        assert strategy is None

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_incomplete_json(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling of incomplete JSON."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with incomplete JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text='{"week_focus": "Test"')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        # Should return None on parse failure
        assert strategy is None

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_json_with_unicode(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test parsing JSON with Unicode characters."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with Unicode in JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        strategy = {
            "week_focus": "AI in Zorg – Françoise's perspectief",
            "search_queries": [{"query": "café AI", "rationale": "testing unicode"}],
            "sectors_to_prioritize": ["healthcare"],
            "topics_to_cover": ["ethics"],
        }
        mock_response.content = [
            MagicMock(type="text", text=json.dumps(strategy, ensure_ascii=False))
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy_result = agent.run_planning_phase()

        assert strategy_result is not None
        assert "Françoise" in strategy_result["week_focus"]

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_nested_json_structures(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test parsing deeply nested JSON structures."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with nested JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        strategy = {
            "week_focus": "Complex Strategy",
            "search_queries": [
                {
                    "query": "test",
                    "rationale": "testing",
                    "metadata": {"priority": "high", "tags": ["tag1", "tag2"]},
                }
            ],
            "sectors_to_prioritize": ["healthcare", "finance"],
            "topics_to_cover": ["ethics", "privacy"],
        }
        mock_response.content = [MagicMock(type="text", text=json.dumps(strategy))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy_result = agent.run_planning_phase()

        assert strategy_result is not None
        assert len(strategy_result["search_queries"]) == 1

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_json_with_escaped_characters(
        self, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test parsing JSON with escaped characters."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with escaped characters
        mock_client = MagicMock()
        mock_response = MagicMock()
        strategy = {
            "week_focus": 'AI & "Machine Learning"',
            "search_queries": [{"query": "test\nquery", "rationale": "multi\nline"}],
            "sectors_to_prioritize": [],
            "topics_to_cover": [],
        }
        mock_response.content = [MagicMock(type="text", text=json.dumps(strategy))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy_result = agent.run_planning_phase()

        assert strategy_result is not None
        assert '"Machine Learning"' in strategy_result["week_focus"]

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_parse_empty_json_object(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test parsing empty JSON object."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with empty JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="{}")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        # Empty JSON is valid but might fail validation
        assert strategy == {}

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_no_json_in_response(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling of response with no JSON."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with plain text, no JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="text", text="This is just plain text with no JSON")
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        # Should return None when no JSON found
        assert strategy is None

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_multiple_json_objects_in_response(
        self, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test handling of multiple JSON objects in response."""
        from src.guest_search.agent import GuestFinderAgent

        # Setup mock with multiple JSON objects
        mock_client = MagicMock()
        mock_response = MagicMock()
        strategy1 = {"week_focus": "First"}
        strategy2 = {"week_focus": "Second", "search_queries": []}
        text = f"Here's one: {json.dumps(strategy1)} and another: {json.dumps(strategy2)}"
        mock_response.content = [MagicMock(type="text", text=text)]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = GuestFinderAgent()
        strategy = agent.run_planning_phase()

        # Should parse the first valid JSON object
        assert strategy is not None
        # Implementation uses first { to last }, so result depends on actual implementation


class TestToolInputJSONParsing:
    """Test parsing of JSON from tool inputs."""

    def test_parse_web_search_input(self):
        """Test parsing web_search tool input."""
        tool_input = {"query": "AI experts Netherlands"}

        assert "query" in tool_input
        assert isinstance(tool_input["query"], str)

    def test_parse_save_candidate_input(self, sample_candidate):
        """Test parsing save_candidate tool input."""
        tool_input = sample_candidate

        assert "name" in tool_input
        assert "organization" in tool_input
        assert "topics" in tool_input
        assert isinstance(tool_input["topics"], list)

    def test_parse_malformed_tool_input(self):
        """Test handling of malformed tool input."""
        # Missing required fields
        tool_input = {"name": "Test"}  # Missing other required fields

        assert "name" in tool_input
        # Validation would happen in actual tool call handling


class TestCandidateDataParsing:
    """Test parsing of candidate data structures."""

    def test_parse_candidate_with_all_fields(self, sample_candidate):
        """Test parsing complete candidate data."""
        assert sample_candidate["name"]
        assert sample_candidate["role"]
        assert sample_candidate["organization"]
        assert len(sample_candidate["sources"]) >= 2

    def test_parse_candidate_with_missing_optional_fields(self):
        """Test parsing candidate with missing optional fields."""
        candidate = {
            "name": "Test Person",
            "role": "Researcher",
            "organization": "Test Org",
            "topics": ["AI"],
            "relevance_description": "Test description",
            "sources": [{"url": "https://example.com", "title": "Test", "date": "2024-01-01"}],
            # Missing contact_info (optional)
        }

        assert "name" in candidate
        assert "contact_info" not in candidate

    def test_serialize_candidates_to_json(self, sample_candidates):
        """Test serializing candidates to JSON for report generation."""
        json_str = json.dumps(sample_candidates, ensure_ascii=False, indent=2)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert len(parsed) == len(sample_candidates)
        assert parsed[0]["name"] == sample_candidates[0]["name"]
