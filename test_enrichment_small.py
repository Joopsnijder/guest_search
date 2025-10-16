#!/usr/bin/env python3
"""Quick test to verify candidate enrichment with just 2 candidates."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from guest_search.agent import GuestFinderAgent


def test_enrichment():
    """Test that report generation enriches candidates with detailed info."""
    print("🧪 Testing candidate enrichment (2 candidates only)\n")

    # Load existing candidates but only use first 2
    with open("data/candidates_latest.json") as f:
        all_candidates = json.load(f)

    # Use only first 2 for faster testing
    original_candidates = all_candidates[:2]

    print(f"📋 Testing with {len(original_candidates)} candidates\n")

    # Show original for first candidate
    first = original_candidates[0]
    print(f"BEFORE: {first['name']}")
    print(f"  Topics ({len(first.get('topics', []))}): {first.get('topics', [])}")
    print(f"  Relevance ({len(first.get('relevance_description', ''))} chars): {first.get('relevance_description', '')[:80]}...")
    print()

    # Initialize agent and inject candidates
    agent = GuestFinderAgent()
    agent.candidates = original_candidates.copy()

    print("🤖 Running report generation...\n")

    # Generate report
    try:
        report = agent.generate_report()

        if report and "Error" not in report:
            print("\n✅ Report generated successfully\n")

            # Check enrichment
            enriched = agent.candidates[0]
            print(f"AFTER: {enriched['name']}")
            print(f"  Topics ({len(enriched.get('topics', []))}): {enriched.get('topics', [])}")
            print(f"  Relevance ({len(enriched.get('relevance_description', ''))} chars):")
            print(f"    {enriched.get('relevance_description', '')}")
            print()

            # Verify enrichment worked
            orig_count = len(first.get('topics', []))
            enrich_count = len(enriched.get('topics', []))

            if enrich_count >= 4 and enrich_count > orig_count:
                print("✅ SUCCESS: Candidates were enriched!")
            elif len(enriched.get('relevance_description', '')) > len(first.get('relevance_description', '')):
                print("✅ SUCCESS: Relevance description was enriched!")
            else:
                print("⚠️  Enrichment may not have worked as expected")

        else:
            print(f"❌ Report generation failed: {report}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_enrichment()
