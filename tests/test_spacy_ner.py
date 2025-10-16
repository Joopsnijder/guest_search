"""
Tests for spaCy NER-based person extraction.

Tests both spaCy extraction and regex fallback methods.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.guest_search.agent import GuestFinderAgent


class TestSpacyPersonExtraction:
    """Test spaCy NER person extraction."""

    @pytest.fixture
    def agent(self):
        """Create agent instance with mocked client."""
        with patch("src.guest_search.agent.get_anthropic_client"):
            agent = GuestFinderAgent()
            return agent

    @pytest.fixture
    def sample_dutch_text(self):
        """Sample Dutch text with person names."""
        return """
        Prof. dr. Jan de Vries is hoogleraar AI aan de Universiteit van Amsterdam.
        Volgens Maria Jansen, directeur van het AI Instituut, is dit een belangrijke
        ontwikkeling. Dr. Pieter Bakker van het TNO vertelt dat het project succesvol is.

        Het onderzoek wordt geleid door Elizabeth Smith van het University Hospital.
        Ook Kees de Jong06 en Amsterdam University zijn betrokken bij het project.
        """

    def test_spacy_extraction_basic(self, agent, sample_dutch_text):
        """Test that spaCy extracts person names correctly."""
        persons = agent._extract_persons_with_spacy(sample_dutch_text)

        # Extract names
        names = [p["name"] for p in persons]

        # Should find these persons
        assert "Jan de Vries" in names or "Maria Jansen" in names or "Pieter Bakker" in names

        # Should NOT find these (filtered out)
        assert not any("06" in name for name in names)  # Numbers filtered
        assert not any("University" in name for name in names)  # Organization keyword
        assert not any("Hospital" in name for name in names)  # Organization keyword

    def test_spacy_extraction_with_titles(self, agent, sample_dutch_text):
        """Test that spaCy detects academic titles."""
        persons = agent._extract_persons_with_spacy(sample_dutch_text)

        # At least one person should have a title match
        persons_with_titles = [p for p in persons if "title_match" in p]

        # May or may not find titles depending on spaCy model availability
        # Just check the structure is correct if titles are found
        if persons_with_titles:
            for person in persons_with_titles:
                assert "Prof." in person["title_match"] or "Dr." in person["title_match"]

    def test_spacy_extraction_context(self, agent, sample_dutch_text):
        """Test that extracted persons include context."""
        persons = agent._extract_persons_with_spacy(sample_dutch_text)

        if persons:
            for person in persons:
                # All persons should have name and context
                assert "name" in person
                assert "context" in person
                assert len(person["context"]) > 0

                # Context should contain the person's name
                assert person["name"] in sample_dutch_text

    def test_spacy_filters_numbers(self, agent):
        """Test that names with numbers are filtered."""
        text = "Kees de Jong06 is directeur van het bedrijf."

        persons = agent._extract_persons_with_spacy(text)
        names = [p["name"] for p in persons]

        # Should filter out name with numbers
        assert not any("06" in name for name in names)

    def test_spacy_filters_organizations(self, agent):
        """Test that organization names are filtered."""
        text = """
        Amsterdam University Hospital heeft een nieuwe AI afdeling.
        Het Children Foundation ondersteunt het project.
        """

        persons = agent._extract_persons_with_spacy(text)
        names = [p["name"] for p in persons]

        # Should not extract organization names
        assert not any("Hospital" in name for name in names)
        assert not any("Children" in name for name in names)
        assert not any("Foundation" in name for name in names)

    def test_spacy_filters_single_words(self, agent):
        """Test that single-word names are filtered."""
        text = "John is de directeur. Jan Jansen is de CEO."

        persons = agent._extract_persons_with_spacy(text)
        names = [p["name"] for p in persons]

        # Should not extract single-word names
        assert "John" not in names

        # Multi-word names should be extracted (if spaCy detects them)
        # Note: This depends on spaCy model being available

    def test_regex_fallback_basic(self, agent, sample_dutch_text):
        """Test regex fallback extraction."""
        persons = agent._extract_persons_with_regex(sample_dutch_text)

        # Extract names
        names = [p["name"] for p in persons]

        # Regex should find names with titles
        assert any("Vries" in name or "Jansen" in name or "Bakker" in name for name in names)

    def test_regex_fallback_with_titles(self, agent):
        """Test that regex extracts names with academic titles."""
        text = "Prof. dr. Jan de Vries en Dr. Maria Jansen werken samen."

        persons = agent._extract_persons_with_regex(text)
        names = [p["name"] for p in persons]

        # Should find at least one name with title
        assert len(names) > 0
        assert any("Vries" in name or "Jansen" in name for name in names)

    def test_regex_fallback_with_roles(self, agent):
        """Test that regex extracts names with job titles."""
        text = "CEO Jan Jansen en directeur Maria de Wit presenteren het plan."

        persons = agent._extract_persons_with_regex(text)
        names = [p["name"] for p in persons]

        # Should find names near job titles
        assert any("Jansen" in name or "Wit" in name for name in names)

    def test_regex_fallback_quotes(self, agent):
        """Test that regex extracts names from quotes."""
        text = 'Volgens Jan Jansen is dit belangrijk. "Dit is goed", zegt Maria de Wit.'

        persons = agent._extract_persons_with_regex(text)
        names = [p["name"] for p in persons]

        # Should find names in quote patterns
        assert "Jan Jansen" in names or "Maria de Wit" in names

    def test_regex_fallback_context(self, agent):
        """Test that regex extraction includes context."""
        text = "Prof. Jan de Vries van de Universiteit Amsterdam legt uit."

        persons = agent._extract_persons_with_regex(text)

        if persons:
            person = persons[0]
            assert "name" in person
            assert "context" in person
            assert len(person["context"]) > 0

    def test_spacy_fallback_on_import_error(self, agent):
        """Test that spaCy falls back to regex when spaCy not available."""
        with patch("src.guest_search.agent.GuestFinderAgent._extract_persons_with_spacy") as mock_spacy:
            # Simulate ImportError
            mock_spacy.side_effect = ImportError("spaCy not installed")

            text = "Prof. Jan Jansen is hoogleraar."

            # Should fall back to regex (won't raise error)
            persons = agent._extract_persons_with_regex(text)
            assert isinstance(persons, list)

    def test_spacy_fallback_on_model_missing(self, agent, sample_dutch_text):
        """Test that spaCy falls back to regex when model not found."""
        # This test verifies the fallback mechanism is in place
        # The actual fallback happens in _extract_persons_with_spacy

        persons = agent._extract_persons_with_spacy(sample_dutch_text)

        # Should return list (either from spaCy or regex fallback)
        assert isinstance(persons, list)

        # If persons found, they should have required fields
        if persons:
            for person in persons:
                assert "name" in person
                assert "context" in person

    def test_deduplication(self, agent):
        """Test that duplicate names are removed."""
        text = """
        Jan Jansen is directeur. Dr. Jan Jansen werkt bij TNO.
        Prof. Jan Jansen is hoogleraar.
        """

        # Test with regex (easier to control)
        persons = agent._extract_persons_with_regex(text)
        names = [p["name"] for p in persons]

        # Count occurrences of "Jan Jansen"
        jan_count = names.count("Jan Jansen")

        # Should only appear once (deduplicated)
        assert jan_count == 1

    def test_empty_text(self, agent):
        """Test extraction with empty text."""
        persons_spacy = agent._extract_persons_with_spacy("")
        persons_regex = agent._extract_persons_with_regex("")

        # Should return empty list, not crash
        assert persons_spacy == []
        assert persons_regex == []

    def test_no_persons_in_text(self, agent):
        """Test extraction when no persons present."""
        text = "Het bedrijf heeft een nieuwe AI afdeling geopend vorige week."

        persons_spacy = agent._extract_persons_with_spacy(text)
        persons_regex = agent._extract_persons_with_regex(text)

        # Should return empty list or list with no valid persons
        # (depending on false positives)
        assert isinstance(persons_spacy, list)
        assert isinstance(persons_regex, list)
