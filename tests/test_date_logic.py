"""Tests for date/time logic and calculations."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from freezegun import freeze_time


class TestGuestExclusionLogic:
    """Test logic for excluding recently recommended guests."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    @freeze_time("2024-10-12 10:00:00")
    def test_guest_within_exclusion_window(
        self, mock_anthropic, mock_search_tool, previous_guests_file, monkeypatch
    ):
        """Test that guests within 8-week window are excluded."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        # Jan Jansen was recommended 4 weeks ago (within window)
        result = agent._handle_tool_call("check_previous_guests", {"name": "Jan Jansen"})

        assert result["already_recommended"] is True
        assert result["weeks_ago"] >= 0

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    @freeze_time("2024-10-12 10:00:00")
    def test_guest_outside_exclusion_window(
        self, mock_anthropic, mock_search_tool, previous_guests_file, monkeypatch
    ):
        """Test that guests outside 8-week window are not excluded."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        # Marie van der Berg was recommended 10 weeks ago (outside window)
        result = agent._handle_tool_call("check_previous_guests", {"name": "Marie van der Berg"})

        assert result["already_recommended"] is False

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    @freeze_time("2024-10-12 10:00:00")
    def test_guest_exactly_at_boundary(
        self, mock_anthropic, mock_search_tool, empty_previous_guests_file, monkeypatch
    ):
        """Test guest recommended exactly 8 weeks ago."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(empty_previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        # Add guest from exactly 8 weeks ago
        exactly_8_weeks_ago = datetime.now() - timedelta(weeks=8)
        agent.previous_guests = [
            {
                "name": "Boundary Guest",
                "date": exactly_8_weeks_ago.isoformat(),
                "organization": "Test Org",
            }
        ]

        result = agent._handle_tool_call("check_previous_guests", {"name": "Boundary Guest"})

        # Should be included (8 weeks is still within exclusion)
        assert result["already_recommended"] is True

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_guest_never_recommended(
        self, mock_anthropic, mock_search_tool, empty_previous_guests_file, monkeypatch
    ):
        """Test guest that has never been recommended."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(empty_previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        result = agent._handle_tool_call("check_previous_guests", {"name": "New Person"})

        assert result["already_recommended"] is False

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    @freeze_time("2024-10-12 10:00:00")
    def test_case_insensitive_name_matching(
        self, mock_anthropic, mock_search_tool, previous_guests_file, monkeypatch
    ):
        """Test that name matching is case-insensitive."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        # Test with different cases
        result1 = agent._handle_tool_call("check_previous_guests", {"name": "jan jansen"})
        result2 = agent._handle_tool_call("check_previous_guests", {"name": "JAN JANSEN"})
        result3 = agent._handle_tool_call("check_previous_guests", {"name": "Jan Jansen"})

        # All should match
        assert result1["already_recommended"] is True
        assert result2["already_recommended"] is True
        assert result3["already_recommended"] is True


class TestCacheExpiration:
    """Test cache expiration logic."""

    @freeze_time("2024-10-12 10:00:00")
    def test_cache_valid_within_24_hours(self, mock_data_dir, mock_search_results):
        """Test that cache is valid within 24 hours."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache = SearchResultCache(cache_file=str(mock_data_dir / "cache.json"))

        # Cache results now
        cache.cache_results("test query", "TestProvider", mock_search_results)

        # Retrieve within 24 hours
        with freeze_time("2024-10-12 20:00:00"):  # 10 hours later
            cached = cache.get_cached_results("test query", "TestProvider")

        assert cached is not None
        assert len(cached) == len(mock_search_results)

    @freeze_time("2024-10-12 10:00:00")
    def test_cache_expired_after_24_hours(self, mock_data_dir, mock_search_results):
        """Test that cache expires after 24 hours."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache = SearchResultCache(cache_file=str(mock_data_dir / "cache.json"))

        # Cache results now
        cache.cache_results("test query", "TestProvider", mock_search_results)

        # Try to retrieve after 24+ hours
        with freeze_time("2024-10-14 10:00:01"):  # 48 hours + 1 second later
            cached = cache.get_cached_results("test query", "TestProvider")

        assert cached is None  # Should be expired

    @freeze_time("2024-10-12 10:00:00")
    def test_cache_exactly_at_expiration_boundary(self, mock_data_dir, mock_search_results):
        """Test cache at exactly 24-hour boundary."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache = SearchResultCache(cache_file=str(mock_data_dir / "cache.json"))

        # Cache results now
        cache.cache_results("test query", "TestProvider", mock_search_results)

        # Try to retrieve at exactly 24 hours
        with freeze_time("2024-10-13 10:00:00"):  # Exactly 24 hours later
            cached = cache.get_cached_results("test query", "TestProvider")

        # Should still be valid (expires AFTER 1 day, not AT 1 day)
        assert cached is not None


