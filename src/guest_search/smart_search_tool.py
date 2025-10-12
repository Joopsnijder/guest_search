"""
Smart Search Tool with Automatic Fallback
Auteur: Joop Snijder
Versie: 1.1

Dit systeem schakelt automatisch tussen search providers:
1. Ollama Web Search (nieuw, generous gratis tier)
2. Serper (tot 2,500 gratis searches)
3. SearXNG (gratis, self-hosted of public instances)
4. Brave Search (gratis tier beschikbaar)
5. Web scraping als laatste redmiddel
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import requests
from dotenv import load_dotenv

# Voor web scraping fallback
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom exception for rate limiting
class RateLimitError(Exception):
    """Raised when a provider hits rate limits"""

    pass


# ============================================
# SEARCH RESULT CACHING
# ============================================


class SearchResultCache:
    """Cache search results for 1 day to reduce rate limits and improve testing speed"""

    def __init__(self, cache_file: str = "data/cache/search_results.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(days=1)
        self.cache_data = self.load_cache()

    def load_cache(self) -> dict:
        """Load cached search results"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load search cache: {e}")
        return {}

    def save_cache(self):
        """Save cache data to file"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to save search cache: {e}")

    def _generate_cache_key(self, query: str, provider: str, **kwargs) -> str:
        """Generate a unique cache key for a search query"""
        import hashlib

        # Create a consistent string from query, provider and relevant kwargs
        key_components = [
            query.lower().strip(),
            provider,
            str(kwargs.get("num_results", 10)),
            str(kwargs.get("language", "nl")),
        ]

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()

    def get_cached_results(
        self, query: str, provider: str, **kwargs
    ) -> list[dict[str, Any]] | None:
        """Get cached results if available and not expired"""
        cache_key = self._generate_cache_key(query, provider, **kwargs)

        if cache_key not in self.cache_data:
            return None

        cached_entry = self.cache_data[cache_key]
        cached_time = datetime.fromisoformat(cached_entry["timestamp"])

        # Check if cache is still valid (within 1 day)
        if datetime.now() - cached_time > self.cache_duration:
            # Remove expired entry
            del self.cache_data[cache_key]
            self.save_cache()
            return None

        result_count = len(cached_entry["results"])
        logger.info(
            f"Cache hit for query '{query}' with provider '{provider}' - {result_count} results"
        )
        return cached_entry["results"]

    def cache_results(self, query: str, provider: str, results: list[dict[str, Any]], **kwargs):
        """Cache search results"""
        cache_key = self._generate_cache_key(query, provider, **kwargs)

        self.cache_data[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "provider": provider,
            "results": results,
            "result_count": len(results),
        }

        self.save_cache()
        logger.info(f"Cached {len(results)} results for query '{query}' with provider '{provider}'")

    def clear_expired_entries(self):
        """Remove all expired cache entries"""
        current_time = datetime.now()
        expired_keys = []

        for key, entry in self.cache_data.items():
            try:
                cached_time = datetime.fromisoformat(entry["timestamp"])
                if current_time - cached_time > self.cache_duration:
                    expired_keys.append(key)
            except (ValueError, KeyError):
                # Invalid timestamp or entry, mark for deletion
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache_data[key]

        if expired_keys:
            self.save_cache()
            logger.info(f"Removed {len(expired_keys)} expired cache entries")

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        self.clear_expired_entries()  # Clean up first

        stats = {
            "total_entries": len(self.cache_data),
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
            "oldest_entry": None,
            "newest_entry": None,
        }

        if self.cache_data:
            timestamps = []
            for entry in self.cache_data.values():
                try:
                    timestamps.append(datetime.fromisoformat(entry["timestamp"]))
                except (ValueError, KeyError):
                    continue

            if timestamps:
                stats["oldest_entry"] = min(timestamps).isoformat()
                stats["newest_entry"] = max(timestamps).isoformat()

        return stats


# ============================================
# SEARCH PROVIDERS
# ============================================


class SearchProvider(ABC):
    """Abstract base class voor search providers"""

    @abstractmethod
    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Voer een zoekopdracht uit"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check of deze provider beschikbaar is"""
        pass


