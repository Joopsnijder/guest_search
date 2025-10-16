#!/usr/bin/env python3
"""
Enrich previous_guests.json with data from candidates_latest.json.

For guests that appear in both files, copy the enriched topics and
relevance_description from candidates_latest.json to previous_guests.json.

This ensures Trello cards get the rich, detailed content.
"""

import json
from pathlib import Path
from datetime import datetime


def find_candidate_by_name(name: str, candidates: list) -> dict | None:
    """Find a candidate by exact name match."""
    for candidate in candidates:
        if candidate.get("name") == name:
            return candidate
    return None


def enrich_guest(guest: dict, candidate: dict | None) -> dict:
    """Enrich a guest with data from matching candidate."""

    if not candidate:
        # No matching candidate - keep existing data or use basic migration
        if "topics" not in guest or not guest["topics"]:
            # Add basic topics from why_now
            why_now = guest.get("why_now", "")
            topics = []

            if "AI Act" in why_now or "regelgeving" in why_now:
                topics.extend(["AI Act", "regelgeving"])
            if "privacy" in why_now.lower():
                topics.append("privacy")
            if "ethiek" in why_now.lower():
                topics.append("AI ethiek")

            if not topics:
                topics = ["AI", "technologie"]

            guest["topics"] = topics

        if "relevance_description" not in guest or not guest["relevance_description"]:
            guest["relevance_description"] = guest.get("why_now", "")

        return guest

    # Found matching candidate - use enriched data!
    print(f"  ✨ Enriching: {guest['name']}")

    # Copy enriched topics (4-5 specific topics)
    if "topics" in candidate and candidate["topics"]:
        guest["topics"] = candidate["topics"]

    # Copy enriched relevance description (detailed 3-5 sentences)
    if "relevance_description" in candidate and candidate["relevance_description"]:
        guest["relevance_description"] = candidate["relevance_description"]

    # Copy sources (should be URL strings)
    if "sources" in candidate and candidate["sources"]:
        # Convert to old format if needed (list of dicts with url/title/date)
        enriched_sources = []
        for source in candidate["sources"]:
            if isinstance(source, str):
                # String URL - convert to dict format
                enriched_sources.append({
                    "url": source,
                    "title": source,
                    "date": ""
                })
            elif isinstance(source, dict):
                enriched_sources.append(source)

        guest["sources"] = enriched_sources

    # Keep existing fields (date, name, organization, role)
    # Update role if candidate has more specific role
    if "role" in candidate and candidate["role"] and len(candidate["role"]) > len(guest.get("role", "")):
        guest["role"] = candidate["role"]

    # Update organization if needed
    if "organization" in candidate and candidate["organization"]:
        guest["organization"] = candidate["organization"]

    return guest


def main():
    """Enrich previous_guests.json with data from candidates_latest.json."""

    previous_guests_file = Path("data/previous_guests.json")
    candidates_file = Path("data/candidates_latest.json")

    if not previous_guests_file.exists():
        print(f"❌ File not found: {previous_guests_file}")
        return

    if not candidates_file.exists():
        print(f"❌ File not found: {candidates_file}")
        return

    # Load data
    with open(previous_guests_file, encoding="utf-8") as f:
        guests = json.load(f)

    with open(candidates_file, encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"📋 Loaded {len(guests)} guests from previous_guests.json")
    print(f"📋 Loaded {len(candidates)} candidates from candidates_latest.json")
    print()

    # Enrich each guest
    enriched_count = 0
    for guest in guests:
        name = guest.get("name")
        candidate = find_candidate_by_name(name, candidates)

        old_topics_count = len(guest.get("topics", []))
        old_relevance_len = len(guest.get("relevance_description", ""))

        guest = enrich_guest(guest, candidate)

        new_topics_count = len(guest.get("topics", []))
        new_relevance_len = len(guest.get("relevance_description", ""))

        if candidate and (new_topics_count > old_topics_count or new_relevance_len > old_relevance_len):
            enriched_count += 1

    print()
    print(f"✨ Enriched {enriched_count} guests with detailed candidate data")

    # Save enriched data
    with open(previous_guests_file, "w", encoding="utf-8") as f:
        json.dump(guests, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved enriched data to {previous_guests_file}")

    # Show example of enriched guest
    for guest in guests:
        if find_candidate_by_name(guest["name"], candidates):
            print(f"\n📝 Example enriched guest: {guest['name']}")
            print(f"  Topics ({len(guest.get('topics', []))}): ")
            for topic in guest.get("topics", [])[:3]:
                print(f"    - {topic}")
            if len(guest.get("topics", [])) > 3:
                print(f"    ... and {len(guest.get('topics', [])) - 3} more")
            print(f"  Relevance ({len(guest.get('relevance_description', ''))} chars):")
            print(f"    {guest.get('relevance_description', '')[:150]}...")
            print(f"  Sources: {len(guest.get('sources', []))} URLs")
            break


if __name__ == "__main__":
    main()
