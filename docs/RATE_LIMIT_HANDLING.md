# Rate Limit Handling in SmartSearchTool

## Overview

Het SmartSearchTool implementeert intelligente rate limit detectie en provider skipping. Wanneer een search provider een rate limit error teruggeeft (HTTP 402 of 429), wordt die provider automatisch geskipped voor de rest van de huidige sessie.

## Provider Priority Order

De tool gebruikt providers in deze volgorde voor optimale kwaliteit:

1. **Serper** (Primary)
   - Best quality results met rijke snippets
   - 2,500 gratis searches/maand
   - Vereist: `SERPER_API_KEY` in .env

2. **SearXNG** (Secondary)
   - Gratis en onbeperkt
   - Variable kwaliteit (afhankelijk van instance)
   - Geen API key nodig

3. **Brave** (Tertiary, Optioneel)
   - Goede kwaliteit met snippets
   - Vereist: `BRAVE_API_KEY` in .env
   - Alleen gebruikt als API key beschikbaar

4. **Google Scraper** (Last Resort)
   - Gratis maar onbetrouwbaar
   - Kan breken als Google HTML wijzigt
   - Rate limited door Google

**Note**: Ollama provider is standaard uitgeschakeld vanwege lege snippets.

## Voordelen

1. **Geen tijdverspilling**: Rate-limited providers worden direct overgeslagen
2. **Snellere fallback**: Directe switch naar volgende provider
3. **Betere logging**: Duidelijke feedback over welke providers beschikbaar zijn
4. **Session-based**: Rate limits resetten automatisch bij nieuwe run

## Technische Implementatie

### RateLimitError Exception

Een nieuwe custom exception wordt geraised door providers bij rate limits:

```python
class RateLimitError(Exception):
    """Raised when a provider hits rate limits"""
    pass
```

### Provider Changes

Alle API-based providers (Ollama, Serper, Brave) checken nu op 402/429 status codes:

```python
if response.status_code in (402, 429):
    logger.error(f"Provider API error: {response.status_code}")
    raise RateLimitError(f"Provider rate limit hit: {response.status_code}")
```

### SmartSearchTool Tracking

Het tool houdt een set bij van rate-limited providers:

```python
self.rate_limited_providers = set()  # Initialized in __init__
```

Bij elke search wordt gecheckt:

```python
# Skip rate-limited providers
if provider_name in self.rate_limited_providers:
    logger.info(f"⏭️  Skipping {provider_name} (rate limited during this session)")
    continue
```

Bij een `RateLimitError` wordt de provider toegevoegd aan de skip-list:

```python
except RateLimitError as e:
    self.rate_limited_providers.add(provider_name)
    logger.warning(f"⚠️  {provider_name} rate limited, skipping for rest of session: {e}")
    continue  # Try next provider
```

## Voorbeeld Output

### Zonder Rate Limit

```
🔍 Zoeken: Nederlandse bedrijven AI Act implementatie
INFO: Trying search with OllamaProvider
INFO: Ollama search succesvol: 10 resultaten
INFO: Success with OllamaProvider: 10 results
✓ 10 resultaten via OllamaProvider
```

### Met Rate Limit (Eerste keer)

```
🔍 Zoeken: Green AI sustainability Netherlands
INFO: Trying search with OllamaProvider
ERROR: Ollama API error: 402 - {"error": "you've reached your hourly usage limit"}
WARNING: ⚠️  OllamaProvider rate limited, skipping for rest of session
INFO: Trying search with SerperProvider
INFO: Serper search succesvol: 10 resultaten
INFO: Success with SerperProvider: 10 results
✓ 10 resultaten via SerperProvider
```

### Volgende Zoekopdrachten (Provider wordt geskipped)

```
🔍 Zoeken: Nederlandse ziekenhuizen AI implementatie
INFO: ⏭️  Skipping OllamaProvider (rate limited during this session)
INFO: Trying search with SerperProvider
INFO: Serper search succesvol: 10 resultaten
INFO: Success with SerperProvider: 10 results
✓ 10 resultaten via SerperProvider
```

## API

### Status Check

```python
tool = SmartSearchTool()
status = tool.get_status()

print(status['rate_limited_providers'])  # ['OllamaProvider']
```

### Rate Limits Resetten

```python
tool = SmartSearchTool()

# Do some searches...

# Reset for new session
tool.reset_rate_limits()
```

## Testing

Er zijn 11 nieuwe tests toegevoegd voor rate limit handling:

- ✅ RateLimitError wordt geraised op 402/429
- ✅ Rate-limited providers worden geskipped
- ✅ Fallback naar volgende provider werkt
- ✅ Status tracking werkt correct
- ✅ Reset functionaliteit werkt
- ✅ Alleen rate limit errors markeren provider (niet andere errors)

## Impact op Bestaande Code

**Breaking change**: Providers gooien nu `RateLimitError` in plaats van een lege lijst te returnen bij rate limits.

**Migration**: Tests die rate limit handling checken moeten worden aangepast:

```python
# Oud
results = provider.search("query")
assert results == []

# Nieuw
with pytest.raises(RateLimitError):
    provider.search("query")
```
