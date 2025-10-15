"""Quick test to see if agent saves candidates now"""

from src.guest_search.agent import GuestFinderAgent
from src.guest_search.config import Config
import os

os.environ["DEBUG_TOOLS"] = "1"

agent = GuestFinderAgent()

# Very targeted strategy with just 1 query
strategy = {
    "week_focus": "Test",
    "search_queries": [
        {
            "query": "Lukasz Grus WUR data science",
            "rationale": "Test",
            "priority": "high",
        }
    ],
}

print("Running single query test...")
Config.MAX_SEARCH_ITERATIONS = 1  # Only 1 query
Config.TARGET_CANDIDATES = 1  # Stop after 1 candidate

agent.run_search_phase(strategy)

print(f"\n{'='*80}")
print(f"RESULT: {len(agent.candidates)} candidates saved")
print('='*80)

if agent.candidates:
    for c in agent.candidates:
        print(f"\n✓ {c['name']}")
        print(f"  Role: {c.get('role')}")
        print(f"  Org: {c.get('organization')}")
else:
    print("\n❌ No candidates saved!")
    print(f"Debug: {len(agent.current_session_queries)} queries executed")
    if agent.current_session_queries:
        q = agent.current_session_queries[0]
        print(f"  Sources fetched: {len(q['successful_sources'])}")
