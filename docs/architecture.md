# Guest Search - Architectuur Documentatie (arc42)

## 1. Introductie en Doelen

### 1.1 Doel van het Systeem
Een geautomatiseerde AI-agent die wekelijks zoekt naar relevante Nederlandse AI-experts als potentiële gasten voor de podcast AIToday Live.

### 1.2 Stakeholders

| Stakeholder | Verwachtingen |
|------------|---------------|
| Podcast producers | Wekelijks actuele gastenlijst met diverse AI-experts |
| Redactie | Geverifieerde kandidaten met meerdere bronnen |
| Eindgebruikers | Betrouwbare en relevante gastvoorstellen |

## 2. Randvoorwaarden

### 2.1 Technische Randvoorwaarden
- Python 3.10+
- Claude Sonnet 4 API (Anthropic)
- Multiple search providers (Serper/SearXNG/Brave/Google scraper)
- Lokale file-based storage

### 2.2 Organisatorische Randvoorwaarden
- Wekelijkse uitvoering
- Exclusie window: 8 weken
- Target: 8 kandidaten per week
- Nederlandse focus

## 3. Context en Scope

```mermaid
graph LR
    U[Gebruiker] -->|Start cyclus| GF[Guest Finder Agent]
    GF -->|API calls| CA[Claude API]
    GF -->|Search queries| SP[Search Providers]
    SP -->|Resultaten| GF
    GF -->|Leest/schrijft| FS[(File Storage)]
    GF -->|Rapport| U

    SP --> S1[Serper]
    SP --> S2[SearXNG]
    SP --> S3[Brave]
    SP --> S4[Google Scraper]

    FS --> F1[previous_guests.json]
    FS --> F2[search_cache.json]
    FS --> F3[reports/*.md]
```

## 4. Oplossingstrategie

### 4.1 Kernprincipes
1. **Multi-phase approach**: Planning → Zoeken → Rapporteren
2. **AI-driven**: Claude agent met extended thinking voor strategische beslissingen
3. **Search resilience**: Automatic fallback tussen meerdere search providers
4. **Caching**: 1-dag cache om rate limits te beheersen
5. **Verificatie**: Minimaal 2 bronnen per kandidaat

### 4.2 Technologie Keuzes
- **Anthropic Claude**: Extended thinking voor planning en strategie
- **Smart Search Tool**: Multi-provider fallback systeem
- **File-based storage**: Simpel, geen database overhead

## 5. Bouwstenen (Building Blocks)

```mermaid
graph TD
    subgraph "Guest Finder Agent"
        M[main.py] --> GFA[GuestFinderAgent]
        GFA --> P1[Planning Phase]
        GFA --> P2[Search Phase]
        GFA --> P3[Report Phase]
    end

    subgraph "Core Components"
        GFA --> C[Config]
        GFA --> T[Tools]
        GFA --> PR[Prompts]
        GFA --> SST[SmartSearchTool]
    end

    subgraph "Search Providers"
        SST --> Cache[SearchResultCache]
        SST --> SP1[OllamaProvider]
        SST --> SP2[SerperProvider]
        SST --> SP3[SearXNGProvider]
        SST --> SP4[BraveProvider]
        SST --> SP5[GoogleScraperProvider]
    end

    subgraph "Storage"
        GFA --> PG[(previous_guests.json)]
        SST --> SC[(search_cache.json)]
        P3 --> RP[(reports/*.md)]
    end
```

### 5.1 Component Beschrijvingen

| Component | Verantwoordelijkheid |
|-----------|---------------------|
| **GuestFinderAgent** | Orkestreert de 3 fases, beheert conversatie met Claude |
| **SmartSearchTool** | Intelligente search met automatic fallback |
| **SearchResultCache** | 1-dag caching van zoekresultaten |
| **SearchProviders** | Abstractie laag voor verschillende search APIs |
| **Tools** | Agent tool definitions (web_search, check_previous_guests, save_candidate) |
| **Prompts** | Gestructureerde prompts voor elke fase |
| **Config** | Centrale configuratie (API keys, thresholds) |

## 6. Runtime View

### 6.1 Volledige Cyclus

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant C as Claude API
    participant S as SmartSearch
    participant FS as File Storage

    U->>A: run_full_cycle()

    rect rgb(200, 220, 240)
        Note over A,C: FASE 1: Planning
        A->>C: Planning prompt + extended thinking
        C->>A: Search strategy JSON
        A->>A: Parse strategy
    end

    rect rgb(220, 240, 200)
        Note over A,S: FASE 2: Zoeken (iteratief)
        loop Voor elke query (max 12)
            A->>C: Execute search query
            C->>A: web_search tool call
            A->>S: search(query)
            S->>S: Check cache
            alt Cache hit
                S->>A: Cached results
            else Cache miss
                S->>S: Try providers in order
                S->>A: Fresh results + cache
            end
            C->>A: check_previous_guests tool call
            A->>FS: Read previous_guests.json
            FS->>A: Guest history
            C->>A: save_candidate tool call
            A->>A: Add to candidates list
            alt Target bereikt
                A->>A: Break loop
            end
        end
    end

    rect rgb(240, 220, 200)
        Note over A,FS: FASE 3: Rapporteren
        A->>C: Generate report prompt
        C->>A: Markdown rapport
        A->>FS: Save report
        A->>FS: Update previous_guests.json
        A->>U: Rapport klaar
    end
