from typing import Dict, List, Tuple
from .config import SCHEMA, QUERY
from .pipeline import run_pipeline

def fetch_one_source(name: str, url: str, livecrawl: str, min_structured: int) -> Tuple[str, List[Dict]]:
    """
    Fetch one source and return (page_text, unified_events).
    The unified schema is: drug, indication, company, pdufa_date, fda_date_no_pdufa, source_url
    """
    page_text, unified = run_pipeline(
        url=url,
        schema=SCHEMA,
        query=QUERY,
        source_name=name,         
        livecrawl=livecrawl,
        min_structured=min_structured,
    )
    return page_text, unified
