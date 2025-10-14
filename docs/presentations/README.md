# Presentations

Marp presentations voor het Guest Search project.

## Structuur

```
presentations/
├── templates/                 # 📐 Herbruikbare templates
│   ├── default-theme.md       # Standaard styling met adaptive layouts
│   └── README.md              # Template documentatie & best practices
│
├── guest-finder/              # Guest Finder Agent presentatie
│   ├── presentation.md        # Source (Marp + Mermaid)
│   ├── presentation.build.md  # Intermediate (Mermaid → SVG)
│   ├── presentation-final.html # HTML output
│   ├── presentation-final.pdf  # PDF output
│   └── diagrams/              # SVG diagram exports
│
├── topic-researcher/          # Topic Researcher Agent presentatie
│   ├── presentation.md        # Source (Marp + Mermaid)
│   ├── presentation.build.md  # Intermediate (Mermaid → SVG)
│   ├── presentation-final.html # HTML output
│   ├── presentation-final.pdf  # PDF output
│   └── diagrams/              # SVG diagram exports
│
├── agent-functionality/       # DEPRECATED: Oude gecombineerde presentatie
│   └── presentation.md        # Gebruik guest-finder + topic-researcher
│
└── architecture/              # Architectuur presentatie (arc42)
    ├── presentation.md        # Source (Marp + Mermaid)
    ├── presentation.build.md  # Intermediate (Mermaid → SVG)
    ├── presentation-final.html # HTML output
    ├── presentation-final.pdf  # PDF output
    └── diagrams/              # SVG diagram exports
```

## Bouwen

### Individuele presentatie bouwen:

```bash
# Guest Finder Agent
./scripts/build-presentations.sh docs/presentations/guest-finder/presentation.md

# Topic Researcher Agent
./scripts/build-presentations.sh docs/presentations/topic-researcher/presentation.md

# Architecture
./scripts/build-presentations.sh docs/presentations/architecture/presentation.md
```

### Alle agent presentaties bouwen:

```bash
./scripts/build-all-presentations.sh
```

Dit bouwt automatisch beide agent presentaties (Guest Finder + Topic Researcher).

## 📐 Template Systeem

**Herbruikbare styling voor consistente presentaties!**

### Adaptive Layouts

Het template systeem past zich automatisch aan aan de hoeveelheid content:

- **Normale slides** - Standaard layout voor 5-7 bullets
- **Compact mode** (`<!-- _class: compact -->`) - Voor content-heavy slides
- **Column layouts** - 2 of 3 kolommen voor parallelle info
- **Responsive diagrams** - Auto-schaling van Mermaid SVGs

### Quick Start

```markdown
---
marp: true
theme: default
# ... kopieer frontmatter van templates/default-theme.md
---

# Je Presentatie

## Normale Slide
- Bullet 1
- Bullet 2

---

<!-- _class: compact -->

## Compacte Slide met Veel Content
<div class="columns">

**Kolom 1:**
- Item 1
- Item 2

**Kolom 2:**
- Item 3
- Item 4

</div>
```

### Documentatie

Volledige template documentatie: [templates/README.md](templates/README.md)

Inclusief:
- Layout beslisboom (wanneer welke layout gebruiken)
- Voorbeelden van alle layout types
- Best practices voor content density
- Tips voor probleem oplossing

## Presentaties

### 1. 🔍 Guest Finder Agent (~35 slides)
**Doel:** Uitleg over hoe de Guest Finder Agent werkt

**Inhoud:**
- Strategic planning phase
- Multi-provider search system
- Deduplication tracking (12 weeks)
- Interactive selection UI
- Trello integration
- Smart Search tool
- 166 tests coverage

**Output:**
- [HTML](guest-finder/presentation-final.html)
- [PDF](guest-finder/presentation-final.pdf)

### 2. 📊 Topic Researcher Agent (~35 slides)
**Doel:** Uitleg over hoe de Topic Researcher Agent werkt

**Inhoud:**
- Target persona (Anne de Vries)
- Six topic categories
- Last month search timeframe
- Smart caching system
- Rich terminal rendering
- Integration with Guest Finder
- 15 tests coverage

**Output:**
- [HTML](topic-researcher/presentation-final.html)
- [PDF](topic-researcher/presentation-final.pdf)

### 3. 🏗️ Architecture (arc42) (~30 slides)
**Doel:** Technische architectuur documentatie volgens arc42 template

**Inhoud:**
- Context diagram
- Building blocks (components)
- Runtime view (sequence diagrams)
- Deployment view
- Quality requirements
- Technical debt
- Test coverage (181 tests)

**Output:**
- [HTML](architecture/presentation-final.html)
- [PDF](architecture/presentation-final.pdf)

### 4. 🔧 Tool Calling Explained (~43 slides)
**Doel:** Uitleg over hoe `_handle_tool_call()` werkt en de communicatie tussen LLM, prompts en tools

**Inhoud:**
- What is tool calling?
- Complete flow diagrams
- Tool definities (JSON schema)
- `_handle_tool_call()` deep dive
- Conversatie geschiedenis
- Agentic loop concept
- Real example walkthrough (8 stappen)
- Testing, debugging & best practices

**Output:**
- [HTML](tool-calling-explained/presentation-final.html)
- [PDF](tool-calling-explained/presentation-final.pdf)

## Diagram Conversie

Het build script converteert automatisch Mermaid diagrams naar SVG:

1. **Input**: `presentation.md` met Mermaid codeblocks
2. **Conversie**: Mermaid → SVG via `scripts/mermaid-to-images.js`
3. **Output**: SVG files in `diagrams/` directory
4. **Build**: Marp genereert HTML + PDF met embedded SVG's

## Vereisten

- Node.js
- `@marp-team/marp-core` (zie `package.json`)
- Marp CLI (`npm install -g @marp-team/marp-cli`)

## Tips

### Presentatie openen:

```bash
# Guest Finder Agent
open docs/presentations/guest-finder/presentation-final.html
open docs/presentations/guest-finder/presentation-final.pdf

# Topic Researcher Agent
open docs/presentations/topic-researcher/presentation-final.html
open docs/presentations/topic-researcher/presentation-final.pdf

# Architecture
open docs/presentations/architecture/presentation-final.html
open docs/presentations/architecture/presentation-final.pdf
```

### Nieuwe presentatie toevoegen:

1. Maak een nieuwe folder in `presentations/`
2. Maak `presentation.md` met Marp frontmatter
3. Gebruik Mermaid voor diagrams
4. Build met `./scripts/build-presentations.sh`
