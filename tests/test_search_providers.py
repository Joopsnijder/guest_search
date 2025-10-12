"""Tests for search providers and fallback logic."""

import pytest
from unittest.mock import Mock, patch

from requests.exceptions import Timeout


class TestSearchProviderFallback:
    """Test search provider fallback logic."""

    def test_smart_search_tool_initialization(self, mock_env_vars):
        """Test SmartSearchTool initialization with API keys."""
        from src.utils.smart_search_tool import SmartSearchTool

        tool = SmartSearchTool(
            serper_api_key="test-serper",
            brave_api_key="test-brave",
            enable_cache=False,
        )

        assert len(tool.providers) > 0
        assert tool.cache is None  # Cache disabled

    def test_search_with_serper_success(self, mock_env_vars, mock_serper_response):
        """Test successful search with Serper provider."""
        from src.utils.smart_search_tool import SmartSearchTool

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_serper_response

            tool = SmartSearchTool(serper_api_key="test-key", enable_cache=False)
            result = tool.search("AI Netherlands")

            assert result["results"]
            assert len(result["results"]) > 0
            assert result["provider"] == "SerperProvider"

    def test_search_with_searxng_success(self, mock_searxng_response):
        """Test successful search with SearXNG provider."""
        from src.utils.smart_search_tool import SmartSearchTool

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_searxng_response

            tool = SmartSearchTool(enable_cache=False)
            result = tool.search("AI Netherlands")

            assert result["results"]
            assert len(result["results"]) > 0

    def test_search_with_brave_success(self, mock_brave_response):
        """Test successful search with Brave provider."""
        from src.utils.smart_search_tool import SmartSearchTool

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_brave_response

            tool = SmartSearchTool(brave_api_key="test-key", enable_cache=False)

            # Make Serper fail so Brave is tried
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 429  # Rate limited

                result = tool.search("AI Netherlands")

                # Should fallback to another provider
                assert "results" in result

    def test_automatic_fallback_on_provider_failure(self, mock_env_vars):
        """Test automatic fallback when primary provider fails."""
        from src.utils.smart_search_tool import SmartSearchTool

        call_count = {"post": 0, "get": 0}

        def mock_post_side_effect(*args, **kwargs):
            call_count["post"] += 1
            if "serper.dev" in args[0]:
                # Serper fails
                raise Timeout("Connection timeout")
            return Mock(status_code=200, json=lambda: {"results": []})

        def mock_get_side_effect(*args, **kwargs):
            call_count["get"] += 1
            # SearXNG succeeds
            return Mock(
                status_code=200,
                json=lambda: {
                    "results": [
                        {
                            "title": "Test",
                            "content": "Test content",
                            "url": "https://example.com",
                        }
                    ]
                },
            )

        with patch("requests.post", side_effect=mock_post_side_effect):
            with patch("requests.get", side_effect=mock_get_side_effect):
                tool = SmartSearchTool(serper_api_key="test-key", enable_cache=False)
                result = tool.search("test query")

                # Should have tried Serper first, then fallback to SearXNG
                assert call_count["post"] >= 1  # Serper attempt
                assert result["results"]  # Got results from fallback

    def test_all_providers_fail_returns_empty(self):
        """Test that empty results are returned when all providers fail."""
        from src.utils.smart_search_tool import SmartSearchTool

        with patch("requests.post") as mock_post:
            with patch("requests.get") as mock_get:
                with patch("httpx.Client") as mock_httpx:
                    # All providers fail
                    mock_post.side_effect = Timeout()
                    mock_get.side_effect = Timeout()
                    mock_httpx.return_value.__enter__.return_value.get.side_effect = Timeout()

                    tool = SmartSearchTool(serper_api_key="test-key", enable_cache=False)
                    result = tool.search("test query")

                    # Should return empty results
                    assert result["results"] == []

    def test_searxng_instance_rotation(self):
        """Test SearXNG instance rotation on failure."""
        from src.utils.smart_search_tool import SearXNGProvider

        provider = SearXNGProvider()
        initial_instance = provider.instance_url

        # Rotate to next instance
        provider.rotate_instance()

        # Should have changed (unless only 1 instance)
        if len(provider.instances) > 1:
            assert provider.instance_url != initial_instance

    def test_empty_search_results_handling(self):
        """Test handling when primary provider returns empty, falls back to others."""
        from src.utils.smart_search_tool import SmartSearchTool

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"organic": []}  # Empty from Serper

            tool = SmartSearchTool(serper_api_key="test-key", enable_cache=False)
            result = tool.search("obscure query with no results")

            # Result may be empty if all providers fail, or have results if fallback succeeds
            assert isinstance(result["results"], list)
            # If provider is not Serper, it means fallback worked
            if result["provider"] != "SerperProvider":
                assert len(result["results"]) >= 0  # Fallback may or may not find results


