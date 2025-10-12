"""
Tests for rate limit handling in SmartSearchTool
"""

import pytest
from unittest.mock import MagicMock, patch
from src.utils.smart_search_tool import (
    SmartSearchTool,
    RateLimitError,
    OllamaProvider,
    SerperProvider,
)


class TestRateLimitHandling:
    """Test rate limit detection and provider skipping"""

    def test_rate_limit_error_raised_on_402(self):
        """Test that providers raise RateLimitError on 402 status"""
        provider = OllamaProvider(api_key="test_key")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 402
            mock_response.text = '{"error": "rate limit exceeded"}'
            mock_post.return_value = mock_response

            with pytest.raises(RateLimitError):
                provider.search("test query")

    def test_rate_limit_error_raised_on_429(self):
        """Test that providers raise RateLimitError on 429 status"""
        provider = SerperProvider(api_key="test_key")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Too Many Requests"
            mock_post.return_value = mock_response

            with pytest.raises(RateLimitError):
                provider.search("test query")

    def test_provider_skipped_after_rate_limit(self):
        """Test that rate-limited provider is skipped in subsequent searches"""
        # Create tool with serper API key (first provider)
        with patch.dict("os.environ", {"SERPER_API_KEY": "test_key"}, clear=True):
            tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

            # Mock the first provider (SerperProvider) to raise RateLimitError
            with patch.object(
                tool.providers[0], "search", side_effect=RateLimitError("Rate limit hit")
            ):
                # First search should trigger rate limit
                result1 = tool.search("test query 1")

                # Check that provider was marked as rate-limited
                assert "SerperProvider" in tool.rate_limited_providers

                # Second search should skip the rate-limited provider
                result2 = tool.search("test query 2")

                # Provider should still be in rate-limited set
                assert "SerperProvider" in tool.rate_limited_providers

    def test_rate_limit_tracking_in_status(self):
        """Test that rate-limited providers appear in status"""
        tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

        # Manually mark provider as rate-limited
        tool.rate_limited_providers.add("SerperProvider")

        status = tool.get_status()

        assert "rate_limited_providers" in status
        assert "SerperProvider" in status["rate_limited_providers"]

    def test_reset_rate_limits(self):
        """Test that rate limit tracking can be reset"""
        tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

        # Mark provider as rate-limited
        tool.rate_limited_providers.add("SerperProvider")
        assert len(tool.rate_limited_providers) == 1

        # Reset
        tool.reset_rate_limits()

        # Should be empty now
        assert len(tool.rate_limited_providers) == 0

    def test_fallback_to_next_provider_on_rate_limit(self):
        """Test that search falls back to next provider when first is rate-limited"""
        # Create tool with Serper (will be first) and ensure SearXNG is second
        with patch.dict("os.environ", {"SERPER_API_KEY": "test1"}, clear=True):
            tool = SmartSearchTool(serper_api_key="test1", enable_cache=False)

            # Mock first provider (Serper) to raise RateLimitError
            mock_results = [{"title": "Test", "snippet": "Test snippet", "link": "http://test.com"}]

            with patch.object(
                tool.providers[0], "search", side_effect=RateLimitError("Rate limit")
            ):
                with patch.object(tool.providers[1], "search", return_value=mock_results):
                    result = tool.search("test query")

                    # Should have gotten results from second provider (SearXNG)
                    assert result["results"] == mock_results
                    assert result["provider"] == "SearXNGProvider"
                    assert "SerperProvider" in tool.rate_limited_providers

    def test_rate_limited_provider_skipped_immediately_on_second_call(self):
        """Test that rate-limited provider is not tried again on subsequent calls"""
        with patch.dict("os.environ", {"SERPER_API_KEY": "test_key"}, clear=True):
            tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

            # Manually mark first provider (Serper) as rate-limited
            tool.rate_limited_providers.add("SerperProvider")

            # Mock provider search - should NOT be called
            with patch.object(tool.providers[0], "search") as mock_search:
                mock_search.return_value = []

                # Do a search
                tool.search("test query")

                # Provider's search method should NOT have been called
                mock_search.assert_not_called()

    def test_non_rate_limit_errors_dont_mark_provider(self):
        """Test that other errors don't mark provider as rate-limited"""
        with patch.dict("os.environ", {"SERPER_API_KEY": "test_key"}, clear=True):
            tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

            # Mock provider to return empty results (simulating error handled internally)
            with patch.object(tool.providers[0], "search", return_value=[]):
                result = tool.search("test query")

                # Provider should NOT be marked as rate-limited
                assert "SerperProvider" not in tool.rate_limited_providers

    def test_empty_results_dont_mark_provider_as_rate_limited(self):
        """Test that empty results don't mark provider as rate-limited"""
        with patch.dict("os.environ", {"SERPER_API_KEY": "test_key"}, clear=True):
            tool = SmartSearchTool(serper_api_key="test_key", enable_cache=False)

            # Mock provider to return empty results
            with patch.object(tool.providers[0], "search", return_value=[]):
                result = tool.search("test query")

                # Provider should NOT be marked as rate-limited
                assert "SerperProvider" not in tool.rate_limited_providers


class TestRateLimitErrorPropagation:
    """Test that RateLimitError is properly raised from all providers"""

    def test_ollama_raises_rate_limit_on_402(self):
        """OllamaProvider raises RateLimitError on 402"""
        provider = OllamaProvider(api_key="test")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 402
            mock_response.text = "Payment required"
            mock_post.return_value = mock_response

            with pytest.raises(RateLimitError, match="Ollama rate limit"):
                provider.search("test")

    def test_serper_raises_rate_limit_on_429(self):
        """SerperProvider raises RateLimitError on 429"""
        provider = SerperProvider(api_key="test")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Too many requests"
            mock_post.return_value = mock_response

            with pytest.raises(RateLimitError, match="Serper rate limit"):
                provider.search("test")
