# Troubleshooting Guide

## Probleem: Geen Gasten Gevonden

### Symptomen
- Agent voert alle zoekopdrachten uit
- Search results worden gevonden en gecached
- Maar aan het einde: 0 kandidaten opgeslagen
- Rapport is leeg

### Root Cause Analyse

#### 1. Lege Snippets (Meest Voorkomend)

**Probleem**: Search provider geeft results zonder snippets terug.

**Detectie**:
```bash
# Check search cache
cat data/cache/search_results.json | grep -c '"snippet": ""'
```

Als dit aantal hoog is (>50%), dan heb je waarschijnlijk dit probleem.

**Impact**:
- Agent heeft geen context om relevantie te beoordelen
- Kan geen persoonsnamen of expertise herkennen
- Kan geen verificatie doen met meerdere bronnen

**Oplossing**:
1. Check welke provider gebruikt wordt (zie logs)
2. Switch naar provider met betere snippet quality:
   - ✅ **Serper** - Beste kwaliteit (aanbevolen)
   - ✅ **Brave** - Goede kwaliteit
   - ⚠️ **SearXNG** - Variable kwaliteit
   - ❌ **Ollama** - Vaak lege snippets (disabled by default)
   - ⚠️ **Google Scraper** - Laatste redmiddel

**Preventie**:
- Gebruik Serper als primary provider (is nu default)
- Zorg dat SERPER_API_KEY in .env staat

#### 2. Rate Limits op Alle Providers

**Probleem**: Alle providers zijn rate limited.

**Detectie**:
```bash
# Check logs voor rate limit warnings
grep "rate limit" output/logs/latest.log
```

**Oplossing**:
1. Wacht tot rate limits verlopen (meestal 1 uur)
2. Check API quota's:
   - Serper: 2,500 free searches/month
   - Brave: Check je plan
3. Voeg meer providers toe via .env

#### 3. Te Weinig Bronnen per Kandidaat

**Symptoom**: Agent vindt wel personen maar slaat ze niet op.

**Check**:
```python
# In config.py
MIN_SOURCES_PER_CANDIDATE = 2  # Moet minimaal 2 zijn
```

**Oplossing**:
- Verlaag MIN_SOURCES_PER_CANDIDATE naar 1 (voor testing)
- Of: verbeter search queries om meer resultaten per persoon te vinden

#### 4. Previous Guests Filter Te Streng

**Symptoom**: Agent vindt kandidaten maar markeert ze als "recent aanbevolen".

**Check**:
```python
# In config.py
EXCLUDE_WEEKS = 8  # Gasten binnen 8 weken worden geskipped
```

**Debug**:
```bash
# Check previous guests file
cat data/previous_guests.json
```

**Oplossing**:
- Clear previous_guests.json voor testing
- Of: verlaag EXCLUDE_WEEKS naar 0

## Debug Workflow

### Stap 1: Check Search Quality

```bash
# Analyze cached results
cat data/cache/search_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for key, entry in list(data.items())[:3]:
    results = entry['results']
    empty = sum(1 for r in results if not r.get('snippet', '').strip())
    print(f'Query: {entry[\"query\"][:50]}')
    print(f'Empty snippets: {empty}/{len(results)}\\n')
"
```

### Stap 2: Check Provider Status

```python
from src.guest_search.agent import GuestFinderAgent

agent = GuestFinderAgent()
status = agent.smart_search.get_status()

print(f"Providers: {status['providers']}")
print(f"Rate limited: {status['rate_limited_providers']}")
```

### Stap 3: Check Configuration

```python
from src.guest_search.config import Config

print(f"Min sources: {Config.MIN_SOURCES_PER_CANDIDATE}")
print(f"Exclude weeks: {Config.EXCLUDE_WEEKS}")
print(f"Target candidates: {Config.TARGET_CANDIDATES}")
```

### Stap 4: Manual Test Search

```python
from src.guest_search.smart_search_tool import SmartSearchTool

tool = SmartSearchTool(enable_cache=False)
result = tool.search("AI expert Netherlands 2025")

print(f"Provider: {result['provider']}")
print(f"Results: {len(result['results'])}")

# Check first result
if result['results']:
    first = result['results'][0]
    print(f"\\nFirst result:")
    print(f"  Title: {first['title']}")
    print(f"  Snippet: {first['snippet'][:100]}")
```

## Quick Fixes

### Fix 1: Clear Bad Cache

```bash
rm data/cache/search_results.json
```

### Fix 2: Switch to Serper

```bash
# In .env
SERPER_API_KEY=your_key_here
```

### Fix 3: Relax Filters (Testing Only)

```python
# In config.py
MIN_SOURCES_PER_CANDIDATE = 1  # Was 2
EXCLUDE_WEEKS = 0  # Was 8
```

### Fix 4: Enable Debug Logging

```python
# In smart_search_tool.py
logging.basicConfig(level=logging.DEBUG)  # Was INFO
```

## Prevention Checklist

✅ Use Serper as primary provider (now default)
✅ Monitor cache for empty snippets
✅ Set up rate limit alerts
✅ Keep API keys valid and within quota
✅ Test with single query before full run
✅ Clear cache between major runs

## Common Error Messages

### "⚠️ Geen kandidaten gevonden"

**Betekent**: Agent heeft wel gezocht maar niemand voldeed aan criteria.

**Check**:
1. Snippets (zijn ze leeg?)
2. Search queries (zijn ze specifiek genoeg?)
3. Filters (zijn ze te streng?)

### "⏭️ Skipping Provider (rate limited)"

**Betekent**: Provider hit rate limit en wordt geskipped.

**Actie**: Normaal gedrag, systeem valt terug op volgende provider.

### "Cache hit for query"

**Betekent**: Result komt uit cache (kan oud zijn).

**Actie**: Clear cache als je fresh results wilt.

## Contact

Als bovenstaande oplossingen niet werken:
1. Check logs in `output/logs/`
2. Run met `pytest` om systeem te testen
3. Review `data/cache/search_results.json` voor data quality issues
