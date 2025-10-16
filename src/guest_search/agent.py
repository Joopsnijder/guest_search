import json
import os
from datetime import datetime, timedelta
from typing import cast

from anthropic.types import ToolParam
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.utils.portkey_client import get_anthropic_client
from src.utils.smart_search_tool import SmartSearchTool

from .config import Config
from .prompts import (
    PLANNING_PROMPT,
    REPORT_GENERATION_PROMPT,
    SEARCH_EXECUTION_PROMPT_CACHEABLE,
    SEARCH_EXECUTION_PROMPT_DYNAMIC,
)
from .tools import get_tools


class GuestFinderAgent:
    def __init__(self):
        self.client = get_anthropic_client(Config.ANTHROPIC_API_KEY)
        self.tools = get_tools()
        self.candidates = []
        self.previous_guests = self._load_previous_guests()
        # Initialize smart search tool (will auto-detect API keys from env)
        self.smart_search = SmartSearchTool(enable_cache=True)
        # Rich console for pretty output
        self.console = Console()
        # Learning: Track query performance and strategy
        self.search_history = self._load_search_history()
        self.current_session_queries = []
        self.current_session_strategy = None

    def _load_previous_guests(self):
        """Laad lijst van eerder aanbevolen gasten"""
        try:
            with open("data/previous_guests.json", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_previous_guests(self):
        """Bewaar bijgewerkte gastenlijst"""
        import os

        os.makedirs("data", exist_ok=True)
        with open("data/previous_guests.json", "w", encoding="utf-8") as f:
            json.dump(self.previous_guests, f, indent=2, ensure_ascii=False)

    def _get_recent_guests(self, weeks: int = 2):
        """Haal gasten op die recent zijn aanbevolen (laatste N weken)"""
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        recent_guests = []

        for guest in self.previous_guests:
            try:
                guest_date = datetime.fromisoformat(guest["date"])
                if guest_date >= cutoff_date:
                    recent_guests.append(guest)
            except (ValueError, KeyError):
                continue

        return recent_guests

    def _handle_enrich_candidate(self, tool_input: dict) -> str:
        """Handle enrich_candidate tool call to update candidate with enriched data."""
        name = tool_input.get("name", "")
        enriched_topics = tool_input.get("enriched_topics", [])
        enriched_relevance = tool_input.get("enriched_relevance", "")

        # Find candidate by name
        for candidate in self.candidates:
            if candidate["name"] == name:
                # Update with enriched data
                candidate["topics"] = enriched_topics
                candidate["relevance_description"] = enriched_relevance
                return f"✓ Kandidaat '{name}' verrijkt met {len(enriched_topics)} topics"

        return f"⚠️ Kandidaat '{name}' niet gevonden"

    def _load_search_history(self):
        """Laad search history voor learning"""
        try:
            with open("data/search_history.json", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"sessions": []}

    def _save_search_history(self):
        """Bewaar search history"""
        import os

        os.makedirs("data", exist_ok=True)
        with open("data/search_history.json", "w", encoding="utf-8") as f:
            json.dump(self.search_history, f, indent=2, ensure_ascii=False)

    def _get_recently_used_sources(self, weeks: int = 1):
        """Haal bronnen op die recent zijn gebruikt (voor deduplicatie)"""
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        recent_sources = set()

        for session in self.search_history.get("sessions", []):
            try:
                session_date = datetime.fromisoformat(session["date"])
                if session_date >= cutoff_date:
                    # Verzamel alle bronnen uit deze sessie
                    for query in session.get("queries", []):
                        for source in query.get("successful_sources", []):
                            recent_sources.add(source)
            except (ValueError, KeyError):
                continue

        return list(recent_sources)

    def _get_learning_insights(self, weeks: int = 4):
        """Analyseer recente search history voor learning insights"""
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        recent_sessions = []

        for session in self.search_history.get("sessions", []):
            try:
                session_date = datetime.fromisoformat(session["date"])
                if session_date >= cutoff_date:
                    recent_sessions.append(session)
            except (ValueError, KeyError):
                continue

        if not recent_sessions:
            return None

        # Verzamel alle queries met hun performance
        all_queries = []
        for session in recent_sessions:
            for query in session.get("queries", []):
                all_queries.append(query)

        # Sorteer queries op candidates gevonden (meest succesvol eerst)
        successful_queries = [q for q in all_queries if q.get("candidates_found", 0) > 0]
        successful_queries.sort(key=lambda x: x.get("candidates_found", 0), reverse=True)

        # Verzamel meest productieve bronnen
        source_stats = {}
        for query in all_queries:
            for source in query.get("successful_sources", []):
                source_stats[source] = source_stats.get(source, 0) + 1

        # Top 5 bronnen
        top_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        # Verzamel previous strategies (for reflection)
        previous_strategies = []
        for session in recent_sessions:
            if "strategy" in session and session["strategy"]:
                previous_strategies.append(
                    {
                        "week_focus": session["strategy"].get("week_focus", ""),
                        "candidates_found": session.get("total_candidates", 0),
                        "date": session.get("date", ""),
                    }
                )

        return {
            "total_sessions": len(recent_sessions),
            "total_queries": len(all_queries),
            "successful_queries": len(successful_queries),
            "top_performing_queries": successful_queries[:5],
            "top_sources": [source for source, count in top_sources],
            "previous_strategies": previous_strategies,  # NEW
            "avg_candidates_per_query": (
                sum(q.get("candidates_found", 0) for q in all_queries) / len(all_queries)
                if all_queries
                else 0
            ),
        }

    def _handle_tool_call(self, tool_name, tool_input, silent=False):
        """Verwerk tool calls van de agent"""

        if tool_name == "web_search":
            query = tool_input["query"]

            # Use SmartSearchTool with automatic fallback
            search_result = self.smart_search.search(query, num_results=10)

            if search_result["results"]:
                # Format results for the agent
                return {
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "snippet": r.get("snippet", ""),
                            "url": r.get("link", ""),
                        }
                        for r in search_result["results"]
                    ],
                    "provider": search_result.get("provider", "unknown"),
                }
            else:
                return {"results": [], "error": "No results found"}

        elif tool_name == "fetch_page_content":
            url = tool_input["url"]

            try:
                import requests
                from bs4 import BeautifulSoup

                response = requests.get(
                    url,
                    timeout=10,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                        )
                    },
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text content
                    text = soup.get_text()

                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = "\n".join(chunk for chunk in chunks if chunk)

                    # Extract potential person names with context
                    import re

                    potential_persons = []

                    # Pattern 1: Names with titles (Prof., Dr., etc.)
                    title_patterns = [
                        r"(Prof\.?\s+(?:dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))",
                        r"(Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))",
                        r"(Drs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))",
                        r"(Ir\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))",
                    ]

                    for pattern in title_patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            full_match = match.group(1)
                            name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                            # Get context (50 chars before and after)
                            start = max(0, match.start() - 50)
                            end = min(len(text), match.end() + 100)
                            context = text[start:end].replace("\n", " ")
                            potential_persons.append(
                                {"name": name, "title_match": full_match, "context": context}
                            )

                    # Pattern 2: Names with job titles/roles
                    role_patterns = [
                        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(hoogleraar|professor|docent|onderzoeker|CEO|CTO|directeur|hoofd|lead|manager|wethouder|burgemeester)",
                        r"(hoogleraar|professor|docent|onderzoeker|CEO|CTO|directeur|hoofd|lead|manager|wethouder|burgemeester)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                        r"volgens\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                        r"door\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),",
                        r"zegt\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                        r"vertelt\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                        r"aldus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                    ]

                    for pattern in role_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            # Extract name from match groups
                            name = None
                            for group in match.groups():
                                if (
                                    group
                                    and len(group.split()) >= 2
                                    and group[0].isupper()
                                    and group.lower()
                                    not in [
                                        "hoogleraar",
                                        "professor",
                                        "docent",
                                        "onderzoeker",
                                        "ceo",
                                        "cto",
                                        "directeur",
                                        "hoofd",
                                        "lead",
                                        "manager",
                                        "wethouder",
                                        "burgemeester",
                                    ]
                                ):
                                    name = group
                                    break

                            if name:
                                start = max(0, match.start() - 50)
                                end = min(len(text), match.end() + 100)
                                context = text[start:end].replace("\n", " ")
                                potential_persons.append({"name": name, "context": context})

                    # Remove duplicates (same name)
                    seen_names = set()
                    unique_persons = []
                    for person in potential_persons:
                        name_lower = person["name"].lower()
                        if name_lower not in seen_names:
                            seen_names.add(name_lower)
                            unique_persons.append(person)

                    # Truncate text if too long (max 4000 chars)
                    if len(text) > 4000:
                        text = text[:4000] + "\n\n[...tekst ingekort...]"

                    return {
                        "url": url,
                        "content": text,
                        "potential_persons": unique_persons[:10],  # Max 10 to avoid overload
                        "persons_found": len(unique_persons),
                        "status": "success",
                    }
                else:
                    return {"url": url, "error": f"HTTP {response.status_code}", "status": "error"}

            except Exception as e:
                return {"url": url, "error": str(e), "status": "error"}

        elif tool_name == "check_previous_guests":
            name = tool_input["name"]
            cutoff_date = datetime.now() - timedelta(weeks=Config.EXCLUDE_WEEKS)

            for guest in self.previous_guests:
                if guest["name"].lower() == name.lower():
                    guest_date = datetime.fromisoformat(guest["date"])
                    if guest_date >= cutoff_date:
                        return {
                            "already_recommended": True,
                            "date": guest["date"],
                            "weeks_ago": (datetime.now() - guest_date).days // 7,
                        }

            return {"already_recommended": False}

        elif tool_name == "save_candidate":
            self.candidates.append(tool_input)
            return {"status": "saved", "total_candidates": len(self.candidates)}

        elif tool_name == "search_linkedin_profile":
            name = tool_input["name"]
            company = tool_input["company"]
            # TODO: Implement real LinkedIn search logic here
            # For now, return a mock LinkedIn profile URL based on name and company
            name_encoded = name.replace(" ", "%20")
            company_encoded = company.replace(" ", "%20")
            linkedin_url = (
                f"https://www.linkedin.com/search/results/people/"
                f"?keywords={name_encoded}%20{company_encoded}"
            )
            return {"linkedin_url": linkedin_url, "status": "success"}

        return {"error": "Unknown tool"}

    def run_planning_phase(self):
        """Fase 1: Agent maakt zoekstrategie"""

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]📋 FASE 1: PLANNING[/bold cyan]\n"
                "Agent analyseert trends en maakt zoekstrategie",
                border_style="cyan",
            )
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        day_of_week = datetime.now().strftime("%A")

        # Learning: Get insights from previous searches
        learning_insights = self._get_learning_insights(weeks=4)
        recently_used_sources = self._get_recently_used_sources(weeks=1)

        # Format learning section for prompt
        if learning_insights and learning_insights["total_sessions"] > 0:
            learning_section = f"""## 🎓 Leergeschiedenis (laatste 4 weken)

Je hebt de afgelopen 4 weken {learning_insights["total_queries"]} zoekopdrachten uitgevoerd \
in {learning_insights["total_sessions"]} sessies.

**Succesvol gebleken queries** (vonden meeste kandidaten):
"""
            for i, query in enumerate(learning_insights["top_performing_queries"][:3], 1):
                query_text = query["query"]
                candidates = query["candidates_found"]
                learning_section += f'\n{i}. "{query_text}" → {candidates} kandidaten'

            if learning_insights["top_sources"]:
                learning_section += "\n\n**Meest productieve bronnen:**\n"
                for source in learning_insights["top_sources"][:5]:
                    domain = source.split("/")[2] if "/" in source else source
                    learning_section += f"- {domain}\n"

            avg = learning_insights["avg_candidates_per_query"]
            learning_section += f"\n**Gemiddeld**: {avg:.1f} kandidaten per query\n"

            # Add previous strategies (for reflection)
            if learning_insights.get("previous_strategies"):
                learning_section += "\n\n📋 **Eerdere strategieën:**\n"
                for strat in learning_insights["previous_strategies"][:3]:
                    focus = strat.get("week_focus", "Geen focus opgegeven")[:60]
                    candidates = strat.get("candidates_found", 0)
                    learning_section += f'- "{focus}" → {candidates} kandidaten\n'

                # Add reflection prompt
                if avg < 1.0:
                    learning_section += (
                        "\n⚠️ **KRITISCH**: Gemiddeld <1 kandidaat per query. "
                        "Vorige strategieën werkten niet. Overweeg:\n"
                        "- Andere query types (niet alleen site:)\n"
                        "- Bredere bronnen (niet alleen vakmedia)\n"
                        "- Andere zoektermen (meer Nederlands, minder technisch)\n"
                    )

            # Add recently used sources warning
            if recently_used_sources:
                learning_section += "\n\n⚠️ **Recent gebruikte bronnen** (laatste week):\n"
                learning_section += (
                    "Deze bronnen zijn recent gebruikt. "
                    "Personen hiervan vallen mogelijk binnen de 8-weken exclusie.\n"
                )
                for source in recently_used_sources[:5]:
                    domain = source.split("/")[2] if "/" in source else source
                    learning_section += f"- {domain}\n"
                learning_section += (
                    "\n**Zoek bij voorkeur naar NIEUWE bronnen** om duplicaten te voorkomen.\n"
                )
        else:
            learning_section = "## 🎓 Leergeschiedenis\n\nDit is je eerste zoeksessie. \
Er is nog geen historische data beschikbaar.\n"

        prompt = PLANNING_PROMPT.format(
            current_date=current_date,
            day_of_week=day_of_week,
            learning_section=learning_section,
        )

        with self.console.status("[cyan]Agent denkt na over zoekstrategie...[/cyan]"):
            response = self.client.messages.create(
                model=Config.MODEL,
                max_tokens=Config.PLANNING_MAX_TOKENS,
                thinking={"type": "enabled", "budget_tokens": Config.PLANNING_THINKING_BUDGET},
                messages=[{"role": "user", "content": prompt}],
            )

        # Extraheer strategy uit response
        strategy_text = None

        for block in response.content:
            if block.type == "text":
                strategy_text = block.text

        # Parse JSON uit strategy
        try:
            if strategy_text is None:
                print("⚠️  Geen strategy text gevonden in response")
                return None

            # Zoek eerste valide JSON object in de tekst
            start = strategy_text.find("{")
            if start == -1:
                raise json.JSONDecodeError("No JSON found in response", strategy_text, 0)

            # Probeer JSON te parsen met incremental depth tracking
            depth = 0
            in_string = False
            escape_next = False

            for i in range(start, len(strategy_text)):
                char = strategy_text[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            # Found complete JSON object
                            json_str = strategy_text[start : i + 1]
                            strategy_json = json.loads(json_str)
                            break
            else:
                raise json.JSONDecodeError("No complete JSON found", strategy_text, 0)

            # Create summary table
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_row(
                "[green]✓[/green]",
                "Focus",
                strategy_json.get("week_focus", "Niet gespecificeerd")[:80],
            )

            if "search_queries" in strategy_json:
                table.add_row(
                    "[green]✓[/green]", "Queries", str(len(strategy_json["search_queries"]))
                )

            if "sectors_to_prioritize" in strategy_json:
                sectors = ", ".join(strategy_json["sectors_to_prioritize"])
                table.add_row("[green]✓[/green]", "Sectoren", sectors)

            self.console.print(
                Panel(table, title="[bold green]Strategie Klaar", border_style="green")
            )

            # Learning: Save strategy for this session
            self.current_session_strategy = {
                "week_focus": strategy_json.get("week_focus", ""),
                "sectors_to_prioritize": strategy_json.get("sectors_to_prioritize", []),
                "topics_to_cover": strategy_json.get("topics_to_cover", []),
                "total_queries_planned": len(strategy_json.get("search_queries", [])),
            }

            return strategy_json

        except json.JSONDecodeError as e:
            self.console.print(f"[red]⚠️  Kon JSON niet parsen: {e}[/red]")
            return None

    def run_search_phase(self, strategy):
        """Fase 2: Voer zoekopdrachten uit"""

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]🔍 FASE 2: ZOEKEN[/bold cyan]\n"
                "Agent zoekt en analyseert potentiële gasten",
                border_style="cyan",
            )
        )

        if not strategy or "search_queries" not in strategy:
            self.console.print("[red]❌ Geen geldige strategie ontvangen[/red]")
            return

        queries = strategy["search_queries"]
        conversation = []

        # Create progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[candidates]} kandidaten"),
        )

        with Live(progress, console=self.console):
            task = progress.add_task(
                "[cyan]Zoeken...",
                total=min(len(queries), Config.MAX_SEARCH_ITERATIONS),
                candidates=0,
            )

            for i, query_obj in enumerate(queries[: Config.MAX_SEARCH_ITERATIONS]):
                # Learning: Track candidates before query
                candidates_before = len(self.candidates)

                # Update progress description with current query
                short_query = query_obj["query"][:50]
                progress.update(
                    task,
                    description=f"[cyan]{short_query}...",
                    candidates=len(self.candidates),
                )

                # Check of we genoeg kandidaten hebben
                if len(self.candidates) >= Config.TARGET_CANDIDATES:
                    progress.update(task, description="[green]✓ Target bereikt!", completed=True)
                    break

                # Format dynamic part of the prompt
                dynamic_prompt = SEARCH_EXECUTION_PROMPT_DYNAMIC.format(
                    searches_done=i,
                    total_searches=len(queries),
                    candidates_found=len(self.candidates),
                    target_candidates=Config.TARGET_CANDIDATES,
                    current_query=query_obj["query"],
                    query_rationale=query_obj.get("rationale", ""),
                )

                # Use prompt caching if enabled: cache static instructions, vary dynamic part
                # Cache TTL is 5 minutes - perfect for 8-12 query sessions
                if Config.ENABLE_PROMPT_CACHING:
                    # Use structured content with cache_control marker
                    conversation.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": SEARCH_EXECUTION_PROMPT_CACHEABLE,
                                    "cache_control": {"type": "ephemeral"},
                                },
                                {"type": "text", "text": dynamic_prompt},
                            ],
                        }
                    )
                else:
                    # Legacy mode: combine prompts into single string
                    combined_prompt = SEARCH_EXECUTION_PROMPT_CACHEABLE + "\n\n" + dynamic_prompt
                    conversation.append({"role": "user", "content": combined_prompt})

                # Learning: Track sources used in this query
                sources_used = []

                # Multi-turn conversation loop: agent kan meerdere tool calls doen
                max_turns = 10  # Safety limit
                turn_count = 0

                while turn_count < max_turns:
                    turn_count += 1

                    # Agent doet zoekopdracht (of vervolgactie)
                    response = self.client.messages.create(
                        model=Config.MODEL,
                        max_tokens=Config.SEARCH_MAX_TOKENS,
                        tools=cast(list[ToolParam], self.tools),
                        messages=conversation,
                    )

                    # DEBUG: Print stop reason
                    if os.getenv("DEBUG_TOOLS"):
                        self.console.print(
                            f"[dim]Turn {turn_count}, Stop: {response.stop_reason}[/dim]"
                        )

                    # Verwerk response en tool calls
                    assistant_message = {"role": "assistant", "content": []}
                    has_tool_use = False

                    for block in response.content:
                        if block.type == "text":
                            assistant_message["content"].append(block)

                        elif block.type == "tool_use":
                            has_tool_use = True

                            # DEBUG: Print tool calls
                            if os.getenv("DEBUG_TOOLS"):
                                self.console.print(f"[dim]🔧 Tool: {block.name}[/dim]")

                            # Voer tool uit (silent)
                            result = self._handle_tool_call(block.name, block.input, silent=True)

                            # DEBUG: Print results
                            if os.getenv("DEBUG_TOOLS"):
                                if block.name == "fetch_page_content":
                                    self.console.print(
                                        f"[dim]   → Status: {result.get('status')}, "
                                        f"Persons: {result.get('persons_found', 0)}[/dim]"
                                    )
                                elif block.name == "save_candidate":
                                    # block.input is a dict at runtime
                                    name = block.input.get("name", "unknown")  # type: ignore
                                    self.console.print(f"[dim]   → Saved: {name}[/dim]")

                            # Learning: Track successful fetch_page_content calls
                            if (
                                block.name == "fetch_page_content"
                                and result.get("status") == "success"
                            ):
                                sources_used.append(block.input.get("url", ""))

                            # Voeg tool use en result toe aan conversatie
                            assistant_message["content"].append(block)
                            conversation.append(assistant_message)
                            conversation.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": block.id,
                                            "content": json.dumps(result),
                                        }
                                    ],
                                }
                            )

                            # Reset voor volgende tool call
                            assistant_message = {"role": "assistant", "content": []}

                    # Voeg laatste assistant message toe als die text bevat
                    if assistant_message["content"]:
                        conversation.append(assistant_message)

                    # Stop loop als agent geen tool calls meer doet (klaar met deze query)
                    if not has_tool_use:
                        if os.getenv("DEBUG_TOOLS"):
                            self.console.print("[dim]✓ Agent finished (no more tools)[/dim]")
                        break

                # Learning: Calculate candidates found by this query
                candidates_found = len(self.candidates) - candidates_before

                # Learning: Record query performance
                query_record = {
                    "query": query_obj["query"],
                    "rationale": query_obj.get("rationale", ""),
                    "priority": query_obj.get("priority", "medium"),
                    "candidates_found": candidates_found,
                    "successful_sources": sources_used,
                    "timestamp": datetime.now().isoformat(),
                }
                self.current_session_queries.append(query_record)

                # Update progress
                progress.update(task, advance=1, candidates=len(self.candidates))

        # Show summary
        summary = Table(show_header=False, box=None)
        summary.add_row(
            "[green]✓[/green]", "Kandidaten gevonden", f"[bold]{len(self.candidates)}[/bold]"
        )
        summary.add_row("[green]✓[/green]", "Queries uitgevoerd", f"{i + 1}/{len(queries)}")

        self.console.print(
            Panel(summary, title="[bold green]Zoeken Voltooid", border_style="green")
        )

    def generate_report(self):
        """Fase 3: Genereer eindrapport"""

        week_number = datetime.now().isocalendar()[1]

        # Als er geen nieuwe kandidaten zijn, skip rapport generatie
        if not self.candidates:
            self.console.print()
            self.console.print(
                "[yellow]⚠️  Geen nieuwe kandidaten gevonden - rapport wordt overgeslagen[/yellow]"
            )
            return "Geen nieuwe kandidaten deze week."

        # Haal recent aanbevolen gasten op (laatste 2 weken) voor context
        recent_guests = self._get_recent_guests(weeks=2)

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]📊 FASE 3: RAPPORT GENEREREN[/bold cyan]\n"
                "Agent maakt gestructureerd overzicht",
                border_style="cyan",
            )
        )

        # Define enrich_candidate tool for capturing enriched data
        enrich_tool = {
            "name": "enrich_candidate",
            "description": (
                "Sla verrijkte kandidaat informatie op met uitgebreide topics "
                "en relevance description"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Volledige naam van de kandidaat "
                            "(moet exact matchen met bestaande kandidaat)"
                        ),
                    },
                    "enriched_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "4-5 specifieke, concrete onderwerpen "
                            "(bijv. 'Cijfers over AI-impact op banen in Nederland' "
                            "niet alleen 'AI')"
                        ),
                    },
                    "enriched_relevance": {
                        "type": "string",
                        "description": (
                            "Uitgebreide relevance description van 3-5 zinnen die "
                            "feitelijk beschrijft wat deze persoon doet en waarom relevant"
                        ),
                    },
                },
                "required": ["name", "enriched_topics", "enriched_relevance"],
            },
        }

        prompt = REPORT_GENERATION_PROMPT.format(
            candidates_json=json.dumps(self.candidates, indent=2, ensure_ascii=False),
            recent_guests_json=json.dumps(recent_guests, indent=2, ensure_ascii=False),
            week_number=week_number,
            has_new_candidates=len(self.candidates) > 0,
            has_recent_guests=len(recent_guests) > 0,
        )

        # Use multi-turn conversation to handle tool calls and report generation
        conversation: list = [{"role": "user", "content": prompt}]
        report = None

        status_msg = "[cyan]Agent verrijkt kandidaten en schrijft rapport...[/cyan]"
        with self.console.status(status_msg):
            # Max 10 turns (enough for enriching all candidates + report)
            for turn_num in range(10):
                response = self.client.messages.create(
                    model=Config.MODEL,
                    max_tokens=Config.SEARCH_MAX_TOKENS,
                    messages=conversation,  # type: ignore
                    tools=[enrich_tool],  # type: ignore
                )

                # Debug: show what the agent is doing
                if os.getenv("DEBUG_TOOLS"):
                    self.console.print(f"[dim]Turn {turn_num + 1}: {response.stop_reason}[/dim]")
                    for block in response.content:
                        if block.type == "text":
                            self.console.print(f"[dim]  Text: {block.text[:100]}...[/dim]")
                        elif block.type == "tool_use":
                            self.console.print(f"[dim]  Tool: {block.name}[/dim]")

                # Check if there are tool calls in the response (regardless of stop reason)
                has_tool_calls = any(block.type == "tool_use" for block in response.content)

                if has_tool_calls:
                    # Process tool calls
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            if block.name == "enrich_candidate":
                                # Convert tool input to dict
                                tool_input = dict(block.input) if block.input else {}
                                result = self._handle_enrich_candidate(tool_input)

                                # Show progress
                                name = tool_input.get("name", "unknown")  # type: ignore
                                self.console.print(f"[dim]✓ Verrijkt: {name}[/dim]")

                                tool_results.append(
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result,
                                    }
                                )

                    # Add assistant message and tool results to conversation
                    conversation.append({"role": "assistant", "content": response.content})
                    conversation.append({"role": "user", "content": tool_results})

                elif response.stop_reason == "end_turn":
                    # Extract text from response
                    for block in response.content:
                        if block.type == "text":
                            report = block.text
                            break
                    break
                else:
                    # Unexpected stop reason
                    break

        if not report:
            report = "Error: Kon geen rapport genereren"

        # Bewaar rapport
        filename = f"output/reports/week_{week_number}_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        summary = Table(show_header=False, box=None)
        summary.add_row("[green]✓[/green]", "Rapport", filename)
        if recent_guests:
            summary.add_row("[yellow]📋[/yellow]", "Recente gasten", f"{len(recent_guests)}")

        self.console.print(Panel(summary, title="[bold green]Rapport Klaar", border_style="green"))

        # Update previous_guests
        for candidate in self.candidates:
            guest_entry = {
                "name": candidate["name"],
                "date": datetime.now().isoformat(),
                "organization": candidate["organization"],
                "role": candidate.get("role", ""),
                "why_now": candidate.get("relevance_description", ""),
                "sources": [],
            }

            # Extract source URLs from candidate
            if "sources" in candidate and isinstance(candidate["sources"], list):
                for source in candidate["sources"]:
                    if isinstance(source, dict) and "url" in source:
                        guest_entry["sources"].append(
                            {
                                "url": source["url"],
                                "title": source.get("title", ""),
                                "date": source.get("date", ""),
                            }
                        )

            self.previous_guests.append(guest_entry)

        self._save_previous_guests()

        # Save current candidates for interactive selector
        self._save_candidates_for_selector()

        # Learning: Save session data to search history
        session_record = {
            "date": datetime.now().isoformat(),
            "week_number": week_number,
            "total_queries": len(self.current_session_queries),
            "total_candidates": len(self.candidates),
            "strategy": self.current_session_strategy,  # NEW: Save the planning strategy
            "queries": self.current_session_queries,
        }
        self.search_history["sessions"].append(session_record)
        self._save_search_history()

        return report

    def _save_candidates_for_selector(self):
        """Save current candidates to a file for the interactive selector."""
        import os

        os.makedirs("data", exist_ok=True)
        with open("data/candidates_latest.json", "w", encoding="utf-8") as f:
            json.dump(self.candidates, f, indent=2, ensure_ascii=False)

    def display_report(self, report: str):
        """Toon het rapport mooi geformatteerd in de terminal."""
        self.console.print()
        self.console.print("=" * 80)
        md = Markdown(report)
        self.console.print(md)
        self.console.print("=" * 80)

    def run_full_cycle(self):
        """Voer volledige cyclus uit"""

        # Fase 1: Planning
        strategy = self.run_planning_phase()

        if not strategy:
            self.console.print("[red]❌ Planning fase mislukt[/red]")
            return None

        # Fase 2: Zoeken
        self.run_search_phase(strategy)

        # Fase 3: Rapporteren
        report = self.generate_report()

        return report
        return report
        return report
