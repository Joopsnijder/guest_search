"""Test a single query to see if the agent now finds candidates"""

import os
from src.guest_search.agent import GuestFinderAgent
from src.guest_search.config import Config

# Ensure we have API key
if not Config.ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found")
    exit(1)

# Initialize agent
agent = GuestFinderAgent()

print("=" * 80)
print("TESTING SINGLE QUERY WITH NAME EXTRACTION")
print("=" * 80)

# Create a simple strategy with ONE query that we know has names
strategy = {
    "week_focus": "Test name extraction fix",
    "sectors_to_prioritize": ["onderwijs"],
    "topics_to_cover": ["AI education"],
    "search_queries": [
        {
            "query": "WUR nieuws data science Lukasz Grus",
            "rationale": "Direct test - we KNOW this person exists on WUR website",
            "priority": "high",
        }
    ],
}

print(f"\nQuery: {strategy['search_queries'][0]['query']}")
print(f"Rationale: {strategy['search_queries'][0]['rationale']}")
print("\n" + "=" * 80)
print("EXECUTING SEARCH...")
print("=" * 80 + "\n")

# Run search phase
agent.run_search_phase(strategy)

print("\n" + "=" * 80)
print(f"RESULTS: {len(agent.candidates)} candidates found")
print("=" * 80)

if agent.candidates:
    print("\nCANDIDATES:")
    for i, candidate in enumerate(agent.candidates, 1):
        print(f"\n{i}. {candidate['name']}")
        print(f"   Role: {candidate.get('role', 'N/A')}")
        print(f"   Organization: {candidate.get('organization', 'N/A')}")
        print(f"   Topics: {', '.join(candidate.get('topics', []))}")
        if "why_now" in candidate:
            print(f"   Why now: {candidate['why_now']}")
else:
    print("\n⚠️  No candidates found")
    print("\nDEBUG: Check if fetch_page_content was called:")
    print(f"Session queries: {len(agent.current_session_queries)}")
    if agent.current_session_queries:
        for q in agent.current_session_queries:
            print(f"  - Query: {q['query'][:60]}...")
            print(f"    Sources: {q['successful_sources']}")
            print(f"    Candidates found: {q['candidates_found']}")
