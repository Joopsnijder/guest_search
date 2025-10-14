"""Topic Finder Agent - Zoekt interessante AI-topics voor de podcast."""

import json
from datetime import datetime
from typing import Any, cast

from anthropic.types import ToolParam
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.guest_search.config import Config
from src.topic_search.prompts import TOPIC_REPORT_GENERATION_PROMPT, TOPIC_SEARCH_PROMPT
from src.utils.portkey_client import get_anthropic_client
from src.utils.smart_search_tool import SmartSearchTool


class TopicFinderAgent:
    """Agent die interessante AI-topics zoekt voor de podcast."""

    def __init__(self):
        self.client = get_anthropic_client(Config.ANTHROPIC_API_KEY)
        self.topics = []
        self.smart_search = SmartSearchTool(enable_cache=True)
        self.console = Console()
        self.current_activity = "Initialiseren..."

    def _get_topic_tools(self):
        """Definieer de tools specifiek voor topic search."""
        return [
            {
                "name": "web_search",
                "description": """Zoek op het web naar recente AI-ontwikkelingen,
                nieuws, trends en discussies. Geeft resultaten met titel, snippet en URL.

                Gebruik voor:
                - Recente AI-ontwikkelingen (laatste 14 dagen)
                - Wetenschappelijke doorbraken
                - Praktijkvoorbeelden van AI-implementaties
                - Controverses en discussies over AI
                - Nieuwe AI-regelgeving en beleid
                - AI-transformaties in sectoren

                Tips voor effectief zoeken:
                - Voeg "Nederland" of "Dutch" toe aan queries voor lokale context
                - Gebruik quotes voor exacte zinnen
                - Voeg tijdsaanduiding toe: "2024", "recent", "laatste week"
                - Combineer met sector: "AI gezondheidszorg", "AI onderwijs"
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "De zoekopdracht"}},
                    "required": ["query"],
                },
            },
            {
                "name": "fetch_page_content",
                "description": """Haal de volledige inhoud van een webpagina op om
                details te vinden over AI-ontwikkelingen, onderzoeksresultaten, of
                praktijkvoorbeelden. Gebruik dit voor diepgaande analyse van veelbelovende topics.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "De URL van de pagina om op te halen",
                        }
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "save_topic",
                "description": """Sla een interessant topic op voor het eindrapport.
                Gebruik dit zodra je een relevant AI-topic hebt gevonden en geverifieerd.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Pakkende titel voor het topic"},
                        "category": {
                            "type": "string",
                            "enum": [
                                "Wetenschappelijk",
                                "Praktijkvoorbeeld",
                                "Informatief",
                                "Transformatie",
                                "Waarschuwend",
                                "Kans",
                            ],
                            "description": "Categorie van het topic",
                        },
                        "why_relevant_for_anne": {
                            "type": "string",
                            "description": "Waarom dit interessant is voor Anne de Vries",
                        },
                        "description": {
                            "type": "string",
                            "description": "Korte beschrijving van het topic (2-3 zinnen)",
                        },
                        "search_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Zoektermen om gasten te vinden voor dit topic",
                        },
                        "discussion_angles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Mogelijke discussiehoeken voor in de podcast",
                        },
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string"},
                                    "title": {"type": "string"},
                                    "date": {"type": "string"},
                                },
                            },
                            "description": "Bronnen die dit topic onderbouwen",
                        },
                    },
                    "required": [
                        "title",
                        "category",
                        "why_relevant_for_anne",
                        "description",
                        "search_keywords",
                        "discussion_angles",
                        "sources",
                    ],
                },
            },
        ]

    def _handle_tool_call(self, tool_name, tool_input, silent=False, progress=None, task=None):
        """Verwerk tool calls van de agent."""

        if tool_name == "web_search":
            query = tool_input["query"]

            # Update progress with current search query
            if progress and task is not None:
                short_query = query[:45] if len(query) > 45 else query
                progress.update(
                    task,
                    description=f"[cyan]🔍 Zoeken: {short_query}...",
                    topics=len(self.topics),
                )

            search_result = self.smart_search.search(query, num_results=10)

            if search_result["results"]:
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

            # Update progress with domain being fetched
            if progress and task is not None:
                from urllib.parse import urlparse

                domain = urlparse(url).netloc or url[:30]
                progress.update(
                    task,
                    description=f"[cyan]📄 Ophalen: {domain}...",
                    topics=len(self.topics),
                )

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

        elif tool_name == "save_topic":
            self.topics.append(tool_input)

            # Update progress with saved topic
            if progress and task is not None:
                topic_title = tool_input.get("title", "Onbekend")
                short_title = topic_title[:35] if len(topic_title) > 35 else topic_title
                progress.update(
                    task,
                    description=f"[green]💾 Opgeslagen: {short_title}...",
                    topics=len(self.topics),
                )

            return {"status": "saved", "total_topics": len(self.topics)}

        return {"error": "Unknown tool"}

    def run_topic_search(self):
        """Zoek interessante AI-topics."""

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]🔍 TOPIC SEARCH[/bold cyan]\n"
                "Agent zoekt interessante AI-topics voor Anne de Vries",
                border_style="cyan",
            )
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        day_of_week = datetime.now().strftime("%A")

        prompt = TOPIC_SEARCH_PROMPT.format(current_date=current_date, day_of_week=day_of_week)

        # Create progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[cyan]{task.fields[topics]} topics"),
        )

        tools = cast(list[ToolParam], self._get_topic_tools())
        conversation: list[Any] = [{"role": "user", "content": prompt}]

        with Live(progress, console=self.console):
            task = progress.add_task(
                "[cyan]Zoeken naar interessante AI-topics...", total=None, topics=0
            )

            # Agent zoekt topics met iteratieve tool calls
            max_iterations = 20  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                response = self.client.messages.create(
                    model=Config.MODEL,
                    max_tokens=Config.SEARCH_MAX_TOKENS,
                    tools=tools,
                    messages=conversation,
                )

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent is done
                    break

                # Process response and tool calls
                assistant_message: dict[str, Any] = {"role": "assistant", "content": []}
                has_tool_calls = False

                for block in response.content:
                    if block.type == "text":
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        has_tool_calls = True

                        # Execute tool (silent) with progress updates
                        result = self._handle_tool_call(
                            block.name, block.input, silent=True, progress=progress, task=task
                        )

                        # Add tool use and result to conversation
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

                        # Reset for next iteration
                        assistant_message = {"role": "assistant", "content": []}

                        # Update progress
                        progress.update(task, topics=len(self.topics))

                # Add last assistant message if it has text
                if assistant_message["content"] and not has_tool_calls:
                    conversation.append(assistant_message)
                    break

                # If no tool calls and no end_turn, something went wrong
                if not has_tool_calls:
                    break

        # Show summary
        summary = Table(show_header=False, box=None)
        summary.add_row("[green]✓[/green]", "Topics gevonden", f"[bold]{len(self.topics)}[/bold]")

        self.console.print(
            Panel(summary, title="[bold green]Zoeken Voltooid", border_style="green")
        )

    def generate_report(self):
        """Genereer rapport met gevonden topics."""

        if not self.topics:
            self.console.print("[yellow]⚠️  Geen topics gevonden[/yellow]")
            return "Geen interessante topics deze week."

        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]📊 RAPPORT GENEREREN[/bold cyan]\nAgent maakt gestructureerd overzicht",
                border_style="cyan",
            )
        )

        week_number = datetime.now().isocalendar()[1]

        prompt = TOPIC_REPORT_GENERATION_PROMPT.format(
            topics_json=json.dumps(self.topics, indent=2, ensure_ascii=False),
            week_number=week_number,
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

        # Save report
        import os

        os.makedirs("output/topic_reports", exist_ok=True)
        filename = f"output/topic_reports/week_{week_number}_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        # Save topics JSON for reference
        topics_filename = (
            f"output/topic_reports/week_{week_number}_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(topics_filename, "w", encoding="utf-8") as f:
            json.dump(self.topics, f, indent=2, ensure_ascii=False)

        summary = Table(show_header=False, box=None)
        summary.add_row("[green]✓[/green]", "Rapport", filename)
        summary.add_row("[green]✓[/green]", "Topics JSON", topics_filename)

        self.console.print(Panel(summary, title="[bold green]Rapport Klaar", border_style="green"))

        return report

    def display_report(self, report: str):
        """Toon het rapport mooi geformatteerd in de terminal."""
        self.console.print()
        self.console.print("=" * 80)
        md = Markdown(report)
        self.console.print(md)
        self.console.print("=" * 80)

    def run_full_cycle(self):
        """Voer volledige cyclus uit: zoeken en rapporteren."""

        # Search for topics
        self.run_topic_search()

        # Generate report
        report = self.generate_report()

        return report
