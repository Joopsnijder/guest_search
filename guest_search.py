import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from src.guest_search.agent import GuestFinderAgent
from src.guest_search.config import Config
from src.guest_search.interactive_selector import InteractiveGuestSelector


def main():
    console = Console()

    # Check API key
    if not Config.ANTHROPIC_API_KEY:
        console.print("[red]❌ ANTHROPIC_API_KEY niet gevonden in .env[/red]")
        return

    # Maak directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("output/reports", exist_ok=True)

    # Initialiseer previous_guests.json als die niet bestaat
    if not os.path.exists("data/previous_guests.json"):
        with open("data/previous_guests.json", "w") as f:
            f.write("[]")

    # Run agent
    from datetime import datetime

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]🚀 AIToday Live Guest Finder[/bold cyan]\n"
            f"📅 {datetime.now().strftime('%A, %d %B %Y - %H:%M')}",
            border_style="cyan",
        )
    )

    agent = GuestFinderAgent()
    report = agent.run_full_cycle()

    # Show brief summary
    if report and agent.candidates:
        console.print("\n" + "=" * 60)
        console.print("[bold green]✓ Zoeken voltooid![/bold green]")
        console.print("=" * 60)
        console.print(f"Nieuwe kandidaten gevonden: [bold]{len(agent.candidates)}[/bold]\n")

        # Ask if user wants to view the report in terminal
        if Confirm.ask("Wil je het rapport nu in de terminal bekijken?", default=False):
            agent.display_report(report)
            console.print()

        # Ask if user wants to review and select guests
        console.print(
            Panel.fit(
                "[bold]Wil je de kandidaten nu bekijken en selecteren voor Trello?[/bold]\n"
                "Je kunt ook later 'python select_guests.py' uitvoeren.",
                border_style="cyan",
            )
        )

        if Confirm.ask("Kandidaten bekijken en naar Trello sturen?", default=True):
            console.print()
            # Launch interactive selector
            selector = InteractiveGuestSelector()
            selector.run()
        else:
            console.print(
                "\n[cyan]Je kunt later 'python select_guests.py' "
                "uitvoeren om kandidaten te selecteren.[/cyan]"
            )

    elif report:
        console.print("\n[yellow]Geen nieuwe kandidaten gevonden deze week.[/yellow]")
        console.print(
            "[dim]Je kunt 'python select_guests.py' uitvoeren "
            "om recente kandidaten te bekijken.[/dim]"
        )


if __name__ == "__main__":
    main()
