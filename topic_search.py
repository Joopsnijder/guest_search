#!/usr/bin/env python3
"""Topic Search - Zoekt interessante AI-topics voor de podcast."""

import json
import os
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from src.guest_search.config import Config
from src.guest_search.topic_agent import TopicFinderAgent


def check_existing_report():
    """Check of er al een rapport bestaat voor vandaag."""
    week_number = datetime.now().isocalendar()[1]
    date_str = datetime.now().strftime("%Y%m%d")

    report_path = f"output/topic_reports/week_{week_number}_{date_str}.md"
    json_path = f"output/topic_reports/week_{week_number}_{date_str}.json"

    if os.path.exists(report_path) and os.path.exists(json_path):
        return report_path, json_path

    return None, None


def display_existing_report(console, report_path, json_path):
    """Toon een bestaand rapport."""
    # Load report
    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    # Load topics JSON
    with open(json_path, "r", encoding="utf-8") as f:
        topics = json.load(f)

    # Show summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Bestaand rapport gevonden![/bold green]")
    console.print("=" * 60)
    console.print(f"Topics in rapport: [bold]{len(topics)}[/bold]\n")

    # Show topic categories
    categories = {}
    for topic in topics:
        cat = topic.get("category", "Onbekend")
        categories[cat] = categories.get(cat, 0) + 1

    if categories:
        console.print("[bold]Topics per categorie:[/bold]")
        for cat, count in sorted(categories.items()):
            console.print(f"  • {cat}: {count}")

    console.print(f"\n[cyan]Rapport: {report_path}[/cyan]")

    # Ask if user wants to view it
    console.print()
    if Confirm.ask("Wil je het rapport nu in de terminal bekijken?", default=True):
        console.print()
        console.print("=" * 80)
        md = Markdown(report_content)
        console.print(md)
        console.print("=" * 80)


def main():
    console = Console()

    # Check API key
    if not Config.ANTHROPIC_API_KEY:
        console.print("[red]❌ ANTHROPIC_API_KEY niet gevonden in .env[/red]")
        return

    # Maak directories
    os.makedirs("output/topic_reports", exist_ok=True)

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]🔍 AIToday Live Topic Finder[/bold cyan]\n"
            f"📅 {datetime.now().strftime('%A, %d %B %Y - %H:%M')}\n"
            f"🎯 Zoekt interessante AI-topics voor Anne de Vries",
            border_style="cyan",
        )
    )

    # Check for existing report
    report_path, json_path = check_existing_report()

    if report_path and json_path:
        console.print()
        console.print(
            Panel.fit(
                "[bold yellow]⚠️  Er bestaat al een rapport voor vandaag[/bold yellow]\n"
                f"Aangemaakt: {datetime.now().strftime('%d %B %Y')}",
                border_style="yellow",
            )
        )

        # Ask if user wants to see existing report or create new one
        console.print()
        if Confirm.ask("Bestaand rapport tonen?", default=True):
            display_existing_report(console, report_path, json_path)
            return
        else:
            if not Confirm.ask(
                "Nieuwe zoekactie starten? (overschrijft bestaand rapport)", default=False
            ):
                console.print("\n[dim]Geannuleerd.[/dim]")
                return

    # Run agent
    agent = TopicFinderAgent()
    report = agent.run_full_cycle()

    # Show brief summary
    if report and agent.topics:
        console.print("\n" + "=" * 60)
        console.print("[bold green]✓ Topic search voltooid![/bold green]")
        console.print("=" * 60)
        console.print(f"Interessante topics gevonden: [bold]{len(agent.topics)}[/bold]\n")

        # Show topic categories
        categories = {}
        for topic in agent.topics:
            cat = topic.get("category", "Onbekend")
            categories[cat] = categories.get(cat, 0) + 1

        if categories:
            console.print("[bold]Topics per categorie:[/bold]")
            for cat, count in sorted(categories.items()):
                console.print(f"  • {cat}: {count}")

        console.print("\n[cyan]Rapport opgeslagen in output/topic_reports/[/cyan]")

        # Ask if user wants to view the report in terminal
        console.print()
        if Confirm.ask("Wil je het rapport nu in de terminal bekijken?", default=True):
            agent.display_report(report)
        else:
            console.print(
                "\n[dim]Je kunt het rapport later bekijken in output/topic_reports/[/dim]"
            )

    elif report:
        console.print("\n[yellow]Geen interessante topics gevonden deze week.[/yellow]")


if __name__ == "__main__":
    main()