```

### 6.2 Smart Search Fallback

```mermaid
sequenceDiagram
    participant A as Agent
    participant S as SmartSearch
    participant C as Cache
    participant P1 as Serper
    participant P2 as SearXNG
    participant P3 as Brave
    participant P4 as Scraper

    A->>S: search(query)
    S->>C: Check cache
    alt Cache hit
        C-->>S: Cached results
        S-->>A: Return results
    else Cache miss
        S->>P1: Try Serper
        alt Serper success
            P1-->>S: Results
            S->>C: Cache results
            S-->>A: Return results
        else Serper fail
            S->>P2: Try SearXNG
            alt SearXNG success
                P2-->>S: Results
                S->>C: Cache results
                S-->>A: Return results
            else SearXNG fail
                S->>P3: Try Brave
                alt Brave success
                    P3-->>S: Results
                    S->>C: Cache results
                    S-->>A: Return results
                else All API fail
                    S->>P4: Try Scraper
                    P4-->>S: Scraped results
                    S->>C: Cache results
                    S-->>A: Return results
                end
            end
        end
    end
```

## 7. Deployment View

```mermaid
graph TB
    subgraph "Development Machine"
        subgraph "Python Environment"
            M[main.py]
            P[guest_search package]
            V[.venv]
        end

        subgraph "Local Storage"
            D1[data/previous_guests.json]
            D2[data/cache/search_results.json]
            D3[output/reports/]
        end

        M --> P
        P --> D1
        P --> D2
        P --> D3
    end

    subgraph "External Services"
        E1[Claude API<br/>Anthropic]
        E2[Serper API]
        E3[SearXNG Public<br/>Instances]
        E4[Brave Search API]
    end

    P --> E1
    P --> E2
    P --> E3
    P --> E4
```

## 8. Crosscutting Concepts

### 8.1 Caching Strategie
- **Doel**: Rate limit beheersing en snellere tests
- **Duur**: 1 dag
- **Scope**: Query + provider agnostic
- **Location**: `data/cache/search_results.json`

### 8.2 Error Handling
- **Search fallback**: Automatisch naar volgende provider
- **SearXNG rotation**: Dynamic instance rotation bij failures
- **Graceful degradation**: Werkt door met minder resultaten

### 8.3 Configuratie
- **Centraal**: `config.py`
- **Environment**: API keys via `.env`
- **Versioned**: Thresholds en parameters in code

### 8.4 Testing
- **148 tests** over 8 risk areas
- **Mocking**: Responses library voor API calls
- **Freezegun**: Tijd-gerelateerde tests
- **Fixtures**: Herbruikbare test data

## 9. Architectuurbeslissingen

### ADR-001: Multi-Phase Agent Design
**Context**: Complex taak met verschillende cognitieve eisen

**Besluit**: Splits in 3 fases (planning, zoeken, rapporteren)

**Rationale**:
- Planning fase kan extended thinking gebruiken
- Zoek fase is iteratief en tool-heavy
- Rapport fase is output-focused

**Consequenties**: ✅ Duidelijke separation of concerns, ❌ Meer code complexity

### ADR-002: Smart Search met Fallback
**Context**: Rate limits en reliability issues bij search providers

**Besluit**: Multi-provider systeem met automatische fallback

**Rationale**:
- Geen vendor lock-in
- Resilience tegen rate limits
- Cost optimization (gratis tiers eerst)

**Consequenties**: ✅ High availability, ❌ Meer configuratie

### ADR-003: File-based Storage
**Context**: Simpele data persistence nodig

**Besluit**: JSON files in plaats van database

**Rationale**:
- Geen database overhead
- Makkelijk te inspecteren
- Git-friendly voor backups

**Consequenties**: ✅ Simpel, ✅ Geen setup, ❌ Geen concurrent access

### ADR-004: 1-Day Search Cache
**Context**: Herhaalde queries tijdens development/testing

**Besluit**: 1-dag cache voor search resultaten

**Rationale**:
- Rate limit bescherming
- Snellere tests
- Actueel genoeg voor gebruik

**Consequenties**: ✅ Sneller en goedkoper, ❌ Mogelijk verouderde data

## 10. Kwaliteitseisen

| Kwaliteit | Target | Huidige Status |
|-----------|--------|----------------|
| **Test Coverage** | >80% | ✅ 148 tests, 8 risk areas |
| **Availability** | >95% | ✅ Multi-provider fallback |
| **Response Time** | <2 min per query | ✅ Met caching |
| **Accuracy** | 2+ bronnen per kandidaat | ✅ Verificatie verplicht |
| **Freshness** | Max 14 dagen oud | ✅ Recent search focus |

## 11. Risico's en Technische Schuld

### Risico's
1. **Rate Limits**: Mitigatie via multi-provider + caching
2. **API Changes**: Providers kunnen API wijzigen → Tests detecteren dit
3. **Search Quality**: Google scraper kan breken → Niet primary provider

### Technische Schuld
1. **Async Support**: SmartSearch kan async worden voor parallelle queries
2. **Database**: Bij schaling naar team usage
3. **Monitoring**: Nog geen alerting op failures

## 12. Glossary

| Term | Definitie |
|------|-----------|
| **Agent** | Claude AI die autonome beslissingen neemt |
| **Tool** | Functie die agent kan aanroepen (web_search, etc.) |
| **Provider** | Externe search service (Serper, SearXNG, etc.) |
| **Extended Thinking** | Claude feature voor diep nadenken met thinking budget |
| **Candidate** | Potentiële podcast gast met verificatie |
| **Strategy** | JSON output van planning fase met queries |
