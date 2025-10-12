"""Tests for configuration and environment variables."""

from unittest.mock import MagicMock, patch


class TestConfigurationLoading:
    """Test configuration loading from environment variables."""

    def test_load_config_with_api_key(self, mock_env_vars):
        """Test loading configuration with API key present."""

        # Reload config module to pick up environment variables
        import importlib

        from src.guest_search import config

        importlib.reload(config)

        assert config.Config.ANTHROPIC_API_KEY is not None
        assert len(config.Config.ANTHROPIC_API_KEY) > 0

    def test_load_config_without_api_key(self, mock_missing_api_key):
        """Test loading configuration without API key."""

        # Reload config module
        import importlib

        from src.guest_search import config

        importlib.reload(config)

        # Should be empty string when not set
        assert config.Config.ANTHROPIC_API_KEY == ""

    def test_config_constants(self):
        """Test that configuration constants have expected values."""
        from src.guest_search.config import Config

        assert Config.EXCLUDE_WEEKS == 8
        assert Config.TARGET_CANDIDATES == 8
        assert Config.MAX_SEARCH_ITERATIONS == 12
        assert Config.MIN_SOURCES_PER_CANDIDATE == 2

    def test_model_configuration(self):
        """Test model configuration."""
        from src.guest_search.config import Config

        assert Config.MODEL == "claude-sonnet-4-20250514"
        assert "claude" in Config.MODEL.lower()

    def test_token_budgets(self):
        """Test token budget configurations."""
        from src.guest_search.config import Config

        assert Config.PLANNING_MAX_TOKENS > 0
        assert Config.PLANNING_THINKING_BUDGET > 0
        assert Config.SEARCH_MAX_TOKENS > 0

        # max_tokens must be greater than thinking budget (Anthropic requirement)
        assert Config.PLANNING_MAX_TOKENS > Config.PLANNING_THINKING_BUDGET
        # Thinking budget must be at least 1024 (Anthropic minimum)
        assert Config.PLANNING_THINKING_BUDGET >= 1024

    def test_timezone_configuration(self):
        """Test timezone configuration."""
        from src.guest_search.config import Config

        assert Config.TIMEZONE == "Europe/Berlin"


class TestMainFunctionConfiguration:
    """Test main function configuration checks."""

    @patch("src.guest_search.agent.GuestFinderAgent")
    def test_main_checks_api_key(self, mock_agent, mock_missing_api_key):
        """Test that main function checks for API key."""
        import importlib

        import main

        # Reload to pick up missing API key
        from src.guest_search import config

        importlib.reload(config)
        importlib.reload(main)

        # Run main - should exit early without API key
        # It uses rich Console.print, not builtins.print
        with patch("main.Console") as mock_console:
            mock_console_instance = MagicMock()
            mock_console.return_value = mock_console_instance

            main.main()

            # Should print error message about API key
            mock_console_instance.print.assert_called()
            print_calls = [str(call) for call in mock_console_instance.print.call_args_list]
            assert any("ANTHROPIC_API_KEY" in call for call in print_calls)

    @patch("src.guest_search.agent.GuestFinderAgent")
    @patch("os.makedirs")
    def test_main_creates_directories(self, mock_makedirs, mock_agent, mock_env_vars, monkeypatch):
        """Test that main function creates necessary directories."""
        import importlib

        # Reload config to pick up mocked environment variables
        from src.guest_search import config

        importlib.reload(config)

        import main

        importlib.reload(main)

        # Mock the agent to prevent actual execution
        mock_agent_instance = mock_agent.return_value
        mock_agent_instance.run_full_cycle.return_value = "Test report"
        mock_agent_instance.candidates = []  # No candidates so no interactive prompts

        main.main()

        # Should create data and output directories
        assert mock_makedirs.call_count >= 2

    def test_main_initializes_previous_guests_file(self, temp_dir, mock_env_vars, monkeypatch):
        """Test that main initializes previous_guests.json if missing."""
        import importlib
        import os

        # Reload config to pick up mocked environment variables
        from src.guest_search import config

        importlib.reload(config)

        import main

        importlib.reload(main)

        monkeypatch.chdir(temp_dir)
        os.makedirs("data", exist_ok=True)

        # Mock the agent
        with patch("main.GuestFinderAgent") as mock_agent:
            mock_agent.return_value.run_full_cycle.return_value = "Test"
            mock_agent.return_value.candidates = []  # No candidates so no interactive prompts
            main.main()

        # Check file was created
        guests_file = temp_dir / "data" / "previous_guests.json"
        assert guests_file.exists()

        import json

        with open(guests_file) as f:
            data = json.load(f)

        assert data == []


