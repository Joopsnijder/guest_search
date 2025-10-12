#!/usr/bin/env python3
"""
Interactive Guest Selector voor AIToday Live

Dit script laat je gasten selecteren en naar Trello sturen.
"""

from src.guest_search.interactive_selector import InteractiveGuestSelector


def main():
    """Run the interactive guest selector."""
    selector = InteractiveGuestSelector()
    selector.run()


if __name__ == "__main__":
    main()