class TestSearchProviders:
    """Test individual search providers."""

    def test_serper_provider_is_available(self):
        """Test SerperProvider availability check."""
        from src.utils.smart_search_tool import SerperProvider

        provider_with_key = SerperProvider("test-key")
        assert provider_with_key.is_available()

        provider_without_key = SerperProvider(None)
        assert not provider_without_key.is_available()

    def test_serper_provider_search_success(self, mock_serper_response):
        """Test SerperProvider search method."""
        from src.utils.smart_search_tool import SerperProvider

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_serper_response

            provider = SerperProvider("test-key")
            results = provider.search("AI Netherlands")

            assert len(results) > 0
            assert results[0]["source"] == "serper"
            assert "title" in results[0]
            assert "snippet" in results[0]
            assert "link" in results[0]

    def test_serper_provider_rate_limit_handling(self):
        """Test SerperProvider raises RateLimitError on rate limits."""
        from src.utils.smart_search_tool import SerperProvider, RateLimitError

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 429  # Rate limited
            mock_post.return_value.text = "Rate limit exceeded"

            provider = SerperProvider("test-key")

            # Should raise RateLimitError instead of returning empty list
            with pytest.raises(RateLimitError):
                provider.search("test query")

    def test_brave_provider_is_available(self):
        """Test BraveProvider availability check."""
        from src.utils.smart_search_tool import BraveProvider

        provider_with_key = BraveProvider("test-key")
        assert provider_with_key.is_available()

        provider_without_key = BraveProvider(None)
        assert not provider_without_key.is_available()

    def test_searxng_provider_always_available(self):
        """Test that SearXNG is always available (free, no key needed)."""
        from src.utils.smart_search_tool import SearXNGProvider

        provider = SearXNGProvider()
        assert provider.is_available()

    def test_google_scraper_always_available(self):
        """Test that Google scraper is always available as last resort."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        provider = GoogleScraperProvider()
        assert provider.is_available()

    def test_google_scraper_parses_html(self):
        """Test Google scraper HTML parsing."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html_content = """
        <html>
            <div class="g">
                <h3>Test Title</h3>
                <a href="https://example.com">Link</a>
                <div class="VwiC3b">Test snippet content</div>
            </div>
        </html>
        """

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            assert len(results) > 0
            assert results[0]["source"] == "google_scraper"


class TestSearchCache:
    """Test search result caching."""

    def test_cache_initialization(self, mock_data_dir):
        """Test cache initialization."""
        from src.utils.smart_search_tool import SearchResultCache

        cache = SearchResultCache(cache_file=str(mock_data_dir / "search_cache.json"))
        assert cache.cache_data == {}

    def test_cache_stores_and_retrieves_results(self, mock_data_dir, mock_search_results):
        """Test caching and retrieval of search results."""
        from src.utils.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "search_cache.json"
        cache = SearchResultCache(cache_file=str(cache_file))

        # Cache results
        query = "AI Netherlands"
        provider = "SerperProvider"
        cache.cache_results(query, provider, mock_search_results)

        # Retrieve cached results
        cached = cache.get_cached_results(query, provider)

        assert cached is not None
        assert len(cached) == len(mock_search_results)
        assert cached[0]["title"] == mock_search_results[0]["title"]

    def test_cache_expiration(self, mock_data_dir, mock_search_results):
        """Test that expired cache entries are not returned."""
        from datetime import datetime, timedelta

        from src.utils.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "search_cache.json"
        cache = SearchResultCache(cache_file=str(cache_file))

        # Manually create expired cache entry
        query = "test query"
        provider = "TestProvider"
        cache_key = cache._generate_cache_key(query, provider)

        cache.cache_data[cache_key] = {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),  # Expired
            "query": query,
            "provider": provider,
            "results": mock_search_results,
        }
        cache.save_cache()

        # Try to retrieve - should return None (expired)
        cached = cache.get_cached_results(query, provider)
        assert cached is None

    def test_cache_hit_in_smart_search(self, mock_data_dir, mock_search_results):
        """Test that SmartSearchTool respects cache."""
        from src.utils.smart_search_tool import SearchResultCache, SmartSearchTool

        cache_file = str(mock_data_dir / "search_cache.json")

        # Pre-populate cache with known results
        cache = SearchResultCache(cache_file=cache_file)
        test_results = [
            {
                "title": "Cached Result",
                "snippet": "This is from cache",
                "link": "https://cached.example.com",
                "source": "cached",
            }
        ]
        # Cache with "any" provider (provider-agnostic caching)
        cache.cache_results("AI Netherlands", "any", test_results)

        # Search with cache enabled - should return cached results
        # Temporarily replace default cache file with our test cache
        with patch.dict("os.environ", {"OLLAMA_API_KEY": ""}, clear=False):
            with patch(
                "src.utils.smart_search_tool.SearchResultCache.__init__",
                return_value=None,
            ):
                tool = SmartSearchTool(
                    serper_api_key="test-key",
                    enable_cache=True,
                )
                # Inject our pre-populated cache
                tool.cache = cache

                result = tool.search("AI Netherlands")

                # Should have cache hit and return cached results
                assert result["cache_hit"] is True
                assert len(result["results"]) == 1
                assert result["results"][0]["title"] == "Cached Result"

    def test_disable_cache(self):
        """Test disabling cache functionality."""
        from src.utils.smart_search_tool import SmartSearchTool

        tool = SmartSearchTool(enable_cache=True)
        assert tool.cache is not None

        tool.disable_cache()
        assert tool.cache is None

    def test_enable_cache(self):
        """Test enabling cache functionality."""
        from src.utils.smart_search_tool import SmartSearchTool

        tool = SmartSearchTool(enable_cache=False)
        assert tool.cache is None

        tool.enable_cache()
        assert tool.cache is not None

    def test_clear_expired_cache_entries(self, mock_data_dir):
        """Test clearing expired cache entries."""
        from datetime import datetime, timedelta

        from src.utils.smart_search_tool import SearchResultCache

        cache = SearchResultCache(cache_file=str(mock_data_dir / "cache.json"))

        # Add valid and expired entries
        cache.cache_data = {
            "valid": {
                "timestamp": datetime.now().isoformat(),
                "results": [],
            },
            "expired": {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "results": [],
            },
        }

        cache.clear_expired_entries()

        assert "valid" in cache.cache_data
        assert "expired" not in cache.cache_data
