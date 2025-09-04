from typing import Any, Dict, List, Tuple
from .exa_client import ExaClient

def fetch_text_and_structured(
    url: str,
    schema: Dict[str, Any],
    query: str,
    livecrawl: str = "preferred"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (page_text, structured_events)
    """
    cli = ExaClient()
    page_text = cli.get_text(url, livecrawl=livecrawl)

    structured = cli.get_structured(url, schema=schema, query=query, livecrawl=livecrawl)
    events: List[Dict[str, Any]] = []
    if isinstance(structured, dict):
        events = structured.get("events", []) or []
    return page_text, events
