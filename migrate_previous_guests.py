#!/usr/bin/env python3
"""
Migrate previous_guests.json to new enriched data structure.

Old structure:
{
  "name": "...",
  "why_now": "Short description",
  ...
}

New structure:
{
  "name": "...",
  "topics": ["topic1", "topic2", ...],
  "relevance_description": "Detailed 3-5 sentence description",
  ...
}
"""

import json
from pathlib import Path


def migrate_guest(guest: dict) -> dict:
    """Migrate a single guest to new structure."""

    # If already has topics and relevance_description, skip
    if "topics" in guest and "relevance_description" in guest:
        return guest

    # Extract from why_now if available
    why_now = guest.get("why_now", "")

    # Create basic topics from role/organization
    topics = []
    role = guest.get("role", "")

    # Add generic topics based on role
    if "AI" in role or "AI" in guest.get("organization", ""):
        topics.append("AI")

    if why_now:
        # Try to extract topics from why_now
        if "AI Act" in why_now or "regelgeving" in why_now:
            topics.append("AI Act")
            topics.append("regelgeving")
        if "privacy" in why_now.lower():
            topics.append("privacy")
        if "ethiek" in why_now.lower() or "ethics" in why_now.lower():
            topics.append("ethiek")

    # Default topics if none found
    if not topics:
        topics = ["AI", "technologie"]

    # Use why_now as relevance_description, or create one
    relevance_description = why_now if why_now else f"{role} bij {guest.get('organization', '')}"

    # Update guest with new fields
    guest["topics"] = topics
    guest["relevance_description"] = relevance_description

    # Keep why_now for backward compatibility
    # (it will be ignored by Trello if topics/relevance exist)

    return guest


def main():
    """Migrate previous_guests.json to new structure."""

    previous_guests_file = Path("data/previous_guests.json")

    if not previous_guests_file.exists():
        print(f"❌ File not found: {previous_guests_file}")
        return

    # Load existing data
    with open(previous_guests_file, encoding="utf-8") as f:
        guests = json.load(f)

    print(f"📋 Loaded {len(guests)} guests from {previous_guests_file}")

    # Migrate each guest
    migrated_count = 0
    for guest in guests:
        old_has_topics = "topics" in guest
        guest = migrate_guest(guest)
        if not old_has_topics and "topics" in guest:
            migrated_count += 1

    print(f"✨ Migrated {migrated_count} guests to new structure")

    # Save migrated data
    with open(previous_guests_file, "w", encoding="utf-8") as f:
        json.dump(guests, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved migrated data to {previous_guests_file}")
    print(f"💾 Backup available at: {previous_guests_file}.backup")

    # Show example
    if guests:
        print("\n📝 Example migrated guest:")
        example = guests[0]
        print(f"  Name: {example.get('name')}")
        print(f"  Topics: {example.get('topics', [])}")
        print(f"  Relevance: {example.get('relevance_description', '')[:80]}...")


if __name__ == "__main__":
    main()