class TestWeekNumberCalculation:
    """Test week number calculation for reports."""

    @freeze_time("2024-10-12 10:00:00")
    def test_current_week_number(self):
        """Test getting current week number."""
        week_number = datetime.now().isocalendar()[1]

        # October 12, 2024 is week 41
        assert week_number == 41

    @freeze_time("2024-01-01 10:00:00")
    def test_week_number_at_year_start(self):
        """Test week number at start of year."""
        week_number = datetime.now().isocalendar()[1]

        # January 1, 2024 is week 1
        assert week_number == 1

    @freeze_time("2024-12-31 10:00:00")
    def test_week_number_at_year_end(self):
        """Test week number at end of year."""
        week_number = datetime.now().isocalendar()[1]

        # December 31, 2024 might be week 1 of 2025 (depends on ISO week date system)
        assert week_number >= 1


class TestISODateParsing:
    """Test ISO date string parsing."""

    def test_parse_valid_iso_date(self):
        """Test parsing valid ISO date string."""
        date_str = "2024-10-12T10:00:00"
        parsed = datetime.fromisoformat(date_str)

        assert parsed.year == 2024
        assert parsed.month == 10
        assert parsed.day == 12

    def test_parse_iso_date_with_timezone(self):
        """Test parsing ISO date with timezone."""
        date_str = "2024-10-12T10:00:00+02:00"
        parsed = datetime.fromisoformat(date_str)

        assert parsed.year == 2024
        assert parsed.month == 10

    def test_parse_iso_date_with_milliseconds(self):
        """Test parsing ISO date with milliseconds."""
        date_str = "2024-10-12T10:00:00.123456"
        parsed = datetime.fromisoformat(date_str)

        assert parsed.microsecond == 123456

    def test_parse_invalid_iso_date(self):
        """Test parsing invalid ISO date string."""
        date_str = "not a date"

        with pytest.raises(ValueError):
            datetime.fromisoformat(date_str)


class TestTimeDeltaCalculations:
    """Test time delta calculations."""

    def test_weeks_ago_calculation(self):
        """Test calculating weeks ago from a date."""
        now = datetime(2024, 10, 12, 10, 0, 0)
        past_date = datetime(2024, 8, 10, 10, 0, 0)

        weeks_ago = (now - past_date).days // 7

        # Should be approximately 9 weeks
        assert weeks_ago >= 8
        assert weeks_ago <= 10

    def test_days_to_weeks_conversion(self):
        """Test converting days to weeks."""
        days = 56  # Exactly 8 weeks
        weeks = days // 7

        assert weeks == 8

    def test_partial_weeks(self):
        """Test handling of partial weeks."""
        days = 59  # 8 weeks + 3 days
        weeks = days // 7

        # Should round down to 8 weeks
        assert weeks == 8


class TestDateComparisons:
    """Test date comparison logic."""

    @freeze_time("2024-10-12 10:00:00")
    def test_date_is_recent(self):
        """Test checking if date is recent."""
        recent_date = datetime.now() - timedelta(days=5)
        cutoff_date = datetime.now() - timedelta(weeks=8)

        assert recent_date > cutoff_date

    @freeze_time("2024-10-12 10:00:00")
    def test_date_is_old(self):
        """Test checking if date is old."""
        old_date = datetime.now() - timedelta(weeks=10)
        cutoff_date = datetime.now() - timedelta(weeks=8)

        assert old_date < cutoff_date

    def test_same_date_comparison(self):
        """Test comparing identical dates."""
        date1 = datetime(2024, 10, 12, 10, 0, 0)
        date2 = datetime(2024, 10, 12, 10, 0, 0)

        assert date1 == date2

    def test_date_with_different_times(self):
        """Test comparing dates with different times."""
        date1 = datetime(2024, 10, 12, 10, 0, 0)
        date2 = datetime(2024, 10, 12, 14, 0, 0)

        # Same day, different times
        assert date1.date() == date2.date()
        assert date1 != date2


class TestTimezoneHandling:
    """Test timezone handling in date operations."""

    def test_iso_format_preserves_timezone(self):
        """Test that ISO format preserves timezone information."""
        from datetime import timezone

        dt = datetime(2024, 10, 12, 10, 0, 0, tzinfo=timezone.utc)
        iso_str = dt.isoformat()

        assert "+00:00" in iso_str or "Z" in iso_str

    def test_naive_datetime_comparison(self):
        """Test comparing naive datetime objects."""
        dt1 = datetime(2024, 10, 12, 10, 0, 0)
        dt2 = datetime(2024, 10, 12, 10, 0, 0)

        # Both naive - should compare fine
        assert dt1 == dt2
