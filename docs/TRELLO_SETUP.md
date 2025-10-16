# Trello Integratie Setup

## Stap 1: Verkrijg je Trello API Key en Token

1. **API Key verkrijgen:**
   - Ga naar: https://trello.com/app-key
   - Log in met je Trello account
   - Kopieer de "Key" (dit is je `TRELLO_API_KEY`)

2. **Token verkrijgen:**
   - Op dezelfde pagina, klik op de link "Token" (linksboven)
   - Of ga direct naar: https://trello.com/1/authorize?expiration=never&name=GuestSearch&scope=read,write&response_type=token&key=YOUR_API_KEY
     (vervang YOUR_API_KEY met je API key)
   - Klik op "Allow" om de app toegang te geven
   - Kopieer de gegenereerde token (dit is je `TRELLO_TOKEN`)

## Stap 2: Voeg credentials toe aan .env

Open je `.env` bestand en voeg toe:

```bash
TRELLO_API_KEY=jouw_api_key_hier
TRELLO_TOKEN=jouw_token_hier
```

## Stap 3: Zorg dat je Trello board klaar is

De integratie verwacht:
- Een board genaamd: **"AIToday Live"**
- Een lijst in dat board genaamd: **"Spot"**

Als je andere namen wilt gebruiken, pas dan de code aan in `interactive_selector.py`.

## Gebruik

Na het draaien van de agent:

```bash
# Voer de agent uit
python guest_search.py

# Selecteer en stuur gasten naar Trello
python select_guests.py
```

De interactive selector laat je:
- Alle nieuwe en recente gasten zien in een mooie terminal UI
- Individuele gasten selecteren om naar Trello te sturen
- Alle nieuwe gasten in één keer naar Trello sturen
- Zien of een kaart al bestaat (duplicaat detectie)

## Trello Kaart Format

Elke kaart bevat:
- **Naam**: Alleen de naam van de gast
- **Beschrijving**:
  - Rol en organisatie
  - Mogelijke onderwerpen
  - Waarom interessant
  - Bronnen met links
  - Contactinfo (indien beschikbaar)
  - Datum aanbevolen
