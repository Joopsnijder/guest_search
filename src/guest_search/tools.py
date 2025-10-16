"""Tool definitions for the Guest Finder Agent."""


def get_tools():
    """Definieer de tools die de agent kan gebruiken"""

    return [
        {
            "name": "web_search",
            "description": """Zoek op het web naar recente informatie over AI-experts,
            nieuws, persberichten en publicaties. Geeft resultaten met titel, snippet en URL.

            Gebruik voor:
            - Nederlandse AI-experts zoeken
            - Recente persberichten van universiteiten/bedrijven
            - Vakmedia artikelen (AG Connect, Computable)
            - LinkedIn posts over AI-projecten
            - Congresprogramma's en sprekers

            Tips voor effectief zoeken:
            - Voeg "Nederland" of "Dutch" toe aan queries
            - Gebruik quotes voor exacte zinnen: "AI Act implementatie"
            - Combineer naam + organisatie voor verificatie
            - Voeg tijdsaanduiding toe: "2024" of "recent"
            """,
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "De zoekopdracht"}},
                "required": ["query"],
            },
        },
        {
            "name": "fetch_page_content",
            "description": """Haal de volledige inhoud van een webpagina op en extraheer automatisch
            personen met hun context. Gebruik dit voor:
            - Congresprogramma's om sprekers te vinden
            - University pages om onderzoekers te identificeren
            - Persberichten om namen en functies te vinden
            - Vakmedia artikelen om experts te extraheren

            De tool returnt:
            - content: De volledige paginatext (max 4000 chars)
            - potential_persons: Lijst van gedetecteerde personen met context
            - persons_found: Aantal unieke personen gevonden

            De tool gebruikt patroonherkenning om personen te vinden:
            - Titels: Prof., Dr., Drs., Ir.
            - Rollen: hoogleraar, CEO, directeur, wethouder, etc.
            - Citaten: "volgens [Name]", "zegt [Name]", "vertelt [Name]"

            Elk persoon bevat:
            - name: De volledige naam
            - context: 150 karakters rondom de naam voor context
            - title_match: (optioneel) Als er een titel werd gevonden
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
            "name": "check_previous_guests",
            "description": """Controleer of een persoon recent is aanbevolen (laatste 8 weken).
            Voorkom duplicaten door dit te gebruiken voordat je iemand toevoegt aan de
            kandidatenlijst.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Volledige naam van de persoon"}
                },
                "required": ["name"],
            },
        },
        {
            "name": "save_candidate",
            "description": """Sla een kandidaat op voor het eindrapport.
            Gebruik dit zodra je een persoon hebt geverifieerd met minimaal 2 bronnen.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "organization": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "relevance_description": {"type": "string"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs waar deze persoon gevonden is",
                    },
                    "contact_info": {
                        "type": "object",
                        "properties": {"email": {"type": "string"}, "linkedin": {"type": "string"}},
                    },
                },
                "required": [
                    "name",
                    "role",
                    "organization",
                    "topics",
                    "relevance_description",
                    "sources",
                ],
            },
        },
    ]
