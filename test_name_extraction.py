"""Test the enhanced fetch_page_content name extraction"""

from src.guest_search.agent import GuestFinderAgent

# Initialize agent (we just need the tool handler)
agent = GuestFinderAgent()

# Test with the WUR page that contains "Lukasz Grus"
test_url = "https://www.wur.nl/nl/nieuws/nieuwe-bsc-data-science-for-global-challenges-ai-en-datawetenschap-voor-een-betere-wereld.htm"

print("=" * 80)
print(f"Testing name extraction on: {test_url}")
print("=" * 80)

result = agent._handle_tool_call("fetch_page_content", {"url": test_url})

if result["status"] == "success":
    print(f"\n✓ Fetch successful!")
    print(f"✓ Content length: {len(result['content'])} chars")
    print(f"✓ Persons found: {result['persons_found']}")

    if result["potential_persons"]:
        print(f"\n{'=' * 80}")
        print("EXTRACTED PERSONS:")
        print('=' * 80)

        for i, person in enumerate(result["potential_persons"], 1):
            print(f"\n{i}. {person['name']}")
            print(f"   Context: {person['context']}")
            if "title_match" in person:
                print(f"   Title: {person['title_match']}")
    else:
        print("\n⚠️  No persons extracted")
        print("First 500 chars of content:")
        print(result["content"][:500])
else:
    print(f"\n❌ Fetch failed: {result.get('error')}")

# Test with another URL
print("\n" + "=" * 80)
test_url2 = "https://www.edbalphen.nl/nieuws/start-nieuwe-hbo-opleiding-toegepaste-ai-in-alphen-aan-den-rijn"
print(f"Testing name extraction on: {test_url2}")
print("=" * 80)

result2 = agent._handle_tool_call("fetch_page_content", {"url": test_url2})

if result2["status"] == "success":
    print(f"\n✓ Fetch successful!")
    print(f"✓ Persons found: {result2['persons_found']}")

    if result2["potential_persons"]:
        print(f"\nEXTRACTED PERSONS:")
        for i, person in enumerate(result2["potential_persons"], 1):
            print(f"{i}. {person['name']}")
    else:
        print("⚠️  No persons found (expected - this page has no names)")
else:
    print(f"\n❌ Fetch failed: {result2.get('error')}")
