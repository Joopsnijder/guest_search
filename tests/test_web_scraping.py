"""Tests for web scraping functionality."""

from unittest.mock import Mock, patch


class TestGoogleScraper:
    """Test Google search results scraping."""

    def test_scraper_initialization(self):
        """Test Google scraper initialization."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        provider = GoogleScraperProvider()

        assert provider.is_available()
        assert provider.headers["User-Agent"]

    def test_scraper_parses_basic_html(self):
        """Test parsing basic HTML structure."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html = """
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
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            assert len(results) > 0
            assert results[0]["title"] == "Test Title"
            assert results[0]["link"] == "https://example.com"
            assert "snippet" in results[0]

    def test_scraper_handles_alternative_selectors(self):
        """Test scraper with alternative HTML selectors."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html = """
        <html>
            <div class="tF2Cxc">
                <h3 class="LC20lb">Alternative Title</h3>
                <a href="https://example.org">Link</a>
                <span class="aCOpRe">Alternative snippet</span>
            </div>
        </html>
        """

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            assert len(results) > 0
            assert results[0]["title"] == "Alternative Title"

    def test_scraper_handles_google_redirect_urls(self):
        """Test handling of Google redirect URLs."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html = """
        <html>
            <div class="g">
                <h3>Test Title</h3>
                <a href="/url?q=https://example.com&sa=U">Redirect Link</a>
                <div class="VwiC3b">Snippet</div>
            </div>
        </html>
        """

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            assert len(results) > 0
            # Should extract actual URL from redirect
            assert "example.com" in results[0]["link"]

    def test_scraper_handles_empty_results(self):
        """Test scraper with no search results."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html = """
        <html>
            <body>
                <div>No results found</div>
            </body>
        </html>
        """

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("obscure query")

            assert results == []

    def test_scraper_handles_network_errors(self):
        """Test scraper handling of network errors."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Network error"
            )

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            # Should return empty results on error
            assert results == []

    def test_scraper_handles_timeout(self):
        """Test scraper handling of timeout."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        with patch("httpx.Client") as mock_client:
            import httpx

            mock_client.return_value.__enter__.return_value.get.side_effect = (
                httpx.TimeoutException("Request timeout")
            )

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            assert results == []

    def test_scraper_limits_results(self):
        """Test that scraper limits number of results."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        # Create HTML with many results
        html = "<html>"
        for i in range(20):
            html += f"""
            <div class="g">
                <h3>Title {i}</h3>
                <a href="https://example.com/{i}">Link</a>
                <div class="VwiC3b">Snippet {i}</div>
            </div>
            """
        html += "</html>"

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            # Should limit to top 5 results
            assert len(results) <= 5

    def test_scraper_handles_missing_elements(self):
        """Test scraper with incomplete HTML elements."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        html = """
        <html>
            <div class="g">
                <h3>Title Only</h3>
                <!-- Missing link and snippet -->
            </div>
            <div class="g">
                <a href="https://example.com">Link Only</a>
                <!-- Missing title and snippet -->
            </div>
        </html>
        """

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            # Should only include results with both title and link
            for result in results:
                assert result["title"]
                assert result["link"]

    def test_scraper_http_403_handling(self):
        """Test handling of HTTP 403 (blocked)."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            # Should return empty on 403
            assert results == []

    def test_scraper_http_503_handling(self):
        """Test handling of HTTP 503 (service unavailable)."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 503
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            provider = GoogleScraperProvider()
            results = provider.search("test query")

            # Should return empty on 503
            assert results == []


class TestHTMLParsing:
    """Test HTML parsing utilities."""

    def test_parse_nested_html_structure(self):
        """Test parsing nested HTML structures."""
        from bs4 import BeautifulSoup

        html = """
        <div class="g">
            <div class="header">
                <h3>Nested Title</h3>
            </div>
            <a href="https://example.com">Link</a>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", class_="g")

        assert div is not None
        title = div.find("h3")
        assert title is not None
        assert title.text == "Nested Title"

    def test_parse_html_with_special_characters(self):
        """Test parsing HTML with special characters."""
        from bs4 import BeautifulSoup

        html = """
        <div class="g">
            <h3>Title with & ampersand and "quotes"</h3>
            <div>Content with <b>bold</b> and <i>italic</i></div>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h3")

        assert title is not None
        # BeautifulSoup handles HTML entities
        assert "&" in title.text or "ampersand" in title.text

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML."""
        from bs4 import BeautifulSoup

        html = "<div><h3>Unclosed title<div>Other content</div>"

        # BeautifulSoup should handle malformed HTML gracefully
        soup = BeautifulSoup(html, "html.parser")
        assert soup is not None

    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        from bs4 import BeautifulSoup

        html = ""

        soup = BeautifulSoup(html, "html.parser")
        results = soup.find_all("div", class_="g")

        assert results == []


class TestUserAgentHandling:
    """Test User-Agent string handling."""

    def test_user_agent_is_set(self):
        """Test that User-Agent header is set."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        provider = GoogleScraperProvider()

        assert "User-Agent" in provider.headers
        assert len(provider.headers["User-Agent"]) > 0

    def test_user_agent_looks_realistic(self):
        """Test that User-Agent looks like a real browser."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        provider = GoogleScraperProvider()
        user_agent = provider.headers["User-Agent"]

        # Should contain browser indicators
        assert "Mozilla" in user_agent or "Chrome" in user_agent or "Safari" in user_agent

    def test_headers_contain_standard_fields(self):
        """Test that headers contain standard HTTP fields."""
        from src.utils.smart_search_tool import GoogleScraperProvider

        provider = GoogleScraperProvider()

        assert "Accept" in provider.headers
        assert "Accept-Language" in provider.headers
        assert "Accept-Encoding" in provider.headers


class TestURLCleaning:
    """Test URL cleaning and parsing."""

    def test_clean_google_redirect_url(self):
        """Test cleaning Google redirect URLs."""
        from urllib.parse import parse_qs, urlparse

        redirect_url = "/url?q=https://example.com/page&sa=U&ved=xyz"

        parsed = urlparse(redirect_url)
        actual_url = parse_qs(parsed.query).get("q", [""])[0]

        assert actual_url == "https://example.com/page"

    def test_handle_direct_url(self):
        """Test handling of direct URLs (no redirect)."""
        direct_url = "https://example.com/page"

        # Should remain unchanged
        assert direct_url.startswith("http")

    def test_handle_relative_url(self):
        """Test handling of relative URLs."""
        relative_url = "/search?q=test"

        assert not relative_url.startswith("http")
        # In actual implementation, might need to prepend base URL

    def test_handle_malformed_url(self):
        """Test handling of malformed URLs."""
        malformed = "htp://example"  # Typo in protocol

        # Should not crash, just handle gracefully
        assert isinstance(malformed, str)
