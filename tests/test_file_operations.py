"""Tests for file I/O operations and data persistence."""

import json
from unittest.mock import patch

import pytest


class TestPreviousGuestsFileOperations:
    """Test operations on previous_guests.json file."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_load_existing_previous_guests(
        self, mock_anthropic, mock_search_tool, previous_guests_file, monkeypatch
    ):
        """Test loading existing previous_guests.json file."""
        from src.guest_search.agent import GuestFinderAgent

        # Change to directory with previous_guests.json
        monkeypatch.chdir(previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        assert len(agent.previous_guests) == 2
        assert agent.previous_guests[0]["name"] == "Jan Jansen"
        assert agent.previous_guests[1]["name"] == "Marie van der Berg"

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_load_missing_previous_guests_file(
        self, mock_anthropic, mock_search_tool, temp_dir, monkeypatch
    ):
        """Test loading when previous_guests.json doesn't exist."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(temp_dir)

        agent = GuestFinderAgent()

        # Should return empty list when file doesn't exist
        assert agent.previous_guests == []

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_load_malformed_json_file(
        self, mock_anthropic, mock_search_tool, malformed_json_file, monkeypatch
    ):
        """Test handling of malformed JSON in previous_guests.json."""
        from src.guest_search.agent import GuestFinderAgent

        # Rename to previous_guests.json
        target = malformed_json_file.parent / "previous_guests.json"
        malformed_json_file.rename(target)

        monkeypatch.chdir(target.parent.parent)

        # Should handle gracefully
        with pytest.raises(json.JSONDecodeError):
            GuestFinderAgent()

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_save_previous_guests(
        self, mock_anthropic, mock_search_tool, empty_previous_guests_file, monkeypatch
    ):
        """Test saving previous_guests.json file."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(empty_previous_guests_file.parent.parent)

        agent = GuestFinderAgent()
        agent.previous_guests = [
            {
                "name": "New Guest",
                "date": "2024-10-12T10:00:00",
                "organization": "Test Org",
            }
        ]

        agent._save_previous_guests()

        # Verify file was written
        with open(empty_previous_guests_file, encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data) == 1
        assert saved_data[0]["name"] == "New Guest"

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_save_with_special_characters(
        self, mock_anthropic, mock_search_tool, empty_previous_guests_file, monkeypatch
    ):
        """Test saving previous_guests with special characters."""
        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(empty_previous_guests_file.parent.parent)

        agent = GuestFinderAgent()
        agent.previous_guests = [
            {
                "name": "François Müller",
                "date": "2024-10-12T10:00:00",
                "organization": "Café & Co",
            }
        ]

        agent._save_previous_guests()

        # Verify Unicode handling
        with open(empty_previous_guests_file, encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data[0]["name"] == "François Müller"
        assert "Café" in saved_data[0]["organization"]


class TestReportFileOperations:
    """Test report file generation and saving."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_report_file_creation(
        self,
        mock_anthropic,
        mock_search_tool,
        mock_output_dir,
        sample_candidates,
        monkeypatch,
        mock_env_vars,
    ):
        """Test that report files are created correctly."""
        from unittest.mock import MagicMock

        from src.guest_search.agent import GuestFinderAgent

        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="# Test Report")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        monkeypatch.chdir(mock_output_dir.parent.parent)

        agent = GuestFinderAgent()
        agent.candidates = sample_candidates

        report = agent.generate_report()

        # Verify report was generated
        assert "Test Report" in report

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_report_filename_format(
        self, mock_anthropic, mock_search_tool, temp_dir, sample_candidates, monkeypatch
    ):
        """Test that report filenames follow expected format."""
        from unittest.mock import MagicMock

        from src.guest_search.agent import GuestFinderAgent

        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="# Report")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Create output directory
        output_dir = temp_dir / "output" / "reports"
        output_dir.mkdir(parents=True)

        monkeypatch.chdir(temp_dir)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        agent = GuestFinderAgent()
        agent.candidates = sample_candidates

        with patch("src.guest_search.agent.datetime") as mock_datetime:
            mock_datetime.now.return_value.isocalendar.return_value = (2024, 42, 1)
            mock_datetime.now.return_value.strftime.return_value = "20241012"
            mock_datetime.now.return_value.isoformat.return_value = "2024-10-12T10:00:00"

            agent.generate_report()

        # Check file exists with expected name pattern
        report_files = list(output_dir.glob("week_*.md"))
        assert len(report_files) > 0
        assert "week_42" in report_files[0].name


