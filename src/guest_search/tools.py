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
            "name": "search_linkedin_profile",
            "description": "Zoek een LinkedIn-profiel op basis van naam en bedrijf. Gebruik deze tool om het meest relevante LinkedIn-profiel te vinden voor een kandidaat, door zowel de volledige naam als de organisatie te combineren voor een accurate match.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Volledige naam van de persoon"},
                    "company": {
                        "type": "string",
                        "description": "Naam van het bedrijf of de organisatie",
                    },
                },
                "required": ["name", "company"],
            },
        },
        {
            "name": "fetch_page_content",
            "description": """Haal de volledige inhoud van een webpagina op om personen,
            functies en organisaties te vinden. Gebruik dit voor:
            - Congresprogramma's om sprekers te vinden
            - University pages om onderzoekers te identificeren
            - Persberichten om namen en functies te vinden
            - LinkedIn profielen om details op te halen

            De tool geeft een samenvatting van de pagina met focus op personen,
            hun functies, organisaties en contactinformatie.
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
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                                "date": {"type": "string"},
                            },
                        },
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
