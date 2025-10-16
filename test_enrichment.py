#!/usr/bin/env python3
"""Quick test to verify candidate enrichment during report generation."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from guest_search.agent import GuestFinderAgent


def test_enrichment():
    """Test that report generation enriches candidates with detailed info."""
    print("🧪 Testing candidate enrichment during report generation\n")

    # Load existing candidates
    with open("data/candidates_latest.json") as f:
        original_candidates = json.load(f)

    print(f"📋 Loaded {len(original_candidates)} candidates from candidates_latest.json\n")

    # Show original topics for first candidate
    if original_candidates:
        first = original_candidates[0]
        print(f"Original candidate: {first['name']}")
        print(f"  Topics: {first.get('topics', [])}")
        print(f"  Relevance (length): {len(first.get('relevance_description', ''))} chars")
        print()

    # Initialize agent and inject candidates (simulate search phase completion)
    agent = GuestFinderAgent()
    agent.candidates = original_candidates.copy()

    print("🤖 Running report generation (this will enrich candidates)...\n")

    # Generate report (this should enrich the candidates)
    try:
        report = agent.generate_report()

        if report:
            print("✅ Report generated successfully\n")

            # Check if candidates were enriched
            if agent.candidates:
                enriched = agent.candidates[0]
                print(f"Enriched candidate: {enriched['name']}")
                print(f"  Topics: {enriched.get('topics', [])}")
                print(
                    f"  Relevance (length): {len(enriched.get('relevance_description', ''))} chars"
                )
                print()

                # Compare
                orig_topics = original_candidates[0].get("topics", [])
                enrich_topics = enriched.get("topics", [])

                print("📊 Comparison:")
                print(f"  Original topics count: {len(orig_topics)}")
                print(f"  Enriched topics count: {len(enrich_topics)}")
                print(
                    f"  Original relevance length: {len(original_candidates[0].get('relevance_description', ''))}"
                )
                print(
                    f"  Enriched relevance length: {len(enriched.get('relevance_description', ''))}"
                )
                print()

                if len(enrich_topics) > len(orig_topics):
                    print("✅ SUCCESS: Topics were enriched!")
                    print("\nEnriched topics:")
                    for topic in enrich_topics:
                        print(f"  - {topic}")
                    print("\nEnriched relevance:")
                    print(f"  {enriched.get('relevance_description', '')}")
                else:
                    print("⚠️  WARNING: Topics don't appear to be enriched")
                    print("This might mean the agent didn't call enrich_candidate tool")

        else:
            print("❌ Report generation failed\n")

    except Exception as e:
        print(f"❌ Error during report generation: {e}\n")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_enrichment()
