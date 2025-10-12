#!/usr/bin/env python3
"""
Demo van de Interactive Guest Selector UI (zonder Trello connectie)
"""

from rich.console import Console
from rich.panel import Panel

from src.guest_search.interactive_selector import InteractiveGuestSelector


def main():
    """Demo van de UI zonder Trello."""
    console = Console()

    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Demo: Interactive Guest Selector[/bold cyan]\n"
            "Dit is hoe de UI eruit ziet. Voor echte Trello integratie,\n"
            "configureer eerst je Trello credentials (zie TRELLO_SETUP.md)",
            border_style="cyan",
        )
    )
    console.print()

    selector = InteractiveGuestSelector()

    # Load data
    selector.load_candidates()
    selector.load_recent_guests()

    if not selector.new_candidates and not selector.recent_guests:
        console.print("[yellow]Geen gasten gevonden. Voer eerst 'python main.py' uit.[/yellow]")
        return

    # Display all guests (read-only mode)
    all_guests, guest_types = selector.display_all_guests()

    console.print()
    console.print(
        Panel(
            f"[green]✓[/green] {len(selector.new_candidates)} nieuwe kandidaten\n"
            f"[yellow]📋[/yellow] {len(selector.recent_guests)} recente gasten (laatste 2 weken)\n\n"
            "[dim]Voor interactie en Trello integratie, gebruik: python select_guests.py[/dim]",
            title="Samenvatting",
            border_style="cyan",
        )
    )


if __name__ == "__main__":
    main()
