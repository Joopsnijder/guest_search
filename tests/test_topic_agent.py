"""Tests for TopicFinderAgent - topic research functionality."""

from unittest.mock import MagicMock, patch


class TestTopicAgentInitialization:
    """Test initializing the topic finder agent."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_agent_initialization(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that agent initializes with correct attributes."""
        from src.guest_search.topic_agent import TopicFinderAgent

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        agent = TopicFinderAgent()

        assert agent.topics == []
        assert agent.client is not None
        assert agent.smart_search is not None
        assert agent.console is not None


class TestTopicToolDefinitions:
    """Test topic-specific tool definitions."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_get_topic_tools_returns_correct_tools(
        self, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test that topic tools are correctly defined."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        tools = agent._get_topic_tools()

        # Should have 3 tools: web_search, fetch_page_content, save_topic
        assert len(tools) == 3

        tool_names = [tool["name"] for tool in tools]
        assert "web_search" in tool_names
        assert "fetch_page_content" in tool_names
        assert "save_topic" in tool_names

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_save_topic_tool_schema(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that save_topic tool has correct schema."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        tools = agent._get_topic_tools()

        save_topic_tool = next(tool for tool in tools if tool["name"] == "save_topic")

        # Check required fields
        required_fields = save_topic_tool["input_schema"]["required"]
        assert "title" in required_fields
        assert "category" in required_fields
        assert "why_relevant_for_anne" in required_fields
        assert "description" in required_fields
        assert "search_keywords" in required_fields

        # Check category enum
        category_enum = save_topic_tool["input_schema"]["properties"]["category"]["enum"]
        expected_categories = [
            "Wetenschappelijk",
            "Praktijkvoorbeeld",
            "Informatief",
            "Transformatie",
            "Waarschuwend",
            "Kans",
        ]
        assert category_enum == expected_categories


class TestTopicToolHandling:
    """Test handling of topic-specific tool calls."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_handle_web_search(
        self, mock_anthropic, mock_search_tool, mock_env_vars, mock_search_results
    ):
        """Test handling web_search tool call."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        agent.smart_search.search = MagicMock(
            return_value={"results": mock_search_results, "provider": "TestProvider"}
        )

        result = agent._handle_tool_call("web_search", {"query": "AI trends 2025"})

        assert "results" in result
        assert "provider" in result
        assert result["provider"] == "TestProvider"

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    @patch("requests.get")
    def test_handle_fetch_page_content(
        self, mock_get, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test handling fetch_page_content tool call."""
        from src.guest_search.topic_agent import TopicFinderAgent

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>AI News</h1><p>Some content</p></body></html>"
        mock_get.return_value = mock_response

        agent = TopicFinderAgent()
        result = agent._handle_tool_call(
            "fetch_page_content", {"url": "https://example.com/ai-news"}
        )

        assert result["status"] == "success"
        assert "AI News" in result["content"]
        assert "Some content" in result["content"]

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_handle_save_topic(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling save_topic tool call."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()

        topic_data = {
            "title": "AI in Healthcare",
            "category": "Wetenschappelijk",
            "why_relevant_for_anne": "Practical application",
            "description": "AI improves diagnostics",
            "search_keywords": ["AI", "healthcare", "diagnostics"],
            "discussion_angles": ["How does it work?", "What are the risks?"],
            "sources": [{"url": "https://example.com", "title": "AI News", "date": "2025-01-01"}],
        }

        result = agent._handle_tool_call("save_topic", topic_data)

        assert result["status"] == "saved"
        assert result["total_topics"] == 1
        assert len(agent.topics) == 1
        assert agent.topics[0]["title"] == "AI in Healthcare"

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_handle_multiple_save_topics(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test saving multiple topics."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()

        for i in range(3):
            topic_data = {
                "title": f"Topic {i + 1}",
                "category": "Informatief",
                "why_relevant_for_anne": "Relevant",
                "description": "Description",
                "search_keywords": ["keyword"],
                "discussion_angles": ["question"],
                "sources": [{"url": "url", "title": "title", "date": "date"}],
            }
            result = agent._handle_tool_call("save_topic", topic_data)
            assert result["total_topics"] == i + 1

        assert len(agent.topics) == 3


class TestTopicReportGeneration:
    """Test report generation for topics."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_generate_report_with_no_topics(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test generating report when no topics found."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        report = agent.generate_report()

        assert report == "Geen interessante topics deze week."
        assert len(agent.topics) == 0

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    @patch("builtins.open", create=True)
    @patch("os.makedirs")
    def test_generate_report_with_topics(
        self, mock_makedirs, mock_open, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test generating report with topics."""
        from src.guest_search.topic_agent import TopicFinderAgent

        # Mock API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "# Topic Report\n\nSome topics..."
        mock_response.content = [text_block]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        agent = TopicFinderAgent()

        # Add a topic
        agent.topics.append(
            {
                "title": "AI Breakthrough",
                "category": "Wetenschappelijk",
                "why_relevant_for_anne": "Practical",
                "description": "Description",
                "search_keywords": ["AI"],
                "discussion_angles": ["Question"],
                "sources": [{"url": "url", "title": "title", "date": "date"}],
            }
        )

        report = agent.generate_report()

        assert "Topic Report" in report
        assert len(agent.topics) == 1

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_display_report(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test displaying report in terminal."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        agent.console.print = MagicMock()

        report_content = "# Test Report\n\n## Section 1\n\nSome content"
        agent.display_report(report_content)

        # Console.print should be called at least 3 times (separator, markdown, separator)
        assert agent.console.print.call_count >= 3


class TestTopicSearchFlow:
    """Test the complete topic search flow."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_run_full_cycle_integration(
        self, mock_anthropic, mock_search_tool, mock_env_vars, monkeypatch
    ):
        """Test complete cycle from search to report."""
        from src.guest_search.topic_agent import TopicFinderAgent

        # Mock API to return end_turn immediately (no actual search)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Patch makedirs and open to avoid file operations
        monkeypatch.setattr("os.makedirs", MagicMock())
        monkeypatch.setattr("builtins.open", MagicMock())

        agent = TopicFinderAgent()

        # Since no topics will be found (mocked to end immediately),
        # report should return "Geen interessante topics deze week."
        report = agent.run_full_cycle()

        assert report == "Geen interessante topics deze week."


class TestErrorHandling:
    """Test error handling in topic agent."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    @patch("requests.get")
    def test_fetch_page_content_network_error(
        self, mock_get, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test handling network error when fetching page."""
        from src.guest_search.topic_agent import TopicFinderAgent

        mock_get.side_effect = Exception("Network error")

        agent = TopicFinderAgent()
        result = agent._handle_tool_call("fetch_page_content", {"url": "https://example.com/fail"})

        assert result["status"] == "error"
        assert "error" in result
        assert "Network error" in result["error"]

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    @patch("requests.get")
    def test_fetch_page_content_http_error(
        self, mock_get, mock_anthropic, mock_search_tool, mock_env_vars
    ):
        """Test handling HTTP error when fetching page."""
        from src.guest_search.topic_agent import TopicFinderAgent

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        agent = TopicFinderAgent()
        result = agent._handle_tool_call(
            "fetch_page_content", {"url": "https://example.com/notfound"}
        )

        assert result["status"] == "error"
        assert "HTTP 404" in result["error"]

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_handle_unknown_tool(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test handling unknown tool call."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        result = agent._handle_tool_call("unknown_tool", {})

        assert "error" in result
        assert result["error"] == "Unknown tool"


class TestCategoryValidation:
    """Test topic category handling."""

    @patch("src.guest_search.topic_agent.SmartSearchTool")
    @patch("src.guest_search.topic_agent.Anthropic")
    def test_all_categories_accepted(self, mock_anthropic, mock_search_tool, mock_env_vars):
        """Test that all defined categories are accepted."""
        from src.guest_search.topic_agent import TopicFinderAgent

        agent = TopicFinderAgent()
        categories = [
            "Wetenschappelijk",
            "Praktijkvoorbeeld",
            "Informatief",
            "Transformatie",
            "Waarschuwend",
            "Kans",
        ]

        for category in categories:
            topic_data = {
                "title": f"Topic for {category}",
                "category": category,
                "why_relevant_for_anne": "Relevant",
                "description": "Description",
                "search_keywords": ["keyword"],
                "discussion_angles": ["question"],
                "sources": [{"url": "url", "title": "title", "date": "date"}],
            }

            result = agent._handle_tool_call("save_topic", topic_data)
            assert result["status"] == "saved"

        # Should have saved all 6 categories
        assert len(agent.topics) == 6
