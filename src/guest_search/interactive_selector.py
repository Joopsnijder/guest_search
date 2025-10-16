"""Interactive terminal UI for selecting and managing guests."""

import json
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .trello_manager import TrelloManager


class InteractiveGuestSelector:
    """Interactive terminal interface for selecting guests to send to Trello."""

    def __init__(self):
        self.console = Console()
        self.trello = None
        self.new_candidates = []
        self.recent_guests = []

    def load_candidates(self, candidates_file: str = "data/candidates_latest.json"):
        """Load new candidates from the agent's output."""
        try:
            with open(candidates_file, encoding="utf-8") as f:
                self.new_candidates = json.load(f)
        except FileNotFoundError:
            self.console.print(f"[yellow]Waarschuwing: {candidates_file} niet gevonden[/yellow]")
            self.new_candidates = []

    def load_recent_guests(self, previous_guests_file: str = "data/previous_guests.json"):
        """Load recent guests (last 2 weeks) from previous_guests.json."""
        try:
            with open(previous_guests_file, encoding="utf-8") as f:
                all_guests = json.load(f)

            # Filter for last 2 weeks
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(weeks=2)
            self.recent_guests = []

            for guest in all_guests:
                try:
                    guest_date = datetime.fromisoformat(guest["date"])
                    if guest_date >= cutoff_date:
                        self.recent_guests.append(guest)
                except (ValueError, KeyError):
                    continue

        except FileNotFoundError:
            self.console.print(
                f"[yellow]Waarschuwing: {previous_guests_file} niet gevonden[/yellow]"
            )
            self.recent_guests = []

    def connect_trello(self):
        """Connect to Trello."""
        try:
            self.console.print("\n[bold cyan]Verbinden met Trello...[/bold cyan]")
            self.trello = TrelloManager()
            self.trello.connect(board_name="AIToday Live", list_name="Spot")
            self.console.print("[green]✓[/green] Verbonden met Trello board 'AIToday Live'")
            return True
        except Exception as e:
            self.console.print(f"[red]✗[/red] Fout bij verbinden met Trello: {e}")
            self.console.print(
                "\n[yellow]Zorg dat TRELLO_API_KEY en TRELLO_TOKEN "
                "in je .env bestand staan[/yellow]"
            )
            return False

    def display_guest(self, guest: dict, index: int, is_recent: bool = False):
        """Display a single guest in a nice panel."""
        # Create title
        name = guest.get("name", "Unknown")
        role = guest.get("role", "")
        organization = guest.get("organization", "")

        if role and organization:
            subtitle = f"{role} bij {organization}"
        elif organization:
            subtitle = organization
        else:
            subtitle = ""

        # Create content
        content_parts = []

        # Function and company
        highlightcolor = "cyan" if not is_recent else "yellow"
        content_parts.append(f"[{highlightcolor}][bold]{subtitle}[/bold][/{highlightcolor}]")
        content_parts.append("")

        # Topics or expertise
        topics = guest.get("topics", [])
        if topics:
            content_parts.append("[bold]Onderwerpen:[/bold]")
            for topic in topics:
                content_parts.append(f"  • {topic}")
            content_parts.append("")

        # Relevance or why_now
        relevance = guest.get("relevance_description") or guest.get("why_now", "")
        if relevance:
            content_parts.append("[bold]Waarom interessant:[/bold]")
            # Wrap long text
            if len(relevance) > 100:
                content_parts.append(f"{relevance[:300]}...")
            else:
                content_parts.append(relevance)
            content_parts.append("")

        # Sources
        sources = guest.get("sources", [])
        if sources:
            content_parts.append("[bold]Bronnen:[/bold]")
            for source in sources:  # Show all sources
                if isinstance(source, dict):
                    url = source.get("url", "")
                    title = source.get("title", url)
                    date = source.get("date", "")
                    if url:
                        # Shorten title if too long
                        if len(title) > 70:
                            title = title[:67] + "..."
                        date_str = f" ({date})" if date else ""
                        # Show title and URL
                        content_parts.append(f"  • {title}{date_str}")
                        content_parts.append(f"    [dim]{url}[/dim]")
            content_parts.append("")

        # Contact info
        contact_info = guest.get("contact_info", {})
        if contact_info and (contact_info.get("email") or contact_info.get("linkedin")):
            content_parts.append("[bold]Contact:[/bold]")
            if contact_info.get("email"):
                content_parts.append(f"  📧 {contact_info['email']}")
            if contact_info.get("linkedin"):
                linkedin = contact_info["linkedin"]
                content_parts.append(f"  💼 {linkedin}")
            content_parts.append("")

        # Date recommended (for recent guests)
        if is_recent and "date" in guest:
            try:
                date_obj = datetime.fromisoformat(guest["date"])
                date_str = date_obj.strftime("%d %B %Y")
                content_parts.append(f"[dim]Aanbevolen op: {date_str}[/dim]")
            except (ValueError, TypeError):
                pass

        content = "\n".join(content_parts)

        # Create panel
        title_text = f"[{index}] {name} - {subtitle}" if subtitle else f"[{index}] {name}"
        if is_recent:
            title_text = f"[{index}] {name} [yellow](recent)[/yellow]"

        panel = Panel(
            content,
            title=title_text,
            border_style="cyan" if not is_recent else "yellow",
            padding=(1, 2),
        )

        self.console.print(panel)

    def display_all_guests(self):
        """Display all guests in a nice format."""
        self.console.clear()
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                "[bold cyan]Potentiële Gasten voor AIToday Live[/bold cyan]\n"
                "Selecteer gasten om naar Trello te sturen",
                border_style="cyan",
            )
        )
        self.console.print()

        all_guests = []
        guest_types = []

        # Add new candidates
        if self.new_candidates:
            self.console.print("[bold green]Nieuwe kandidaten:[/bold green]\n")
            for i, guest in enumerate(self.new_candidates, 1):
                self.display_guest(guest, i, is_recent=False)
                all_guests.append(guest)
                guest_types.append("new")

        # Filter recent guests to exclude duplicates with new candidates
        # Compare by name (case-insensitive)
        new_candidate_names = {c.get("name", "").lower() for c in self.new_candidates}
        filtered_recent_guests = [
            g for g in self.recent_guests if g.get("name", "").lower() not in new_candidate_names
        ]

        # Add recent guests (excluding duplicates)
        if filtered_recent_guests:
            self.console.print(
                "\n[bold yellow]Recent aanbevolen (laatste 2 weken):[/bold yellow]\n"
            )
            start_index = len(all_guests) + 1
            for i, guest in enumerate(filtered_recent_guests, start_index):
                self.display_guest(guest, i, is_recent=True)
                all_guests.append(guest)
                guest_types.append("recent")

        return all_guests, guest_types

    def run(self):
        """Run the interactive selection process."""
        # Load data
        self.load_candidates()
        self.load_recent_guests()

        if not self.new_candidates and not self.recent_guests:
            self.console.print("[yellow]Geen gasten gevonden om weer te geven.[/yellow]")
            return

        # Connect to Trello
        if not self.connect_trello():
            self.console.print(
                "\n[yellow]Je kunt nog steeds de gasten bekijken "
                "maar niet naar Trello sturen.[/yellow]"
            )
            use_trello = False
        else:
            use_trello = True

        while True:
            # Display all guests
            all_guests, guest_types = self.display_all_guests()

            if not all_guests:
                break

            # Prompt for selection
            self.console.print()
            self.console.print(
                "[bold]Kies een actie:[/bold]\n"
                "  • Typ een nummer om een gast te selecteren\n"
                "  • Typ 'all' om alle nieuwe gasten te sturen\n"
                "  • Typ 'quit' of 'q' om af te sluiten\n"
            )

            choice = Prompt.ask("Jouw keuze", default="quit")

            if choice.lower() in ["quit", "q", ""]:
                self.console.print("\n[cyan]Tot ziens![/cyan]")
                break

            if choice.lower() == "all":
                if use_trello:
                    self.send_all_new_to_trello()
                else:
                    self.console.print("[red]Trello is niet verbonden[/red]")
                continue

            # Try to parse as number
            try:
                index = int(choice)
                if 1 <= index <= len(all_guests):
                    guest = all_guests[index - 1]
                    guest_type = guest_types[index - 1]

                    if use_trello:
                        self.send_guest_to_trello(guest, guest_type)
                    else:
                        self.console.print("[red]Trello is niet verbonden[/red]")
                else:
                    self.console.print(f"[red]Ongeldige keuze: {choice}[/red]")
            except ValueError:
                self.console.print(f"[red]Ongeldige keuze: {choice}[/red]")

            self.console.print("\n[dim]Druk op Enter om door te gaan...[/dim]")
            input()

    def send_guest_to_trello(self, guest: dict, guest_type: str):
        """Send a single guest to Trello."""
        guest_name = guest.get("name", "Unknown")

        try:
            self.console.print(f"\n[cyan]Bezig met aanmaken kaart voor {guest_name}...[/cyan]")
            card_info = self.trello.create_guest_card(guest)
            self.console.print(f"[green]✓[/green] Kaart aangemaakt: {card_info['url']}")
        except ValueError as e:
            # Card already exists
            if "already exists" in str(e):
                self.console.print(
                    f"\n[yellow]⚠️  Kaart voor '{guest_name}' bestaat al in Trello[/yellow]"
                )
                self.console.print("[dim]Deze kaart is overgeslagen.[/dim]")
            else:
                self.console.print(f"[red]✗[/red] Fout: {e}")
        except Exception as e:
            self.console.print(f"[red]✗[/red] Fout bij aanmaken kaart: {e}")

    def send_all_new_to_trello(self):
        """Send all new candidates to Trello."""
        if not self.new_candidates:
            self.console.print("[yellow]Geen nieuwe kandidaten om te versturen[/yellow]")
            return

        self.console.print(
            f"\n[cyan]Alle {len(self.new_candidates)} nieuwe kandidaten "
            f"naar Trello sturen...[/cyan]\n"
        )

        success_count = 0
        skip_count = 0
        error_count = 0

        for guest in self.new_candidates:
            guest_name = guest.get("name", "Unknown")

            # Create card (will automatically check if exists)
            try:
                self.trello.create_guest_card(guest)
                self.console.print(f"[green]✓[/green] {guest_name}")
                success_count += 1
            except ValueError as e:
                # Card already exists
                if "already exists" in str(e):
                    self.console.print(f"[yellow]⊗[/yellow] {guest_name} bestaat al, overgeslagen")
                    skip_count += 1
                else:
                    self.console.print(f"[red]✗[/red] {guest_name}: {e}")
                    error_count += 1
            except Exception as e:
                self.console.print(f"[red]✗[/red] {guest_name}: {e}")
                error_count += 1

        # Summary
        self.console.print()
        summary = Panel(
            f"[green]Aangemaakt:[/green] {success_count}\n"
            f"[yellow]Overgeslagen:[/yellow] {skip_count}\n"
            f"[red]Fouten:[/red] {error_count}",
            title="Samenvatting",
            border_style="cyan",
        )
        self.console.print(summary)