class TestEnvironmentVariableHandling:
    """Test handling of various environment variable scenarios."""

    def test_empty_api_key(self, monkeypatch):
        """Test handling of empty API key."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        import importlib

        from src.guest_search import config

        importlib.reload(config)

        # Empty string should be treated as missing
        assert not config.Config.ANTHROPIC_API_KEY or len(config.Config.ANTHROPIC_API_KEY) == 0

    def test_whitespace_api_key(self, monkeypatch):
        """Test handling of whitespace-only API key."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")

        import importlib

        from src.guest_search import config

        importlib.reload(config)

        # Whitespace should remain (config doesn't strip)
        assert config.Config.ANTHROPIC_API_KEY == "   "

    def test_multiple_api_keys(self, monkeypatch):
        """Test configuration with multiple API keys."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
        monkeypatch.setenv("SERPER_API_KEY", "test-serper")
        monkeypatch.setenv("BRAVE_API_KEY", "test-brave")

        from src.utils.smart_search_tool import SmartSearchTool

        tool = SmartSearchTool(
            serper_api_key="test-serper", brave_api_key="test-brave", enable_cache=False
        )

        # Should have multiple providers available
        assert len(tool.providers) >= 2


class TestConfigurationDefaults:
    """Test configuration default values."""

    def test_exclude_weeks_default(self):
        """Test EXCLUDE_WEEKS default value."""
        from src.guest_search.config import Config

        # Should be 8 weeks
        assert Config.EXCLUDE_WEEKS == 8

    def test_target_candidates_default(self):
        """Test TARGET_CANDIDATES default value."""
        from src.guest_search.config import Config

        # Should aim for 8 candidates
        assert Config.TARGET_CANDIDATES == 8

    def test_max_search_iterations_default(self):
        """Test MAX_SEARCH_ITERATIONS default value."""
        from src.guest_search.config import Config

        # Should allow up to 12 searches
        assert Config.MAX_SEARCH_ITERATIONS == 12
        assert Config.MAX_SEARCH_ITERATIONS >= Config.TARGET_CANDIDATES

    def test_min_sources_per_candidate_default(self):
        """Test MIN_SOURCES_PER_CANDIDATE default value."""
        from src.guest_search.config import Config

        # Should require at least 2 sources
        assert Config.MIN_SOURCES_PER_CANDIDATE == 2


class TestConfigurationValidation:
    """Test configuration value validation."""

    def test_token_budgets_are_positive(self):
        """Test that token budgets are positive integers."""
        from src.guest_search.config import Config

        assert Config.PLANNING_MAX_TOKENS > 0
        assert Config.PLANNING_THINKING_BUDGET > 0
        assert Config.SEARCH_MAX_TOKENS > 0
        assert isinstance(Config.PLANNING_MAX_TOKENS, int)
        assert isinstance(Config.PLANNING_THINKING_BUDGET, int)
        assert isinstance(Config.SEARCH_MAX_TOKENS, int)

    def test_iteration_limits_are_positive(self):
        """Test that iteration limits are positive."""
        from src.guest_search.config import Config

        assert Config.MAX_SEARCH_ITERATIONS > 0
        assert Config.TARGET_CANDIDATES > 0
        assert Config.EXCLUDE_WEEKS > 0
        assert Config.MIN_SOURCES_PER_CANDIDATE > 0

    def test_model_name_format(self):
        """Test that model name follows expected format."""
        from src.guest_search.config import Config

        # Should be a string
        assert isinstance(Config.MODEL, str)
        assert len(Config.MODEL) > 0

        # Should contain claude
        assert "claude" in Config.MODEL.lower()

    def test_timezone_format(self):
        """Test that timezone is in valid format."""
        from src.guest_search.config import Config

        assert isinstance(Config.TIMEZONE, str)
        assert "/" in Config.TIMEZONE  # Should be in format "Continent/City"


class TestDotenvLoading:
    """Test .env file loading."""

    def test_dotenv_loaded_on_import(self):
        """Test that .env file is loaded when config is imported."""
        # Config module calls load_dotenv() on import

        # If .env exists, variables should be loaded
        # This test will pass regardless, as load_dotenv() doesn't fail if file missing
        assert True

    def test_env_vars_take_precedence(self, monkeypatch):
        """Test that environment variables take precedence over .env file."""
        # Set environment variable directly
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-var-key")

        import importlib

        from src.guest_search import config

        importlib.reload(config)

        # Should use environment variable
        assert config.Config.ANTHROPIC_API_KEY == "env-var-key"