class TestCacheFileOperations:
    """Test cache file operations."""

    def test_cache_file_creation(self, mock_data_dir):
        """Test that cache files are created properly."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "cache" / "test_cache.json"
        cache = SearchResultCache(cache_file=str(cache_file))

        # Add some data
        cache.cache_results("test query", "TestProvider", [{"title": "Test"}])

        # Verify file exists and is valid JSON
        assert cache_file.exists()

        with open(cache_file) as f:
            data = json.load(f)

        assert len(data) > 0

    def test_cache_file_corruption_handling(self, mock_data_dir):
        """Test handling of corrupted cache files."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "cache" / "corrupted.json"
        cache_file.write_text("{invalid json content")

        # Should handle gracefully and start with empty cache
        cache = SearchResultCache(cache_file=str(cache_file))
        assert cache.cache_data == {}

    def test_concurrent_cache_access(self, mock_data_dir):
        """Test that cache handles concurrent access safely."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "cache" / "concurrent.json"

        cache1 = SearchResultCache(cache_file=str(cache_file))
        cache2 = SearchResultCache(cache_file=str(cache_file))

        # Both write to cache
        cache1.cache_results("query1", "Provider1", [{"title": "Result1"}])
        cache2.cache_results("query2", "Provider2", [{"title": "Result2"}])

        # Reload and verify
        cache3 = SearchResultCache(cache_file=str(cache_file))
        # At least one should have persisted (last writer wins)
        assert len(cache3.cache_data) >= 1

    def test_cache_directory_creation(self, temp_dir):
        """Test that cache directory is created if it doesn't exist."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache_file = temp_dir / "new_cache_dir" / "cache.json"

        # Directory doesn't exist yet
        assert not cache_file.parent.exists()

        SearchResultCache(cache_file=str(cache_file))

        # Directory should now exist
        assert cache_file.parent.exists()


class TestFilePermissions:
    """Test file permission handling."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_read_only_file_handling(
        self, mock_anthropic, mock_search_tool, previous_guests_file, monkeypatch
    ):
        """Test handling of read-only files."""
        from src.guest_search.agent import GuestFinderAgent

        # Make file read-only
        previous_guests_file.chmod(0o444)

        monkeypatch.chdir(previous_guests_file.parent.parent)

        agent = GuestFinderAgent()

        # Should be able to read
        assert len(agent.previous_guests) > 0

        # Writing should fail gracefully
        agent.previous_guests.append(
            {
                "name": "New Guest",
                "date": "2024-10-12T10:00:00",
                "organization": "Test",
            }
        )

        with pytest.raises(PermissionError):
            agent._save_previous_guests()

        # Cleanup
        previous_guests_file.chmod(0o644)

    def test_invalid_file_path_handling(self):
        """Test handling of invalid file paths."""
        from src.guest_search.smart_search_tool import SearchResultCache

        # Path with invalid characters or non-existent parent
        invalid_path = "/nonexistent/directory/cache.json"

        with pytest.raises((OSError, PermissionError)):
            cache = SearchResultCache(cache_file=invalid_path)
            cache.cache_results("test", "TestProvider", [])


class TestDataIntegrity:
    """Test data integrity across save/load cycles."""

    @patch("src.guest_search.agent.SmartSearchTool")
    @patch("src.guest_search.agent.Anthropic")
    def test_roundtrip_data_integrity(
        self, mock_anthropic, mock_search_tool, empty_previous_guests_file, monkeypatch
    ):
        """Test that data remains intact through save/load cycle."""
        from datetime import datetime

        from src.guest_search.agent import GuestFinderAgent

        monkeypatch.chdir(empty_previous_guests_file.parent.parent)

        original_data = [
            {
                "name": "Test Guest 1",
                "date": datetime.now().isoformat(),
                "organization": "Org 1",
            },
            {
                "name": "Test Guest 2",
                "date": datetime.now().isoformat(),
                "organization": "Org 2",
            },
        ]

        # Save data
        agent1 = GuestFinderAgent()
        agent1.previous_guests = original_data
        agent1._save_previous_guests()

        # Load data in new instance
        agent2 = GuestFinderAgent()

        # Verify data integrity
        assert len(agent2.previous_guests) == len(original_data)
        assert agent2.previous_guests[0]["name"] == original_data[0]["name"]
        assert agent2.previous_guests[1]["organization"] == original_data[1]["organization"]

    def test_cache_data_integrity(self, mock_data_dir, mock_search_results):
        """Test cache data integrity across save/load cycles."""
        from src.guest_search.smart_search_tool import SearchResultCache

        cache_file = mock_data_dir / "cache" / "integrity_test.json"

        # Save data
        cache1 = SearchResultCache(cache_file=str(cache_file))
        cache1.cache_results("test query", "TestProvider", mock_search_results)

        # Load data
        cache2 = SearchResultCache(cache_file=str(cache_file))
        retrieved = cache2.get_cached_results("test query", "TestProvider")

        # Verify integrity
        assert retrieved is not None
        assert len(retrieved) == len(mock_search_results)
        assert retrieved[0]["title"] == mock_search_results[0]["title"]
        assert retrieved[0]["link"] == mock_search_results[0]["link"]
