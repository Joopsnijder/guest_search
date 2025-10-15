#!/usr/bin/env python3
"""
Quick test to verify agent behavior with fetch_page_content.
This runs a single query and monitors tool calls.
"""

import json
from src.guest_search.agent import GuestFinderAgent
from src.guest_search.config import Config

print("=== FETCH BEHAVIOR TEST ===\n")

# Create agent
agent = GuestFinderAgent()

# Override to do just 1 query for testing
original_max = Config.MAX_SEARCH_ITERATIONS
Config.MAX_SEARCH_ITERATIONS = 1

# Track tool calls
tool_calls = []
original_handle_tool = agent._handle_tool_call

def tracked_handle_tool(tool_name, tool_input, silent=False):
    tool_calls.append({
        "tool": tool_name,
        "input": tool_input if tool_name != "fetch_page_content" else {"url": tool_input.get("url", "?")}
    })
    print(f"🔧 Tool called: {tool_name}")
    if tool_name == "fetch_page_content":
        print(f"   URL: {tool_input.get('url', 'unknown')}")
    return original_handle_tool(tool_name, tool_input, silent)

agent._handle_tool_call = tracked_handle_tool

print("Running single query test...\n")

try:
    # Run just the planning and search phases
    strategy = agent.run_planning_phase()

    if strategy and "search_queries" in strategy:
        # Take first query
        first_query = strategy["search_queries"][0]
        print(f"\n📋 Testing query: {first_query['query'][:60]}...\n")

        # Run search phase with just this query
        agent.run_search_phase([first_query])

        print(f"\n=== RESULTS ===")
        print(f"Total tool calls: {len(tool_calls)}")
        print(f"web_search calls: {sum(1 for t in tool_calls if t['tool'] == 'web_search')}")
        print(f"fetch_page_content calls: {sum(1 for t in tool_calls if t['tool'] == 'fetch_page_content')}")
        print(f"save_candidate calls: {sum(1 for t in tool_calls if t['tool'] == 'save_candidate')}")
        print(f"Candidates found: {len(agent.candidates)}")

        fetch_count = sum(1 for t in tool_calls if t['tool'] == 'fetch_page_content')

        if fetch_count == 0:
            print("\n❌ PROBLEM: Agent did NOT call fetch_page_content!")
            print("   This confirms the agent is ignoring the instruction.")
        elif fetch_count < 2:
            print(f"\n⚠️  WARNING: Only {fetch_count} fetch call (should be 2-3)")
        else:
            print(f"\n✅ SUCCESS: Agent called fetch_page_content {fetch_count} times")

        # Show all tool calls
        print("\n=== TOOL CALL SEQUENCE ===")
        for i, call in enumerate(tool_calls, 1):
            print(f"{i}. {call['tool']}")
            if call['tool'] == 'fetch_page_content':
                print(f"   → {call['input']['url']}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Restore
    Config.MAX_SEARCH_ITERATIONS = original_max

print("\n=== END TEST ===")
