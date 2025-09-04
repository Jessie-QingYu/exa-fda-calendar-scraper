from typing import Any, Dict, List, Tuple
from . import extractor
from .fallback_parser import fallback_parse_events

def run_pipeline(
    url: str,
    schema: Dict[str, Any],
    query: str,
    livecrawl: str = "preferred",
    min_structured: int = 5
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (page_text, events). If structured events < min_structured,
    try the fallback parser on page_text.
    """
    page_text, events = extractor.fetch_text_and_structured(url, schema, query, livecrawl=livecrawl)

    if len(events) < min_structured:
        print(f"Structured extraction returned {len(events)} events; trying fallback parser...")
        if page_text:
            fb = fallback_parse_events(page_text, url)
            if len(fb) > len(events):
                print(f"Fallback parser found {len(fb)} events; using fallback results.")
                events = fb
        else:
            print("Fallback skipped: page_text is empty (site likely requires login or heavy JS).")
    return page_text, events
