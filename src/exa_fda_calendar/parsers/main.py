from typing import List, Dict
from .unusualwhales import parse_unusual
from .biopharmcatalyst import parse_bpc
from .benzinga import parse_benzinga
from .checkrare import parse_checkrare
from .fda_advisory import parse_fda_gov
from .bpiq import parse_bpiq
from .fdatracker import parse_fdatracker
from .rttnews import parse_rttnews
from .base import _parse_markdown_table

def parse_by_name(name: str, page_text: str, source_url: str) -> List[Dict]:
    """
    Parse by source name - dispatches to appropriate parser
    """
    key = (name or "").lower()
    
    if key in ("unusualwhales", "unusual"):
        return parse_unusual(page_text, source_url)
    if key in ("biopharmcatalyst", "bpc"):
        return parse_bpc(page_text, source_url)
    if key.startswith("rttnews"):
        return parse_rttnews(page_text, source_url)
    if key.startswith("fdatracker"):
        return parse_fdatracker(page_text, source_url)
    if key.startswith("benzinga"):
        return parse_benzinga(page_text, source_url)
    if key.startswith("checkrare"):
        return parse_checkrare(page_text, source_url)
    if key.startswith("fda_advisory") or key == "fda_gov":
        return parse_fda_gov(page_text, source_url)
    if key.startswith("bpiq"):
        return parse_bpiq(page_text, source_url)
    
    # Fallback to generic markdown table parser
    return _parse_markdown_table(page_text, source_url)
