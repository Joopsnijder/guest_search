"""
Test script to compare spaCy vs regex person extraction.
"""

import os
from src.guest_search.agent import GuestFinderAgent

# Enable debug mode to see extraction stats
os.environ["DEBUG_TOOLS"] = "1"

# Test URLs with known persons
test_urls = [
    # University press release
    "https://www.wur.nl/nl/nieuws/nieuwe-bsc-data-science-for-global-challenges-ai-en-datawetenschap-voor-een-betere-wereld.htm",
    # ICT news article
    "https://www.icthealth.nl/nieuws/ai-model-voorspelt-sepsis-bij-kinderen-tot-48-uur-voor-symptomen",
    # Tech interview
    "https://www.dutchitchannel.nl/interview/665567/jan-heijdra-cisco-ai-en-security-raken-verweven",
]


def test_person_extraction():
    """Test spaCy person extraction vs regex."""
    print("\n🧪 Testing spaCy Person Extraction\n")
    print("=" * 80)

    agent = GuestFinderAgent()

    for i, url in enumerate(test_urls, 1):
        print(f"\n\n📄 Test {i}/{len(test_urls)}")
        print(f"URL: {url}\n")

        # Call the fetch_page_content tool
        result = agent._handle_tool_call("fetch_page_content", {"url": url})

        if result.get("status") == "success":
            persons = result.get("potential_persons", [])
            print(f"\n✅ Extraction successful")
            print(f"   Persons found: {len(persons)}")

            if persons:
                print(f"\n   📋 Persons extracted:")
                for j, person in enumerate(persons[:5], 1):  # Show max 5
                    name = person.get("name", "Unknown")
                    context = person.get("context", "")[:100]
                    title = person.get("title_match", "")

                    print(f"\n   {j}. {name}")
                    if title:
                        print(f"      Title: {title}")
                    print(f"      Context: {context}...")
            else:
                print("   ⚠️  No persons extracted")
        else:
            print(f"   ❌ Error: {result.get('error')}")

        print("\n" + "-" * 80)

    print("\n\n✨ Test complete!")


if __name__ == "__main__":
    test_person_extraction()
