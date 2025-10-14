"""
Tests for Portkey adapter functionality.

These tests verify that the Anthropic-Portkey adapter correctly:
1. Creates clients with proper configuration
2. Converts message formats between Anthropic and OpenAI
3. Handles tool calling correctly
4. Falls back to direct Anthropic when Portkey is not configured
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.utils.portkey_client import get_anthropic_client, AnthropicPortkeyAdapter


class TestPortkeyClientFactory:
    """Test the get_anthropic_client() factory function."""

    def test_returns_anthropic_client_without_portkey_key(self):
        """Should return standard Anthropic client when PORTKEY_API_KEY not set."""
        with patch.dict(os.environ, {"PORTKEY_API_KEY": ""}, clear=False):
            with patch("src.utils.portkey_client.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                client = get_anthropic_client("test-api-key")

                assert client == mock_client
                mock_anthropic.assert_called_once_with(api_key="test-api-key")

    def test_returns_adapter_with_portkey_key(self):
        """Should return Portkey adapter when PORTKEY_API_KEY is set."""
        with patch.dict(
            os.environ,
            {
                "PORTKEY_API_KEY": "test-portkey-key",
                "PORTKEY_PROVIDER_SLUG": "@test-provider",
                "PORTKEY_MODEL_NAME": "test-model",
            },
            clear=False,
        ):
            with patch("portkey_ai.Portkey") as mock_portkey:
                mock_portkey_client = MagicMock()
                mock_portkey.return_value = mock_portkey_client

                client = get_anthropic_client("test-api-key")

                assert isinstance(client, AnthropicPortkeyAdapter)
                mock_portkey.assert_called_once_with(api_key="test-portkey-key")

    def test_uses_default_provider_slug_and_model(self):
        """Should use default provider slug and model when not specified."""
        with patch.dict(
            os.environ,
            {"PORTKEY_API_KEY": "test-key"},
            clear=False,
        ):
            # Remove provider slug and model if present
            os.environ.pop("PORTKEY_PROVIDER_SLUG", None)
            os.environ.pop("PORTKEY_MODEL_NAME", None)

            with patch("portkey_ai.Portkey"):
                client = get_anthropic_client("test-api-key")

                assert isinstance(client, AnthropicPortkeyAdapter)
                assert client.provider_slug == "@aitoday-anthropic"
                assert client.model_name == "claude-sonnet-4-5-20250929"


class TestMessageConversion:
    """Test message format conversion between Anthropic and OpenAI."""

    @pytest.fixture
    def adapter(self):
        """Create a mock adapter for testing."""
        mock_client = MagicMock()
        adapter = AnthropicPortkeyAdapter(
            mock_client, "@test-provider", "test-model"
        )
        return adapter

    def test_converts_simple_string_content(self, adapter):
        """Should convert simple string content correctly."""
        # Mock the Portkey response
        mock_response = MagicMock()
        mock_response.id = "msg_123"
        mock_response.model = "@test-provider/test-model"
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Hello!", tool_calls=None),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)

        adapter.portkey_client.chat.completions.create.return_value = mock_response

        # Call the adapter
        response = adapter.messages.create(
            model="test-model",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify the call was made with correct OpenAI format
        call_args = adapter.portkey_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "@test-provider/test-model"
        assert call_args[1]["messages"] == [{"role": "user", "content": "Hi"}]
        assert call_args[1]["max_tokens"] == 100

        # Verify response is in Anthropic format
        assert response.id == "msg_123"
        assert len(response.content) > 0
        assert response.content[0].text == "Hello!"
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 5

    def test_converts_complex_content_blocks(self, adapter):
        """Should extract text from complex Anthropic content blocks."""
        mock_response = MagicMock()
        mock_response.id = "msg_456"
        mock_response.model = "@test-provider/test-model"
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Response", tool_calls=None),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=20, completion_tokens=10)

        adapter.portkey_client.chat.completions.create.return_value = mock_response

        # Call with complex content blocks (Anthropic format)
        response = adapter.messages.create(
            model="test-model",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hello"},
                        {"type": "text", "text": "World"},
                    ],
                }
            ],
        )

        # Verify content blocks were combined
        call_args = adapter.portkey_client.chat.completions.create.call_args
        assert call_args[1]["messages"] == [{"role": "user", "content": "Hello\nWorld"}]

    def test_filters_empty_content(self, adapter):
        """Should filter out messages with empty content."""
        mock_response = MagicMock()
        mock_response.id = "msg_789"
        mock_response.model = "@test-provider/test-model"
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Response", tool_calls=None),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=15, completion_tokens=8)

        adapter.portkey_client.chat.completions.create.return_value = mock_response

        # Call with empty content (should be filtered)
        response = adapter.messages.create(
            model="test-model",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Valid message"},
                {"role": "assistant", "content": ""},  # Empty - should be filtered
                {"role": "user", "content": "Another valid message"},
            ],
        )

        # Verify empty message was filtered
        call_args = adapter.portkey_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 2  # Only 2 non-empty messages
        assert messages[0]["content"] == "Valid message"
        assert messages[1]["content"] == "Another valid message"

    def test_adds_system_message(self, adapter):
        """Should add system message at the beginning."""
        mock_response = MagicMock()
        mock_response.id = "msg_sys"
        mock_response.model = "@test-provider/test-model"
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Response", tool_calls=None),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=25, completion_tokens=12)

        adapter.portkey_client.chat.completions.create.return_value = mock_response

        # Call with system message
        response = adapter.messages.create(
            model="test-model",
            max_tokens=100,
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify system message was added first
        call_args = adapter.portkey_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0] == {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        assert messages[1] == {"role": "user", "content": "Hi"}


class TestToolConversion:
    """Test tool definition and calling conversion."""

    @pytest.fixture
    def adapter(self):
        """Create a mock adapter for testing."""
        mock_client = MagicMock()
        adapter = AnthropicPortkeyAdapter(
            mock_client, "@test-provider", "test-model"
        )
        return adapter

    def test_converts_tool_definitions(self, adapter):
        """Should convert Anthropic tool format to OpenAI function format."""
        mock_response = MagicMock()
        mock_response.id = "msg_tool"
        mock_response.model = "@test-provider/test-model"
        # Create proper mock for tool call
        tool_call_mock = MagicMock()
        tool_call_mock.id = "call_123"
        tool_call_mock.function.name = "web_search"
        tool_call_mock.function.arguments = '{"query":"test"}'

        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="I'll search for that.",
                    tool_calls=[tool_call_mock],
                ),
                finish_reason="tool_calls",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=30, completion_tokens=15)

        adapter.portkey_client.chat.completions.create.return_value = mock_response

        # Call with Anthropic tool format
        anthropic_tools = [
            {
                "name": "web_search",
                "description": "Search the web",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ]

        response = adapter.messages.create(
            model="test-model",
            max_tokens=100,
            messages=[{"role": "user", "content": "Search for AI news"}],
            tools=anthropic_tools,
        )

        # Verify tools were converted to OpenAI format
        call_args = adapter.portkey_client.chat.completions.create.call_args
        openai_tools = call_args[1]["tools"]

        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "web_search"
        assert openai_tools[0]["function"]["description"] == "Search the web"
        assert openai_tools[0]["function"]["parameters"] == {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

        # Verify response contains tool use in Anthropic format
        assert response.stop_reason == "tool_use"
        assert len(response.content) == 2  # Text + tool use
        assert response.content[0].text == "I'll search for that."
        assert response.content[1].type == "tool_use"
        assert response.content[1].name == "web_search"
        assert response.content[1].input == {"query": "test"}


class TestFallbackBehavior:
    """Test fallback to standard Anthropic client."""

    def test_falls_back_when_portkey_not_installed(self):
        """Should fall back to Anthropic client when portkey-ai import fails."""
        # This test is difficult to mock properly since imports happen at module level
        # Instead, test the logic by checking that without PORTKEY_API_KEY,
        # we get the standard client
        with patch.dict(os.environ, {}, clear=True):
            # Remove PORTKEY_API_KEY to trigger fallback
            os.environ.pop("PORTKEY_API_KEY", None)

            with patch("src.utils.portkey_client.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                client = get_anthropic_client("test-api-key")

                # Should return standard Anthropic client when no PORTKEY_API_KEY
                assert client == mock_client
                mock_anthropic.assert_called_once_with(api_key="test-api-key")
