# Presentations

Marp presentations voor het Guest Search project.

## Structuur

```
presentations/
├── agent-functionality/       # Agent functionaliteit presentatie
│   ├── presentation.md        # Source (Marp + Mermaid)
│   ├── presentation.build.md  # Intermediate (Mermaid → SVG)
│   ├── presentation-final.html # HTML output
│   ├── presentation-final.pdf  # PDF output
│   └── diagrams/              # SVG diagram exports
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
# Agent functionality
./scripts/build-presentations.sh docs/presentations/agent-functionality/presentation.md

# Architecture
./scripts/build-presentations.sh docs/presentations/architecture/presentation.md
```

### Alle presentaties bouwen:

```bash
npm run build:presentations docs/presentations/agent-functionality/presentation.md
npm run build:presentations docs/presentations/architecture/presentation.md
```

## Presentaties

### 1. Agent Functionality (45 slides)
**Doel:** Uitleg over hoe de Guest Finder en Topic Researcher agents werken

**Inhoud:**
- System architecture overview
- Guest Finder workflow (3 phases)
- Topic Researcher workflow
- Smart Search tool (multi-provider fallback)
- Trello integration
- Interactive terminal UI
- Best practices

**Output:**
- [HTML](agent-functionality/presentation-final.html)
- [PDF](agent-functionality/presentation-final.pdf)

### 2. Architecture (arc42) (30 slides)
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
# HTML (in browser)
open docs/presentations/agent-functionality/presentation-final.html

# PDF
open docs/presentations/agent-functionality/presentation-final.pdf
```

### Nieuwe presentatie toevoegen:

1. Maak een nieuwe folder in `presentations/`
2. Maak `presentation.md` met Marp frontmatter
3. Gebruik Mermaid voor diagrams
4. Build met `./scripts/build-presentations.sh`