class OllamaProvider(SearchProvider):
    """Ollama web search provider met gratis tier"""

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.base_url = "https://ollama.com/api/web_search"

    def is_available(self) -> bool:
        """Check of Ollama beschikbaar is"""
        return bool(self.api_key)

    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Zoek via Ollama Web Search API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {"query": query, "max_results": kwargs.get("num_results", 10)}

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Parse Ollama search results format
                for item in data.get("results", []):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", "") or item.get("description", ""),
                            "link": item.get("url", "") or item.get("link", ""),
                            "source": "ollama",
                        }
                    )

                logger.info(f"Ollama search succesvol: {len(results)} resultaten")
                return results
            elif response.status_code in (402, 429):
                # Rate limit or payment required
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise RateLimitError(f"Ollama rate limit hit: {response.status_code}")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return []

        except RateLimitError:
            raise  # Re-raise rate limit errors
        except Exception as e:
            logger.error(f"Ollama search failed: {e}")
            return []


class SerperProvider(SearchProvider):
    """Serper.dev search provider"""

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"

    def is_available(self) -> bool:
        """Check of Serper beschikbaar is"""
        return bool(self.api_key)

    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Zoek via Serper API"""
        try:
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

            payload = {"q": query, "num": kwargs.get("num_results", 10)}

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Parse organic results
                for item in data.get("organic", []):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "source": "serper",
                        }
                    )

                logger.info(f"Serper search succesvol: {len(results)} resultaten")
                return results
            elif response.status_code in (402, 429):
                logger.error(f"Serper API error: {response.status_code}")
                raise RateLimitError(f"Serper rate limit hit: {response.status_code}")
            else:
                logger.error(f"Serper API error: {response.status_code}")
                return []

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []


class SearXNGInstanceManager:
    """Manages SearXNG instances with dynamic discovery and caching"""

    INSTANCES_API_URL = "https://searx.space/data/instances.json"
    CACHE_FILE = Path("data/cache/searxng_instances.json")
    CACHE_DURATION = timedelta(days=1)

    # Fallback instances if API fails
    FALLBACK_INSTANCES = [
        "https://searx.be",
        "https://searx.work",
        "https://search.bus-hit.me",
        "https://search.sapti.me",
        "https://searx.tiekoetter.com",
    ]

    def __init__(self):
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.instances = []
        self._load_instances()

    def _load_instances(self):
        """Load instances from cache or fetch from API"""
        try:
            # Try to load from cache first
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE) as f:
                    cache_data = json.load(f)

                # Check if cache is still valid
                cache_time = datetime.fromisoformat(cache_data.get("cached_at", ""))
                if datetime.now() - cache_time < self.CACHE_DURATION:
                    self.instances = cache_data.get("instances", [])
                    logger.info(f"Loaded {len(self.instances)} SearXNG instances from cache")
                    return

            # Cache is stale or doesn't exist, fetch from API
            self._fetch_and_cache_instances()

        except Exception as e:
            logger.warning(f"Failed to load instances: {e}")
            self.instances = self.FALLBACK_INSTANCES.copy()
            logger.info(f"Using fallback instances: {len(self.instances)}")

    def _fetch_and_cache_instances(self):
        """Fetch instances from API and cache them"""
        try:
            logger.info("Fetching SearXNG instances from API...")
            response = requests.get(self.INSTANCES_API_URL, timeout=10)

            if response.status_code == 200:
                data = response.json()
                instances_data = data.get("instances", {})
                logger.info(f"API returned {len(instances_data)} instances")

                # Filter instances with 100% daily uptime
                good_instances = []
                high_uptime_instances = []
                total_with_uptime = 0

                for url, instance_data in instances_data.items():
                    if isinstance(instance_data, dict):
                        uptime = instance_data.get("uptime", {})
                        if uptime is None:
                            continue  # Skip instances without uptime data
                        uptime_day = uptime.get("uptimeDay")

                        if uptime_day is not None:
                            total_with_uptime += 1
                            # Debug: collect instances with high uptime for fallback
                            if uptime_day >= 99.0:
                                high_uptime_instances.append((url, uptime_day))

                            # Primary filter: 100% uptime
                            if uptime_day == 100.0:
                                if url and url.startswith("http"):
                                    good_instances.append(url)

                logger.info(f"Found {total_with_uptime} instances with uptime data")
                logger.info(f"Found {len(high_uptime_instances)} instances with 99%+ uptime")
                logger.info(f"Found {len(good_instances)} instances with 100% uptime")

                # If no 100% uptime instances, use 99%+ as fallback
                if not good_instances and high_uptime_instances:
                    logger.info("No 100% uptime instances found, using 99%+ uptime instances")
                    good_instances = [
                        url
                        for url, _ in sorted(
                            high_uptime_instances, key=lambda x: x[1], reverse=True
                        )[:10]
                    ]

                if good_instances:
                    self.instances = good_instances

                    # Cache the results
                    cache_data = {
                        "instances": self.instances,
                        "cached_at": datetime.now().isoformat(),
                        "count": len(self.instances),
                    }

                    with open(self.CACHE_FILE, "w") as f:
                        json.dump(cache_data, f, indent=2)

                    logger.info(f"Cached {len(self.instances)} instances with 100% uptime")
                else:
                    raise ValueError("No instances with 100% uptime found")

            else:
                raise ValueError(f"API returned {response.status_code}")

        except Exception as e:
            logger.warning(f"Failed to fetch instances from API: {e}")
            # Fall back to cached instances or fallback list
            if not self.instances:
                self.instances = self.FALLBACK_INSTANCES.copy()
                logger.info("Using hardcoded fallback instances")

    def get_instances(self) -> list[str]:
        """Get list of available instances"""
        return self.instances.copy()

    def refresh_instances(self):
        """Force refresh instances from API"""
        self._fetch_and_cache_instances()


class SearXNGProvider(SearchProvider):
    """SearXNG search provider (gratis, open source)"""

    def __init__(self, instance_url: str | None = None):
        self.instance_manager = SearXNGInstanceManager()
        self.instances = self.instance_manager.get_instances()
        self.instance_url = instance_url or (
            self.instances[0] if self.instances else "https://searx.be"
        )
        self.current_instance_idx = 0

    def rotate_instance(self):
        """Roteer naar volgende instance"""
        if self.instances:
            self.current_instance_idx = (self.current_instance_idx + 1) % len(self.instances)
            self.instance_url = self.instances[self.current_instance_idx]
            logger.info(f"Rotated to SearXNG instance: {self.instance_url}")
        else:
            logger.warning("No instances available to rotate to")

    def is_available(self) -> bool:
        """Check of SearXNG beschikbaar is"""
        return True  # Always available as a free option

    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Zoek via SearXNG"""
        max_retries = 3

        for _attempt in range(max_retries):
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "language": "nl",
                    "engines": "google,bing,duckduckgo",
                }

                response = requests.get(
                    f"{self.instance_url}/search",
                    params=params,
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"},
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    for item in data.get("results", [])[:10]:
                        results.append(
                            {
                                "title": item.get("title", ""),
                                "snippet": item.get("content", ""),
                                "link": item.get("url", ""),
                                "source": "searxng",
                            }
                        )

                    logger.info(f"SearXNG search succesvol: {len(results)} resultaten")
                    return results
                else:
                    logger.warning(
                        f"SearXNG instance {self.instance_url} returned {response.status_code}"
                    )
                    self.rotate_instance()

            except Exception as e:
                logger.warning(f"SearXNG instance {self.instance_url} failed: {e}")
                self.rotate_instance()

        return []


class BraveProvider(SearchProvider):
    """Brave Search provider (heeft gratis tier met 1 req/sec limit)"""

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.last_request_time = 0  # Track last request for rate limiting

    def is_available(self) -> bool:
        """Check of Brave beschikbaar is"""
        return bool(self.api_key)

    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Zoek via Brave Search API (respects 1 req/sec rate limit)"""
        import time

        try:
            # Enforce 1 request per second rate limit
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < 1.0:
                sleep_time = 1.0 - time_since_last
                logger.info(f"Brave rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

            headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}

            params = {"q": query, "count": kwargs.get("num_results", 10)}

            self.last_request_time = time.time()  # Update before request
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("web", {}).get("results", []):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("description", ""),
                            "link": item.get("url", ""),
                            "source": "brave",
                        }
                    )

                logger.info(f"Brave search succesvol: {len(results)} resultaten")
                return results
            elif response.status_code in (402, 429):
                logger.error(f"Brave API error: {response.status_code}")
                raise RateLimitError(f"Brave rate limit hit: {response.status_code}")
            else:
                logger.error(f"Brave API error: {response.status_code}")
                return []

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []


class GoogleScraperProvider(SearchProvider):
    """Laatste redmiddel: scrape Google search (gebruik voorzichtig!)"""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def is_available(self) -> bool:
        """Altijd beschikbaar als laatste optie"""
        return True

    def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Scrape Google search results (laatste redmiddel)"""
        try:
            # Gebruik httpx voor betere async support
            with httpx.Client() as client:
                response = client.get(
                    "https://www.google.com/search",
                    params={"q": query, "hl": "nl"},
                    headers=self.headers,
                    timeout=10,
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    results = []

                    # Parse search results - try multiple selectors as Google changes them
                    search_divs = []

                    # Try different selectors Google uses
                    for selector in ["div.g", "div[data-ved]", ".g", ".tF2Cxc"]:
                        search_divs = soup.select(selector)
                        if search_divs:
                            break

                    if not search_divs:
                        logger.warning("No search result containers found")
                        return []

                    for g in search_divs[:5]:  # Alleen top 5
                        title_elem = g.find("h3")
                        if not title_elem:
                            # Try alternative selectors for title
                            title_elem = g.select_one("h3, .LC20lb, .DKV0Md")

                        link_elem = g.find("a")
                        if not link_elem:
                            # Try alternative selectors for link
                            link_elem = g.select_one("a[href]")

                        # Try multiple selectors for snippets
                        snippet_elem = None
                        for snippet_selector in [".aCOpRe", ".VwiC3b", ".s3v9rd", ".st"]:
                            snippet_elem = g.select_one(snippet_selector)
                            if snippet_elem:
                                break

                        if title_elem and link_elem:
                            href = link_elem.get("href", "")
                            # Clean up href if it's a Google redirect
                            if href.startswith("/url?q="):
                                try:
                                    from urllib.parse import parse_qs, urlparse

                                    parsed = urlparse(href)
                                    href = parse_qs(parsed.query).get("q", [href])[0]
                                except Exception:
                                    pass  # Keep original href if parsing fails

                            results.append(
                                {
                                    "title": title_elem.get_text().strip(),
                                    "snippet": snippet_elem.get_text().strip()
                                    if snippet_elem
                                    else "",
                                    "link": href,
                                    "source": "google_scraper",
                                }
                            )

                    logger.info(f"Google scraper: {len(results)} resultaten")
                    return results

        except Exception as e:
            logger.error(f"Google scraper failed: {e}")

        return []


# ============================================
# SMART SEARCH TOOL
# ============================================


class SmartSearchTool:
    """
    Intelligente search tool met automatische fallback en rate limit handling

    Features:
    - Multi-provider fallback (Serper → SearXNG → Brave → Google Scraper)
    - Automatic rate limit detection (HTTP 402/429)
    - Session-based provider skipping when rate limited
    - 1-day result caching for performance

    Provider Priority:
    1. Serper - Best quality with rich snippets (primary choice)
    2. SearXNG - Free, unlimited, variable quality
    3. Brave - Good quality with snippets (requires API key)
    4. Google Scraper - Last resort fallback

    Note: Ollama provider disabled by default due to empty snippets issue
    """

    def __init__(
        self,
        ollama_api_key: str | None = None,
        serper_api_key: str | None = None,
        brave_api_key: str | None = None,
        searxng_instance: str | None = None,
        enable_cache: bool = True,
    ):
        # Initialize cache only
        self.cache = SearchResultCache() if enable_cache else None

        # Track rate-limited providers for current session
        self.rate_limited_providers = set()

        # Initialize providers in priority order
        self.providers = []

        # 1. Serper (best quality results with snippets, gratis tot 2,500/maand)
        if serper_api_key or os.getenv("SERPER_API_KEY"):
            self.providers.append(SerperProvider(serper_api_key or os.getenv("SERPER_API_KEY")))

        # 2. SearXNG (volledig gratis, open source, variable quality)
        self.providers.append(SearXNGProvider(searxng_instance))

        # 3. Brave (good quality with snippets, gratis tier beschikbaar)
        if brave_api_key or os.getenv("BRAVE_API_KEY"):
            self.providers.append(BraveProvider(brave_api_key or os.getenv("BRAVE_API_KEY")))

        # 4. Google Scraper (laatste redmiddel)
        self.providers.append(GoogleScraperProvider())

        # Note: Ollama disabled by default due to empty snippets issue
        # if ollama_api_key or os.getenv("OLLAMA_API_KEY"):
        #     self.providers.append(OllamaProvider(ollama_api_key or os.getenv("OLLAMA_API_KEY")))

        logger.info(f"Smart Search Tool initialized with {len(self.providers)} providers")

    async def search_recent_content(
        self, query: str, max_results: int = 10, days_back: int = 14, language: str = "nl,en"
    ) -> list[dict]:
        """
        Search for recent content within specified timeframe

        Args:
            query: Search query
            max_results: Maximum number of results
            days_back: Number of days to look back
            language: Language filter

        Returns:
            List of search results
        """
        from datetime import datetime, timedelta

        # Add date filter to query
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            # Use existing search method
            search_results = self.search(
                query=query,
                max_results=max_results,
                language=language,
                time_range="recent",  # Provider-specific recent filter
            )

            results = search_results.get("results", [])

            # Filter by date if available
            filtered_results = []
            for result in results:
                # Try to parse date if available
                result_date = result.get("date") or result.get("published_date")
                if result_date:
                    try:
                        # Parse various date formats
                        if isinstance(result_date, str):
                            # Try common formats
                            for _date_format in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d %b %Y"]:
                                try:
                                    parsed_date = datetime.strptime(result_date[:10], "%Y-%m-%d")
                                    if parsed_date >= cutoff_date:
                                        filtered_results.append(result)
                                    break
                                except ValueError:
                                    continue
                        else:
                            filtered_results.append(result)  # Include if date parsing fails
                    except Exception:
                        filtered_results.append(result)  # Include if date parsing fails
                else:
                    # Include results without date (assume recent)
                    filtered_results.append(result)

            logger.info(f"Found {len(filtered_results)} recent results for query: {query}")
            return filtered_results[:max_results]

        except Exception as e:
            logger.error(f"Error in search_recent_content: {e}")
            return []

    def search(self, query: str, **kwargs) -> dict[str, Any]:
        """
        Voer search uit met automatische fallback en caching
        """
        results = []
        used_provider = None
        cache_hit = False

        # Try cache first if enabled (query-based, provider-agnostic)
        if self.cache:
            cached_results = self.cache.get_cached_results(query, "any", **kwargs)

            if cached_results is not None and len(cached_results) > 0:
                results = cached_results
                used_provider = "cached"
                cache_hit = True
                logger.info(f"Cache hit for query '{query}': {len(results)} results")

        # If no cache hit, search with providers
        if not cache_hit:
            for provider in self.providers:
                provider_name = provider.__class__.__name__

                # Skip rate-limited providers
                if provider_name in self.rate_limited_providers:
                    logger.info(f"⏭️  Skipping {provider_name} (rate limited during this session)")
                    continue

                if provider.is_available():
                    logger.info(f"Trying search with {provider_name}")
                    try:
                        results = provider.search(query, **kwargs)

                        if results:
                            used_provider = provider_name
                            logger.info(f"Success with {provider_name}: {len(results)} results")

                            # Cache the results if caching is enabled (only cache non-empty)
                            # Cache under generic "any" provider so any provider can retrieve it
                            if self.cache and len(results) > 0:
                                self.cache.cache_results(query, "any", results, **kwargs)

                            break
                        else:
                            logger.warning(f"{provider_name} returned no results")
                    except RateLimitError as e:
                        # Mark provider as rate-limited for rest of session
                        self.rate_limited_providers.add(provider_name)
                        logger.warning(
                            f"⚠️  {provider_name} rate limited, skipping for rest of session: {e}"
                        )
                        # Continue to next provider
                        continue
                else:
                    logger.info(f"{provider_name} not available, trying next")

        # Format response
        return {
            "query": query,
            "provider": used_provider,
            "results": results,
            "cache_hit": cache_hit,
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self) -> dict[str, Any]:
        """Krijg status van alle providers en cache"""
        status: dict[str, Any] = {
            "providers": [p.__class__.__name__ for p in self.providers],
            "rate_limited_providers": list(self.rate_limited_providers),
        }

        # Add cache statistics if caching is enabled
        if self.cache:
            status["cache"] = self.cache.get_cache_stats()

        return status

    def clear_cache(self):
        """Clear all cached search results"""
        if self.cache:
            self.cache.clear_expired_entries()
            logger.info("Cleared expired cache entries")
        else:
            logger.info("Caching not enabled")

    def reset_rate_limits(self):
        """Reset rate limit tracking (useful for new sessions)"""
        self.rate_limited_providers.clear()
        logger.info("Rate limit tracking reset")

    def disable_cache(self):
        """Disable caching for testing or other purposes"""
        self.cache = None
        logger.info("Search result caching disabled")

    def enable_cache(self):
        """Re-enable caching"""
        if not self.cache:
            self.cache = SearchResultCache()
            logger.info("Search result caching enabled")

    def run(self, query: str) -> str:
        """
        CrewAI compatible run method
        """
        result = self.search(query)

        # Format voor CrewAI
        if result["results"]:
            formatted = f"Search results for '{query}' (via {result['provider']}):\n\n"
            for i, r in enumerate(result["results"][:5], 1):
                formatted += f"{i}. {r['title']}\n"
                formatted += f"   {r['snippet']}\n"
                formatted += f"   URL: {r['link']}\n\n"
            return formatted
        else:
            return f"No results found for '{query}'"


# ============================================
# TEST & DEMO
# ============================================

if __name__ == "__main__":
    # Test de smart search tool
    print("=" * 50)
    print("SMART SEARCH TOOL - TEST")
    print("=" * 50)

    # Initialize
    tool = SmartSearchTool(
        ollama_api_key=os.getenv("OLLAMA_API_KEY"),
        serper_api_key=os.getenv("SERPER_API_KEY"),
        brave_api_key=os.getenv("BRAVE_API_KEY"),
    )

    # Show status
    print("\nProvider Status:")
    status = tool.get_status()
    for provider in status["providers"]:
        print(f"  - {provider}")

    # Show cache stats if available
    if "cache" in status:
        print("\nCache Status:")
        print(f"  Entries: {status['cache']['total_entries']}")
        print(f"  File size: {status['cache']['cache_file_size']} bytes")

    # Test search
    test_query = "OpenAI GPT-4 parameters aantal"
    print(f"\nTesting search: '{test_query}'")

    result = tool.search(test_query)

    print(f"\nUsed provider: {result['provider']}")
    print(f"Results found: {len(result['results'])}")

    if result["results"]:
        print("\nTop 3 results:")
        for i, r in enumerate(result["results"][:3], 1):
            print(f"\n{i}. {r['title']}")
            print(f"   {r['snippet'][:100]}...")
            print(f"   {r['link']}")
