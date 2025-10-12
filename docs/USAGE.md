# Usage Guide

Complete guide to using the Guest Search and Topic Researcher tools.

## Table of Contents

- [Guest Finder](#guest-finder)
- [Topic Researcher](#topic-researcher)
- [Markdown Report Viewing](#markdown-report-viewing)
- [Interactive Guest Selection](#interactive-guest-selection)
- [Trello Integration](#trello-integration)

---

## Guest Finder

Find potential podcast guests using AI-powered search and analysis.

### Basic Usage

```bash
python main.py
```

### Workflow

1. **Planning Phase** (Fase 1)
   - AI analyzes current AI trends in Netherlands
   - Creates strategic search queries
   - Identifies sectors and topics to prioritize
   - Output: Compact table with strategy summary

2. **Search Phase** (Fase 2)
   - Executes search queries with progress bar
   - Shows current query and candidate count
   - Fetches full page content to find actual people
   - Uses smart_search with multi-provider fallback
   - Output: Clean progress bar, no verbose logs

3. **Report Generation** (Fase 3)
   - Generates markdown report with all candidates
   - Includes recent guests from last 2 weeks
   - Saves to `output/reports/week_X_YYYYMMDD.md`
   - Updates `data/previous_guests.json` for deduplication

4. **Report Preview** (Optional)
   - Prompts: "Wil je het rapport nu in de terminal bekijken?"
   - Default: No (show summary first)
   - Uses Rich markdown rendering for beautiful output

5. **Interactive Selection**
   - Prompts: "Kandidaten bekijken en naar Trello sturen?"
   - Default: Yes
   - Launches interactive UI to browse and select guests

### Output Files

```
output/reports/week_41_20251012.md    # Markdown report
data/previous_guests.json              # Deduplication database
data/candidates_latest.json            # Latest candidates for UI
```

### Configuration

Edit `src/guest_search/config.py`:

```python
TARGET_CANDIDATES = 5        # Number of guests to find
EXCLUDE_WEEKS = 12          # Don't recommend same guest within X weeks
MAX_SEARCH_ITERATIONS = 10  # Max search queries to execute
```

---

## Topic Researcher

Find interesting AI topics for your podcast audience.

### Basic Usage

```bash
python topic_search.py
```

### Workflow

1. **Check Existing Report**
   - Automatically checks if report exists for today
   - Format: `week_41_20251012.md` (week number + date)
   - If exists, shows summary and offers to display it
   - Prevents duplicate API calls on same day

2. **Existing Report Flow**
   ```
   ⚠️  Er bestaat al een rapport voor vandaag
   Aangemaakt: 12 October 2025

   Bestaand rapport tonen? [y/n] (y):
   ```

   - **Yes**: Shows report summary + renders markdown
   - **No**: Asks if you want to create new report (overwrites)

3. **Topic Search Phase** (if no report or creating new)
   - AI searches for 6-8 interesting AI topics
   - Looks for content from last month
   - Targets "Anne de Vries" persona (IT product owner, early adopter)
   - Uses web_search and fetch_page_content tools
   - Shows live progress with topic count

4. **Report Generation**
   - Creates markdown report with emoji categories
   - Saves both MD and JSON files
   - Provides search keywords and discussion angles

5. **Report Preview**
   - Prompts: "Wil je het rapport nu in de terminal bekijken?"
   - Default: Yes
   - Beautiful Rich markdown with emoji headers

### Topic Categories

- 🔬 **Wetenschappelijk** - Research breakthrough with practical implications
- 💼 **Praktijkvoorbeeld** - Dutch organization successfully using AI
- 📚 **Informatief** - Explanation of AI concept/tech that's now relevant
- 🔄 **Transformatie** - Sector/industry being transformed by AI
- ⚠️ **Waarschuwend** - Risk, failure, or ethical dilemma
- 🚀 **Kans** - New opportunity or tool to try immediately

### Target Persona: Anne de Vries

- **Role**: IT product owner at mid-size Dutch company
- **Experience**: Knows basic AI concepts, not deeply technical
- **Interest**: Practical AI application in work and personal life
- **Attitude**: Enthusiastic but critical - wants to know what works AND what doesn't
- **Need**: Concrete examples, practical tips, relatable stories

### Output Files

```
output/topic_reports/week_41_20251012.md      # Markdown report with emojis
output/topic_reports/week_41_20251012.json    # JSON data (for processing)
```

### Report Content per Topic

Each topic includes:

- **Title** - Catchy title (max 60 chars)
- **Category** - One of the 6 categories above
- **Why relevant for Anne** - 2-3 sentences explaining value
- **Description** - Short description (2-3 sentences)
- **Search keywords** - 3-5 keywords to find guests (use with guest_search tool)
- **Discussion angles** - 3-4 questions/perspectives for podcast
- **Sources** - Minimum 2 recent sources (preferably Dutch)

### Duplicate Detection

The tool automatically prevents duplicate searches:

- Checks for existing report based on **week number + date**
- If report exists, shows it instead of searching again
- Option to force new search (overwrites existing)
- Saves API costs and prevents duplicate work

---

## Markdown Report Viewing

Both tools support beautiful terminal rendering of markdown reports.

### Features

- **Rich Formatting**: Headers, bold, italic, lists
- **Syntax Highlighting**: Code blocks with themes
- **Beautiful Headers**: H1 with bordered boxes, H2/H3 with underlining
- **Clean Lists**: Bullet points (•) and numbered lists
- **Visible URLs**: Links shown for easy copying
- **Section Dividers**: Horizontal rules (---) as visual separators

### How It Works

When prompted "Wil je het rapport nu in de terminal bekijken?":

- Loads the markdown file
- Creates Rich `Markdown` object
- Renders with proper formatting, word wrapping, and colors
- Shows full report in terminal without opening editor

### Example Output

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        Potentiële gasten voor AIToday Live - Week 41        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Deze week focus op AI-regelgeving en praktische implementaties.

                          Nieuwe kandidaten

         Dr. Sarah Veldman - Senior AI Policy Advisor bij TNO

Mogelijke onderwerpen:

 • AI Act implementatie in Nederlandse bedrijven
 • Praktische uitdagingen bij compliance
 • Best practices voor risicobeoordelingen
```

### Manual Rendering

You can also render any markdown file manually:

```bash
# Using Rich directly
python -m rich.markdown output/reports/week_41_20251012.md

# Using Python
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("output/reports/week_41_20251012.md") as f:
    md = Markdown(f.read())
    console.print(md)
```

---

## Interactive Guest Selection

Browse and select guests using the beautiful terminal UI.

### Launch Options

```bash
# After running main.py (automatic)
python main.py

# Standalone (uses existing data)
python select_guests.py

# Demo mode (no Trello, shows UI only)
python demo_ui.py
```

### UI Features

**Display:**
- 📋 Compact panels for each guest
- 🎨 Color-coded: Green for new, Yellow for recent (last 2 weeks)
- 🔗 Full source URLs displayed
- 📧 Contact info when available (email, LinkedIn)
- 📅 Date recommended for recent guests

**Navigation:**
- Type a number (e.g., `1`, `2`, `3`) to select that guest
- Type `all` to export all new guests at once
- Type `quit` or `q` to exit
- Invalid input shows helpful error message

**Each Guest Panel Shows:**

```
════════════════════════════════════════════════════════
                  1. Dr. Sarah Veldman
════════════════════════════════════════════════════════

Rol & Organisatie:
  Senior AI Policy Advisor bij TNO

Expertise:
  • AI Act implementatie
  • AI-ethiek en governance
  • Technische haalbaarheid van regelgeving

Waarom interessant:
  Dr. Veldman leidt het TNO onderzoek naar AI Act
  implementatie. Haar expertise combineert juridische
  kennis met technische haalbaarheid.

Bronnen:
  • AI Act Implementatie Congres
    https://aic4nl.nl/evenement/ai-act-congres/
  • TNO AI Policy Research
    https://www.tno.nl/ai-act-onderzoek

Contact:
  📧 sarah.veldman@tno.nl
  🔗 linkedin.com/in/sarahveldman
```

---

## Trello Integration

Export selected guests directly to your Trello board.

### Setup

See [TRELLO_SETUP.md](../TRELLO_SETUP.md) for detailed setup instructions.

Quick setup:
1. Get API key: https://trello.com/app-key
2. Generate token: Click link on API key page
3. Add to `.env`:
   ```
   TRELLO_API_KEY=your_key_here
   TRELLO_TOKEN=your_token_here
   ```

### Usage

When selecting a guest in the interactive UI:

1. Type the guest number
2. Agent connects to Trello (board: "AIToday Live", list: "Spot")
3. Checks for duplicates (prevents creating same card twice)
4. Creates card if new
5. Shows success message with card URL

### Card Format

**Title:**
```
[Naam] - [Organisatie]
```

**Description (order optimized for readability):**

```markdown
**[Rol] bij [Organisatie]**

## Waarom interessant
[Context and relevance]

## Expertise
- Topic 1
- Topic 2
- Topic 3

## Contact
📧 [email]
🔗 [LinkedIn]

## Bronnen
• [Source 1]
  [URL 1]
• [Source 2]
  [URL 2]
```

**Key features:**
- ✅ Role/function at top for quick scanning
- ✅ Why interesting comes before details
- ✅ Sources at bottom as reference material
- ✅ Duplicate detection prevents multiple cards
- ✅ Clean markdown formatting

### Error Handling

**Duplicate Card:**
```
❌ Card for 'Dr. Sarah Veldman - TNO' already exists in the Spot list.
   Please delete the existing card first or use a different name.
```

**Missing Configuration:**
```
⚠️  Trello niet geconfigureerd
   Voeg TRELLO_API_KEY en TRELLO_TOKEN toe aan .env
```

**Network Issues:**
```
❌ Kon geen verbinding maken met Trello: [error details]
```

---

## Tips & Best Practices

### Guest Finder

- **Run weekly**: Get fresh candidates every week
- **Review recent guests**: Check yellow-highlighted recent guests before running new search
- **Verify sources**: Click URLs in UI to verify candidate relevance
- **Update previous_guests.json**: Keeps deduplication accurate

### Topic Researcher

- **Run once per day**: Duplicate detection prevents wasted API calls
- **Review existing report first**: Before forcing new search
- **Use JSON output**: Process topic data programmatically if needed
- **Combine with guest finder**: Use topic keywords to find relevant guests

### Markdown Reports

- **View in terminal**: Faster than opening editor
- **Copy URLs easily**: All sources visible for quick access
- **Share via file**: Reports are standalone markdown files
- **Version control friendly**: Plain text, easy to track changes

### Trello Integration

- **Check for duplicates**: UI warns before creating
- **Update cards manually**: Edit in Trello after creation
- **Use Spot list**: Keeps new candidates separate
- **Move to other lists**: Workflow: Spot → Contacted → Scheduled → Done

---

## Troubleshooting

### No Search Results

**Problem:** Search providers returning no results

**Solutions:**
1. Check API keys in `.env`
2. Verify API quota not exceeded
3. Check provider status:
   ```bash
   python -c "from src.guest_search.smart_search_tool import SmartSearchTool; t = SmartSearchTool(); print(t.search('test'))"
   ```
4. Check logs for rate limit errors

### Empty Reports

**Problem:** Report generated but no candidates found

**Solutions:**
1. Check search queries in planning phase
2. Verify web pages are being fetched (not just snippets)
3. Increase `MAX_SEARCH_ITERATIONS` in config
4. Check previous_guests.json isn't blocking everyone

### Trello Connection Failed

**Problem:** Can't connect to Trello

**Solutions:**
1. Verify credentials in `.env`
2. Check token hasn't expired (generate new one)
3. Verify board name: "AIToday Live"
4. Verify list name: "Spot"
5. See [TRELLO_SETUP.md](../TRELLO_SETUP.md)

### Markdown Not Rendering

**Problem:** Report shows as plain text

**Solutions:**
1. Verify Rich library installed: `pip install rich`
2. Check terminal supports color/formatting
3. Try viewing file manually: `python -m rich.markdown report.md`

---

## Advanced Usage

### Custom Prompts

Edit `src/guest_search/prompts.py` to customize:

- `PLANNING_PROMPT` - Strategy creation
- `SEARCH_EXECUTION_PROMPT` - Search instructions
- `REPORT_GENERATION_PROMPT` - Report formatting
- `TOPIC_SEARCH_PROMPT` - Topic search criteria
- `TOPIC_REPORT_GENERATION_PROMPT` - Topic report format

### Custom Target Persona

Edit `TOPIC_SEARCH_PROMPT` in prompts.py:

```python
## De ideale luisteraar: [Your Persona]

[Your persona description]:
- **Achtergrond**: [background]
- **Ervaring**: [experience level]
- **Interesse**: [interests]
- **Houding**: [attitude]
- **Behoefte**: [needs]
```

### Batch Processing

Process multiple topics programmatically:

```python
from src.guest_search.topic_agent import TopicFinderAgent
import json

agent = TopicFinderAgent()
agent.run_topic_search()

# Access topics
with open("output/topic_reports/week_41_20251012.json") as f:
    topics = json.load(f)

for topic in topics:
    print(f"Topic: {topic['title']}")
    print(f"Keywords: {', '.join(topic['search_keywords'])}")
```

---

For more information, see:
- [README.md](../README.md) - Main documentation
- [TRELLO_SETUP.md](../TRELLO_SETUP.md) - Trello configuration
- [RATE_LIMIT_HANDLING.md](RATE_LIMIT_HANDLING.md) - Search provider details
