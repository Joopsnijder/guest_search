"""Trello integration for managing podcast guests using direct API calls."""

import os

import requests


class TrelloManager:
    """Manage Trello board operations for AIToday Live guests."""

    def __init__(self, api_key: str | None = None, token: str | None = None):
        """Initialize Trello client."""
        self.api_key = api_key or os.getenv("TRELLO_API_KEY")
        self.token = token or os.getenv("TRELLO_TOKEN")

        if not self.api_key or not self.token:
            raise ValueError(
                "TRELLO_API_KEY and TRELLO_TOKEN must be set in environment or passed as arguments"
            )

        self.base_url = "https://api.trello.com/1"
        self.board_id = None
        self.list_id = None

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict | list:
        """Make a request to the Trello API."""
        url = f"{self.base_url}{endpoint}"

        # Add auth parameters
        params = kwargs.pop("params", {})
        params["key"] = self.api_key
        params["token"] = self.token

        response = requests.request(method, url, params=params, **kwargs, timeout=10)

        if response.status_code in (200, 201):
            return response.json()
        else:
            raise Exception(f"Trello API error: {response.status_code} - {response.text[:500]}")

    def connect(self, board_name: str = "AIToday Live", list_name: str = "Spot"):
        """Connect to the Trello board and list."""
        # Get all boards
        boards = self._make_request("GET", "/members/me/boards")

        # Find the board
        board = next((b for b in boards if b["name"] == board_name), None)

        if not board:
            raise ValueError(f"Board '{board_name}' not found")

        self.board_id = board["id"]

        # Get all lists in the board
        lists = self._make_request("GET", f"/boards/{self.board_id}/lists")

        # Find the list
        target_list = next((lst for lst in lists if lst["name"] == list_name), None)

        if not target_list:
            raise ValueError(f"List '{list_name}' not found in board '{board_name}'")

        self.list_id = target_list["id"]

        return True

    def create_guest_card(self, guest: dict) -> dict:
        """
        Create a Trello card for a guest.

        Args:
            guest: Dictionary with guest information

        Returns:
            Dictionary with card info (id, url, name)
        """
        if not self.list_id:
            raise ValueError("Not connected to Trello. Call connect() first.")

        # Format card name (just the guest's name)
        card_name = guest.get("name", "Unknown Guest")

        # Check if card already exists
        if self.card_exists(card_name):
            raise ValueError(
                f"Card for '{card_name}' already exists in the Spot list. "
                "Please delete the existing card first or use a different name."
            )

        # Format card description with all details
        description_parts = []

        # === HEADER: Role and organization (most important info first) ===
        role = guest.get("role", "")
        organization = guest.get("organization", "")
        if role and organization:
            description_parts.append(f"**{role} bij {organization}**\n")
        elif organization:
            description_parts.append(f"**{organization}**\n")

        # === MAIN CONTENT: Relevance and Topics ===
        # Relevance (why interesting)
        if "relevance_description" in guest and guest["relevance_description"]:
            description_parts.append("**Waarom interessant:**")
            description_parts.append(guest["relevance_description"])
            description_parts.append("")

        # Why now (for recent guests)
        if "why_now" in guest and guest["why_now"]:
            description_parts.append("**Context:**")
            description_parts.append(guest["why_now"])
            description_parts.append("")

        # Topics
        if "topics" in guest and guest["topics"]:
            description_parts.append("**Mogelijke onderwerpen:**")
            for topic in guest["topics"]:
                description_parts.append(f"- {topic}")
            description_parts.append("")

        # === FOOTER: Contact info and Sources ===
        # Contact info
        contact_info = guest.get("contact_info", {})
        if contact_info:
            contact_parts = []
            if "email" in contact_info and contact_info["email"]:
                contact_parts.append(f"Email: {contact_info['email']}")
            if "linkedin" in contact_info and contact_info["linkedin"]:
                contact_parts.append(f"LinkedIn: {contact_info['linkedin']}")

            if contact_parts:
                description_parts.append("**Contact:**")
                for part in contact_parts:
                    description_parts.append(f"- {part}")
                description_parts.append("")

        # Sources
        if "sources" in guest and guest["sources"]:
            description_parts.append("**Bronnen:**")
            for source in guest["sources"]:
                if isinstance(source, dict):
                    url = source.get("url", "")
                    title = source.get("title", url)
                    date = source.get("date", "")
                    if url:
                        date_str = f" ({date})" if date else ""
                        description_parts.append(f"- [{title}]({url}){date_str}")
            description_parts.append("")

        # Date recommended (for recent guests)
        if "date" in guest and guest["date"]:
            from datetime import datetime

            try:
                date_obj = datetime.fromisoformat(guest["date"])
                date_str = date_obj.strftime("%d %B %Y")
                description_parts.append(f"\n\n_Aanbevolen op: {date_str}_")
            except (ValueError, TypeError):
                pass

        description = "\n".join(description_parts)

        # Create the card via API
        card = self._make_request(
            "POST",
            "/cards",
            params={"name": card_name, "desc": description, "idList": self.list_id},
        )

        return {"id": card["id"], "url": card["url"], "name": card["name"]}

    def card_exists(self, guest_name: str) -> bool:
        """Check if a card with this guest name already exists in the Spot list."""
        if not self.list_id:
            raise ValueError("Not connected to Trello. Call connect() first.")

        # Get all cards in the list
        cards = self._make_request("GET", f"/lists/{self.list_id}/cards")

        return any(card["name"] == guest_name for card in cards)

    def get_card_by_name(self, guest_name: str) -> dict | None:
        """Get a card by its name."""
        if not self.list_id:
            raise ValueError("Not connected to Trello. Call connect() first.")

        # Get all cards in the list
        cards = self._make_request("GET", f"/lists/{self.list_id}/cards")

        return next((card for card in cards if card["name"] == guest_name), None)

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by its ID."""
        self._make_request("DELETE", f"/cards/{card_id}")
        return True
