import json
from datetime import datetime, timedelta
from typing import cast

from anthropic.types import ToolParam
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import Config
from .prompts import PLANNING_PROMPT, REPORT_GENERATION_PROMPT, SEARCH_EXECUTION_PROMPT
from .tools import get_tools
from src.utils.portkey_client import get_anthropic_client
from src.utils.smart_search_tool import SmartSearchTool


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

                    # Truncate if too long (max 4000 chars)
                    if len(text) > 4000:
                        text = text[:4000] + "\n\n[...tekst ingekort...]"

                    return {"url": url, "content": text, "status": "success"}
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
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}%20{company.replace(' ', '%20')}"
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

        prompt = PLANNING_PROMPT.format(current_date=current_date, day_of_week=day_of_week)

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

                prompt = SEARCH_EXECUTION_PROMPT.format(
                    searches_done=i,
                    total_searches=len(queries),
                    candidates_found=len(self.candidates),
                    target_candidates=Config.TARGET_CANDIDATES,
                    current_query=query_obj["query"],
                    query_rationale=query_obj.get("rationale", ""),
                )

                # Voeg toe aan conversatie
                conversation.append({"role": "user", "content": prompt})

                # Agent doet zoekopdracht
                response = self.client.messages.create(
                    model=Config.MODEL,
                    max_tokens=Config.SEARCH_MAX_TOKENS,
                    tools=cast(list[ToolParam], self.tools),
                    messages=conversation,
                )

                # Verwerk response en tool calls (zonder print statements)
                assistant_message = {"role": "assistant", "content": []}

                for block in response.content:
                    if block.type == "text":
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        # Voer tool uit (silent)
                        result = self._handle_tool_call(block.name, block.input, silent=True)

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

                        # Reset voor volgende iteratie
                        assistant_message = {"role": "assistant", "content": []}

                # Voeg laatste assistant message toe als die text bevat
                if assistant_message["content"]:
                    conversation.append(assistant_message)

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

        # Haal recent aanbevolen gasten op (laatste 2 weken)
        recent_guests = self._get_recent_guests(weeks=2)

        # Als er geen nieuwe kandidaten zijn, maar wel recente gasten, maak dan toch een rapport
        if not self.candidates and not recent_guests:
            print("⚠️  Geen kandidaten gevonden en geen recente gasten")
            return "Geen nieuwe kandidaten deze week."

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]📊 FASE 3: RAPPORT GENEREREN[/bold cyan]\n"
                "Agent maakt gestructureerd overzicht",
                border_style="cyan",
            )
        )

        prompt = REPORT_GENERATION_PROMPT.format(
            candidates_json=json.dumps(self.candidates, indent=2, ensure_ascii=False),
            recent_guests_json=json.dumps(recent_guests, indent=2, ensure_ascii=False),
            week_number=week_number,
            has_new_candidates=len(self.candidates) > 0,
            has_recent_guests=len(recent_guests) > 0,
        )

        with self.console.status("[cyan]Agent schrijft rapport...[/cyan]"):
            response = self.client.messages.create(
                model=Config.MODEL,
                max_tokens=Config.SEARCH_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

        # Extract text from first content block
        first_block = response.content[0]
        if first_block.type == "text":
            report = first_block.text
        else:
            report = "Error: Unexpected response type"

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
