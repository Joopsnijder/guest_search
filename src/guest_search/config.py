import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL = "claude-sonnet-4-20250514"

    # Planning fase
    PLANNING_MAX_TOKENS = 12000  # Must be > thinking budget
    PLANNING_THINKING_BUDGET = 8000

    # Zoek fase
    SEARCH_MAX_TOKENS = 8000
    MAX_SEARCH_ITERATIONS = 12
    TARGET_CANDIDATES = 8

    # Filtering
    EXCLUDE_WEEKS = 8
    MIN_SOURCES_PER_CANDIDATE = 2

    # Tijdzone
    TIMEZONE = "Europe/Berlin"
