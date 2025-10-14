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
- Portkey AI Gateway (optioneel - voor observability)
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
    GF -->|API calls| PK{Portkey Gateway<br/>optioneel}
    PK -->|Routes to| CA[Claude API]
    PK -.->|Logs metrics| PD[(Portkey Dashboard)]
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
- **Portkey AI Gateway**: Optionele observability laag voor monitoring en cost tracking
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
        GFA --> PC[PortkeyClient<br/>Adapter]
        PC --> C[Config]
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
| **PortkeyClient** | Adapter voor Anthropic SDK met optionele Portkey observability |
| **SmartSearchTool** | Intelligente search met automatic fallback |
| **SearchResultCache** | 1-dag caching van zoekresultaten |
| **SearchProviders** | Abstractie laag voor verschillende search APIs |
| **Tools** | Agent tool definitions (web_search, check_previous_guests, save_candidate) |
| **Prompts** | Gestructureerde prompts voor elke fase |
| **Config** | Centrale configuratie (API keys, thresholds) |

## 6. Runtime View

### 6.1 Portkey Observability Layer (Optioneel)

```mermaid
sequenceDiagram
    participant A as Agent
    participant PA as PortkeyAdapter
    participant PG as Portkey Gateway
    participant C as Claude API
    participant PD as Portkey Dashboard

    A->>PA: messages.create() [Anthropic format]
    Note over PA: Convert Anthropic → OpenAI format
    PA->>PG: chat.completions.create() [OpenAI format]
    PG->>PD: Log request metadata
    Note over PG: Route to provider
    PG->>C: messages API call
    C->>PG: Response
    PG->>PD: Log response + tokens + cost
    Note over PA: Convert OpenAI → Anthropic format
    PA->>A: Message response [Anthropic format]
```

**Adapter Werking:**

- Agent code blijft ongewijzigd (Anthropic SDK)
- Adapter converteert formats transparant
- Portkey logt alle metrics automatisch
- Fallback naar direct Anthropic als Portkey niet geconfigureerd

### 6.2 Volledige Cyclus

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
        E0[Portkey Gateway<br/>optioneel]
        E1[Claude API<br/>Anthropic]
        E2[Serper API]
        E3[SearXNG Public<br/>Instances]
        E4[Brave Search API]
    end

    P -.->|via Portkey| E0
    E0 -.-> E1
    P -->|direct fallback| E1
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

- **157 tests** over 9 risk areas (incl. Portkey adapter)
- **Mocking**: Responses library voor API calls
- **Freezegun**: Tijd-gerelateerde tests
- **Fixtures**: Herbruikbare test data

### 8.5 Observability (Optioneel)

- **Portkey Dashboard**: Real-time monitoring van API calls
- **Metrics**: Token usage, costs, latency, error rates
- **Adapter Pattern**: Transparante integratie zonder code wijzigingen
- **Backwards Compatible**: Werkt met/zonder Portkey configuratie

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

### ADR-005: Portkey Observability via Adapter Pattern

**Context**: Behoefte aan monitoring van API usage, costs en performance zonder bestaande code te wijzigen

**Besluit**: Implementeer Portkey via adapter pattern die Anthropic SDK interface behoudt

**Rationale**:

- **Portkey Model Catalog** vereist OpenAI format, maar onze agents gebruiken Anthropic format
- **Adapter pattern** converteert formats transparant zonder code wijzigingen
- **Backwards compatible**: Werkt met/zonder Portkey configuratie
- **Optional feature**: Toggle via environment variables

**Alternatieven overwogen**:

1. ❌ Hele codebase herschrijven naar OpenAI format → Te veel werk, niet backwards compatible
2. ❌ Direct Anthropic SDK met custom base_url → Werkt niet met nieuwe Model Catalog
3. ✅ Adapter pattern → Zero code changes, optioneel, backwards compatible

**Conversies die de adapter doet**:

- Message content blocks: Anthropic `[{type: "text", text: "..."}]` → OpenAI `"..."`
- Tool definitions: `input_schema` → `parameters`
- Tool results: `tool_result` role → `tool` role
- Empty content filtering voor OpenAI compliance

**Consequenties**:

- ✅ Zero wijzigingen aan agent code
- ✅ Real-time monitoring van costs en performance
- ✅ Kan eenvoudig uitgeschakeld worden
- ❌ Extra conversie laag (minimale performance impact)
- ❌ Afhankelijkheid van portkey-ai package (optioneel)

**Implementatie**: `src/utils/portkey_client.py` met 157 tests

## 10. Kwaliteitseisen

| Kwaliteit | Target | Huidige Status |
|-----------|--------|----------------|
| **Test Coverage** | >80% | ✅ 157 tests, 9 risk areas |
| **Availability** | >95% | ✅ Multi-provider fallback |
| **Response Time** | <2 min per query | ✅ Met caching |
| **Accuracy** | 2+ bronnen per kandidaat | ✅ Verificatie verplicht |
| **Freshness** | Max 14 dagen oud | ✅ Recent search focus |
| **Observability** | Real-time monitoring | ✅ Optioneel via Portkey |

## 11. Risico's en Technische Schuld

### Risico's
1. **Rate Limits**: Mitigatie via multi-provider + caching
2. **API Changes**: Providers kunnen API wijzigen → Tests detecteren dit
3. **Search Quality**: Google scraper kan breken → Niet primary provider

### Technische Schuld

1. **Async Support**: SmartSearch kan async worden voor parallelle queries
2. **Database**: Bij schaling naar team usage
3. **Portkey Alerting**: Dashboard heeft metrics maar nog geen automated alerting

## 12. Glossary

| Term | Definitie |
|------|-----------|
| **Agent** | Claude AI die autonome beslissingen neemt |
| **Tool** | Functie die agent kan aanroepen (web_search, etc.) |
| **Provider** | Externe search service (Serper, SearXNG, etc.) |
| **Extended Thinking** | Claude feature voor diep nadenken met thinking budget |
| **Candidate** | Potentiële podcast gast met verificatie |
| **Strategy** | JSON output van planning fase met queries |
| **Adapter** | Wrapper pattern voor format conversie tussen APIs |
| **Portkey** | AI Gateway voor observability en monitoring |
| **Model Catalog** | Portkey's gecentraliseerde provider management systeem |
