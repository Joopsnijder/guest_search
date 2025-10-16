#!/usr/bin/env python3
"""Test LinkedIn enrichment functionality."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from guest_search.agent import GuestFinderAgent


def test_linkedin_enrichment():
    """Test that LinkedIn enrichment finds profiles for candidates."""
    print("🧪 Testing LinkedIn enrichment\n")

    # Load existing candidates
    with open("data/candidates_latest.json") as f:
        candidates = json.load(f)

    print(f"📋 Loaded {len(candidates)} candidates\n")

    # Show before
    print("BEFORE LinkedIn enrichment:")
    for i, candidate in enumerate(candidates[:2], 1):
        name = candidate.get("name")
        linkedin = candidate.get("contact_info", {}).get("linkedin", "")
        print(f"  {i}. {name}: {linkedin or '(geen LinkedIn)'}")

    # Initialize agent and inject candidates
    agent = GuestFinderAgent()
    agent.candidates = candidates.copy()

    print("\n🤖 Running LinkedIn enrichment...\n")

    # Run LinkedIn enrichment
    agent.enrich_linkedin_profiles()

    # Show after
    print("\nAFTER LinkedIn enrichment:")
    for i, candidate in enumerate(agent.candidates[:2], 1):
        name = candidate.get("name")
        linkedin = candidate.get("contact_info", {}).get("linkedin", "")
        print(f"  {i}. {name}:")
        print(f"      LinkedIn: {linkedin or '(niet gevonden)'}")

    # Count how many have LinkedIn
    with_linkedin = sum(
        1 for c in agent.candidates if c.get("contact_info", {}).get("linkedin")
    )

    print(f"\n📊 Resultaat: {with_linkedin}/{len(agent.candidates)} kandidaten met LinkedIn profiel")

    if with_linkedin > 0:
        print("\n✅ SUCCESS: LinkedIn enrichment werkt!")
    else:
        print("\n⚠️  WARNING: Geen LinkedIn profielen gevonden (mogelijk rate limit?)")


if __name__ == "__main__":
    test_linkedin_enrichment()
