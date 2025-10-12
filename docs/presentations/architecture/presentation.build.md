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

**AI-driven podcast guest finder & topic researcher**

arc42 documentatie - Updated 2025

---

## 1. Introductie

### Doel
Geautomatiseerde content discovery voor AIToday Live podcast:
- Nederlandse AI-experts identificeren
- Interessante AI-topics ontdekken

### Stakeholders
- 🎙️ Podcast producers → Actuele gastenlijst + topiclijst
- ✍️ Redactie → Geverifieerde kandidaten en bronnen
- 👥 Eindgebruikers → Betrouwbare voorstellen

---

## 2. Context

<div style="text-align: center; margin: 10px auto;">
  <img src="diagrams/diagram-1.svg" alt="Diagram 1" style="max-width: 95%; height: auto; max-height: 350px; object-fit: contain;" />
</div>

---

## 3. Oplossingstrategie

### Kernprincipes
1. 🎯 **Multi-phase**: Planning → Zoeken → Rapporteren
2. 🧠 **AI-driven**: Claude Sonnet 4 met extended thinking
3. 🔄 **Resilient search**: Multi-provider fallback (4 providers)
4. 💾 **Smart caching**: 1-dag cache + duplicate detection
5. ✅ **Verificatie**: Min. 2 bronnen per item
6. 📊 **Two agents**: Separate guest & topic discovery
7. 📝 **Rich UI**: Beautiful markdown rendering in terminal

---

## 4. Building Blocks

<div style="text-align: center; margin: 10px auto;">
  <img src="diagrams/diagram-2.svg" alt="Diagram 2" style="max-width: 95%; height: auto; max-height: 350px; object-fit: contain;" />
</div>

---

## 5. Runtime: Volledige Cyclus

<div style="text-align: center; margin: 10px auto;">
  <img src="diagrams/diagram-3.svg" alt="Diagram 3" style="max-width: 95%; height: auto; max-height: 350px; object-fit: contain;" />
</div>

---

## 6. Smart Search Fallback

<div style="text-align: center; margin: 10px auto;">
  <img src="diagrams/diagram-4.svg" alt="Diagram 4" style="max-width: 95%; height: auto; max-height: 350px; object-fit: contain;" />
</div>

---

## 7. Deployment

<div style="text-align: center; margin: 10px auto;">
  <img src="diagrams/diagram-5.svg" alt="Diagram 5" style="max-width: 95%; height: auto; max-height: 350px; object-fit: contain;" />
</div>

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
| **Test Coverage** | >80% | ✅ 181 tests |
| **Availability** | >95% | ✅ Multi-provider |
| **Response Time** | <2 min | ✅ Met cache |
| **Accuracy** | 2+ bronnen | ✅ Verplicht |
| **Freshness Topics** | <1 maand | ✅ Recent focus |
| **Freshness Guests** | <12 weeks | ✅ Deduplication |

---

## 10. Component Overzicht

| Component | Verantwoordelijkheid |
|-----------|---------------------|
| **GuestFinderAgent** | Orkestratie gasten zoeken (3 fases) |
| **TopicFinderAgent** | Orkestratie topics zoeken |
| **SmartSearchTool** | Multi-provider search (gedeeld) |
| **InteractiveSelector** | Rich UI voor gast selectie |
| **TrelloManager** | Trello API integratie |
| **SearchResultCache** | 1-dag caching |
| **SearchProviders** | API abstractie (4 providers) |
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
- 🔗 LinkedIn profile search integration
- 📧 Automated outreach templates

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
