"""Test script to see what fetch_page_content actually returns"""

import requests
from bs4 import BeautifulSoup

# URL from the last successful run
# url = "https://www.edbalphen.nl/nieuws/start-nieuwe-hbo-opleiding-toegepaste-ai-in-alphen-aan-den-rijn"
url = "https://www.wur.nl/nl/nieuws/nieuwe-bsc-data-science-for-global-challenges-ai-en-datawetenschap-voor-een-betere-wereld.htm"

try:
    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
    )

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        # Show first 2000 chars
        print("=" * 80)
        print(f"URL: {url}")
        print("=" * 80)
        print(text[:2000])
        print("=" * 80)
        print(f"\nTotal length: {len(text)} characters")

        # Look for common name patterns
        print("\n" + "=" * 80)
        print("Searching for name patterns...")
        print("=" * 80)

        import re

        # Look for "volgens [Name]", "door [Name]", etc.
        patterns = [
            r"volgens\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"door\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"Prof\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"Dr\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+),\s+(hoogleraar|professor|docent|onderzoeker)",
        ]

        found_names = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    found_names.add(match[0])
                else:
                    found_names.add(match)

        if found_names:
            print(f"Found {len(found_names)} potential names:")
            for name in sorted(found_names):
                print(f"  - {name}")
        else:
            print("No names found with standard patterns")
            print("\nFirst 500 chars to inspect manually:")
            print(text[:500])

except Exception as e:
    print(f"Error: {e}")
