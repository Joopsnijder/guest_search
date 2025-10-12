import json
from datetime import datetime, timedelta
from typing import cast

from anthropic import Anthropic
from anthropic.types import ToolParam

from .config import Config
from .prompts import PLANNING_PROMPT, REPORT_GENERATION_PROMPT, SEARCH_EXECUTION_PROMPT
from .smart_search_tool import SmartSearchTool
from .tools import get_tools


class GuestFinderAgent:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.tools = get_tools()
        self.candidates = []
        self.previous_guests = self._load_previous_guests()
        # Initialize smart search tool (will auto-detect API keys from env)
        self.smart_search = SmartSearchTool(enable_cache=True)

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

    def _handle_tool_call(self, tool_name, tool_input):
        """Verwerk tool calls van de agent"""

        if tool_name == "web_search":
            query = tool_input["query"]
            print(f"🔍 Zoeken: {query}")

            # Use SmartSearchTool with automatic fallback
            search_result = self.smart_search.search(query, num_results=10)

            if search_result["results"]:
                provider = search_result.get("provider", "unknown")
                cache_hit = search_result.get("cache_hit", False)
                cache_info = " (cached)" if cache_hit else ""
                print(f"   ✓ {len(search_result['results'])} resultaten via {provider}{cache_info}")

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
                    "provider": provider,
                }
            else:
                print("   ⚠️  Geen resultaten gevonden")
                return {"results": [], "error": "No results found"}

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
            print(f"✅ Kandidaat opgeslagen: {tool_input['name']}")
            self.candidates.append(tool_input)
            return {"status": "saved", "total_candidates": len(self.candidates)}

        return {"error": "Unknown tool"}

    def run_planning_phase(self):
        """Fase 1: Agent maakt zoekstrategie"""

        print("\n" + "=" * 60)
        print("📋 FASE 1: PLANNING")
        print("=" * 60)

        current_date = datetime.now().strftime("%Y-%m-%d")
        day_of_week = datetime.now().strftime("%A")

        prompt = PLANNING_PROMPT.format(current_date=current_date, day_of_week=day_of_week)

        print("🤖 Agent denkt na over zoekstrategie...")

        response = self.client.messages.create(
            model=Config.MODEL,
            max_tokens=Config.PLANNING_MAX_TOKENS,
            thinking={"type": "enabled", "budget_tokens": Config.PLANNING_THINKING_BUDGET},
            messages=[{"role": "user", "content": prompt}],
        )

        # Extraheer strategy uit response
        strategy_text = None
        thinking_summary = []

        for block in response.content:
            if block.type == "thinking":
                thinking_summary.append(f"💭 Denkproces: {len(block.thinking)} tekens")
            elif block.type == "text":
                strategy_text = block.text

        print("\n".join(thinking_summary))

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

            print("\n✅ Strategie gemaakt:")
            print(f"   - Focus: {strategy_json.get('week_focus', 'Niet gespecificeerd')}")

            if "search_queries" in strategy_json:
                print(f"   - Aantal queries: {len(strategy_json['search_queries'])}")
            else:
                print("   ⚠️  Geen search_queries gedefinieerd")

            if "sectors_to_prioritize" in strategy_json:
                print(
                    f"   - Prioriteit sectoren: {', '.join(strategy_json['sectors_to_prioritize'])}"
                )
            else:
                print("   ⚠️  Geen sectors_to_prioritize gedefinieerd")

            return strategy_json

        except json.JSONDecodeError as e:
            print(f"⚠️  Kon JSON niet parsen: {e}")
            print(f"Response was:\n{strategy_text}")
            return None

    def run_search_phase(self, strategy):
        """Fase 2: Voer zoekopdrachten uit"""

        print("\n" + "=" * 60)
        print("🔍 FASE 2: ZOEKEN")
        print("=" * 60)

        if not strategy or "search_queries" not in strategy:
            print("❌ Geen geldige strategie ontvangen")
            return

        queries = strategy["search_queries"]
        conversation = []

        for i, query_obj in enumerate(queries[: Config.MAX_SEARCH_ITERATIONS]):
            print(f"\n--- Zoekopdracht {i + 1}/{len(queries)} ---")

            # Check of we genoeg kandidaten hebben
            if len(self.candidates) >= Config.TARGET_CANDIDATES:
                print(f"✅ Target bereikt: {len(self.candidates)} kandidaten")
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

            # Verwerk response en tool calls
            assistant_message = {"role": "assistant", "content": []}

            for block in response.content:
                if block.type == "text":
                    print(f"💬 Agent: {block.text[:200]}...")
                    assistant_message["content"].append(block)

                elif block.type == "tool_use":
                    print(f"🛠️  Tool: {block.name}")

                    # Voer tool uit
                    result = self._handle_tool_call(block.name, block.input)

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

        print(f"\n✅ Zoekfase afgerond: {len(self.candidates)} kandidaten gevonden")

    def generate_report(self):
        """Fase 3: Genereer eindrapport"""

        print("\n" + "=" * 60)
        print("📊 FASE 3: RAPPORT GENEREREN")
        print("=" * 60)

        if not self.candidates:
            print("⚠️  Geen kandidaten gevonden")
            return "Geen nieuwe kandidaten deze week."

        week_number = datetime.now().isocalendar()[1]

        prompt = REPORT_GENERATION_PROMPT.format(
            candidates_json=json.dumps(self.candidates, indent=2, ensure_ascii=False),
            week_number=week_number,
        )

        print("🤖 Agent schrijft rapport...")

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

        print(f"✅ Rapport opgeslagen: {filename}")

        # Update previous_guests
        for candidate in self.candidates:
            self.previous_guests.append(
                {
                    "name": candidate["name"],
                    "date": datetime.now().isoformat(),
                    "organization": candidate["organization"],
                }
            )

        self._save_previous_guests()

        return report

    def run_full_cycle(self):
        """Voer volledige cyclus uit"""

        print("\n🚀 Start AIToday Live Guest Finder Agent")
        print(f"📅 {datetime.now().strftime('%A, %d %B %Y - %H:%M')}")

        # Fase 1: Planning
        strategy = self.run_planning_phase()

        if not strategy:
            print("❌ Planning fase mislukt")
            return None

        # Fase 2: Zoeken
        self.run_search_phase(strategy)

        # Fase 3: Rapporteren
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("✅ KLAAR!")
        print("=" * 60)
        print(f"Totaal kandidaten: {len(self.candidates)}")

        return report
