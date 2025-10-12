---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-size: 24px;
  }
  .mermaid {
    max-height: 500px;
    max-width: 100%;
  }
  .mermaid svg {
    max-height: 500px;
    max-width: 100%;
    height: auto;
  }
  ul {
    font-size: 0.9em;
  }
---

# Guest Search - Architectuur

**AI-driven podcast guest finder**

arc42 documentatie

---

## 1. Introductie

### Doel
Geautomatiseerde wekelijkse zoektocht naar Nederlandse AI-experts voor AIToday Live podcast

### Stakeholders
- 🎙️ Podcast producers → Actuele gastenlijst
- ✍️ Redactie → Geverifieerde kandidaten
- 👥 Eindgebruikers → Betrouwbare voorstellen

---

## 2. Context

```mermaid
graph LR
    U[Gebruiker] -->|Start| GF[Guest Finder<br/>Agent]
    GF -->|API calls| CA[Claude API]
    GF -->|Queries| SP[Search<br/>Providers]
    SP -->|Resultaten| GF
    GF -->|R/W| FS[(File<br/>Storage)]
    GF -->|Rapport| U

    SP --> S1[Serper]
    SP --> S2[SearXNG]
    SP --> S3[Brave]
    SP --> S4[Google]
```

---

## 3. Oplossingstrategie

### Kernprincipes
1. 🎯 **Multi-phase**: Planning → Zoeken → Rapporteren
2. 🧠 **AI-driven**: Claude met extended thinking
3. 🔄 **Resilient search**: Multi-provider fallback
4. 💾 **Caching**: 1-dag cache voor rate limits
5. ✅ **Verificatie**: Min. 2 bronnen per kandidaat

---

## 4. Building Blocks

```mermaid
graph TD
    subgraph "Agent"
        M[main.py] --> GFA[GuestFinderAgent]
        GFA --> P1[Planning]
        GFA --> P2[Search]
        GFA --> P3[Report]
    end

    subgraph "Components"
        GFA --> SST[SmartSearchTool]
        SST --> Cache
        SST --> Providers
    end

    subgraph "Storage"
        GFA --> PG[(previous<br/>guests)]
        Cache --> SC[(search<br/>cache)]
        P3 --> RP[(reports)]
    end
```

---

## 5. Runtime: Volledige Cyclus

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant C as Claude
    participant S as Search

    U->>A: run_full_cycle()

    rect rgb(200, 220, 240)
    Note over A,C: FASE 1: Planning
    A->>C: Strategy prompt
    C->>A: Search queries JSON
    end

    rect rgb(220, 240, 200)
    Note over A,S: FASE 2: Zoeken
    loop Max 12 queries
        A->>C: Execute query
        C->>S: web_search
        S->>A: Results (cached?)
        C->>A: save_candidate
    end
    end

    rect rgb(240, 220, 200)
    Note over A,U: FASE 3: Rapport
    A->>C: Generate report
    C->>U: Markdown rapport
    end
```

---

## 6. Smart Search Fallback

```mermaid
sequenceDiagram
    participant A as Agent
    participant S as SmartSearch
    participant C as Cache
    participant P as Providers

    A->>S: search(query)
    S->>C: Check cache

    alt Cache hit
        C-->>A: Return cached
    else Try providers
        S->>P: 1. Serper
        alt Success
            P-->>S: Results
            S->>C: Cache
        else Fail
            S->>P: 2. SearXNG
            alt Success
                P-->>S: Results
            else Fail
                S->>P: 3. Brave → 4. Scraper
            end
        end
    end
```

---

## 7. Deployment

```mermaid
graph TB
    subgraph "Local Machine"
        M[main.py]
        P[guest_search]
        D[(data/)]
    end

    subgraph "External APIs"
        E1[Claude API]
        E2[Serper]
        E3[SearXNG]
        E4[Brave]
    end

    P --> E1
    P --> E2
    P --> E3
    P --> E4
```

**Deployment**: Python app met lokale storage

---

## 8. Architectuurbeslissingen

### ADR-001: Multi-Phase Design
✅ Scheiding planning/zoeken/rapporteren
✅ Extended thinking voor strategie

### ADR-002: Smart Search Fallback
✅ Geen vendor lock-in
✅ Resilience tegen rate limits

### ADR-003: File-based Storage
✅ Simpel, geen database overhead
✅ Git-friendly

---

## 9. Kwaliteitseisen

| Kwaliteit | Target | Status |
|-----------|--------|--------|
| **Test Coverage** | >80% | ✅ 148 tests |
| **Availability** | >95% | ✅ Multi-provider |
| **Response Time** | <2 min | ✅ Met cache |
| **Accuracy** | 2+ bronnen | ✅ Verplicht |
| **Freshness** | <14 dagen | ✅ Recent focus |

---

## 10. Component Overzicht

| Component | Verantwoordelijkheid |
|-----------|---------------------|
| **GuestFinderAgent** | Orkestratie 3 fases |
| **SmartSearchTool** | Multi-provider search |
| **SearchResultCache** | 1-dag caching |
| **SearchProviders** | API abstractie |
| **Tools** | Agent capabilities |
| **Prompts** | Fase-specifieke prompts |

---

## 11. Risico's & Mitigaties

### Risico's
1. ⚠️ **Rate Limits** → Multi-provider + caching
2. ⚠️ **API Changes** → Tests detecteren dit
3. ⚠️ **Search Quality** → Scraper als fallback

### Technische Schuld
- 🔄 Async support voor parallelle queries
- 📊 Database voor team usage
- 🔔 Monitoring/alerting

---

## Samenvatting

### Architectuur Highlights
- 🎯 3-fase AI agent (planning/search/report)
- 🔄 Resilient multi-provider search
- 💾 Smart caching strategie
- ✅ 148 tests, 8 risk areas
- 📦 Simpel file-based storage

### Stack
Python 3.10+ | Claude Sonnet 4 | Serper/SearXNG/Brave/Scraper

---

# Vragen?

📖 Volledige documentatie: `docs/architecture.md`
🧪 Tests: `pytest`
🔧 Config: `.env` + `config.py`
