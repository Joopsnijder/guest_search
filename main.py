import os

from src.guest_search.agent import GuestFinderAgent
from src.guest_search.config import Config


def main():
    # Check API key
    if not Config.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY niet gevonden in .env")
        return

    # Maak directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("output/reports", exist_ok=True)

    # Initialiseer previous_guests.json als die niet bestaat
    if not os.path.exists("data/previous_guests.json"):
        with open("data/previous_guests.json", "w") as f:
            f.write("[]")

    # Run agent
    agent = GuestFinderAgent()
    report = agent.run_full_cycle()

    if report:
        print("\n" + "=" * 60)
        print("RAPPORT PREVIEW")
        print("=" * 60)
        print(report[:500] + "...\n")


if __name__ == "__main__":
    main()
