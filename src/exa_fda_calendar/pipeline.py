from typing import Any, Dict, List, Tuple
import re
from . import extractor
from .normalize import to_unified_from_structured
from . import parsers


def _regex_fallback_events(page_text: str, source_url: str) -> List[Dict[str, Any]]:
    """Very small regex-based fallback to extract legacy-shaped events.
    Looks for lines with a date followed by company (TICKER) and event keywords.
    Returns list of dicts with keys: date/company/ticker/drug/event_type/notes/source_url
    """
    if not page_text:
        return []
    events: List[Dict[str, Any]] = []
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    month_pat = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    date_re = re.compile(rf"(\d{{4}}-\d{{2}}-\d{{2}}|{month_pat}\s+\d{{1,2}},\s*\d{{4}}|\d{{1,2}}/\d{{1,2}}(?:/\d{{2,4}})?)")
    ticker_re = re.compile(r"\(([A-Z]{1,5})\)")
    for i, ln in enumerate(lines):
        m = date_re.search(ln)
        if not m:
            continue
        raw_date = m.group(1)
        date_str = raw_date
        # naive normalization for MM/DD(/YY)
        if re.fullmatch(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?", date_str):
            mm, dd, *yy = date_str.split("/")
            y = yy[0] if yy else "2025"
            if len(y) == 2:
                y = f"20{y}"
            try:
                date_str = f"{int(y):04d}-{int(mm):02d}-{int(dd):02d}"
            except Exception:
                pass
        comp = ""
        tick = ""
        m2 = ticker_re.search(ln)
        if m2:
            tick = m2.group(1)
            comp = ln.split("(", 1)[0]
            comp = comp.split(raw_date, 1)[-1].strip(" -—:|,")
        notes = ln
        ev_type = "PDUFA" if re.search(r"(?i)\bPDUFA\b", ln) else ("AdComm" if re.search(r"(?i)ad ?comm|advisory", ln) else "Event")
        events.append({
            "date": date_str,
            "company": comp,
            "ticker": tick,
            "drug": "",
            "event_type": ev_type,
            "notes": notes[:240],
            "source_url": source_url,
        })
    return events


def run_pipeline(
    url: str,
    schema: Dict[str, Any],
    query: str,
    source_name: str = "unusualwhales",   
    livecrawl: str = "preferred",
    min_structured: int = 5,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (page_text, unified_events).

    Steps:
      1) Use Exa to fetch page_text + structured JSON (legacy fields from schema).
      2) If structured count >= min_structured -> map to unified schema and return.
      3) Else run site-specific parser from parsers.parse_by_name (unified fields).
      4) If still empty, use a minimal regex fallback (legacy fields) and map to unified.
      5) Final fallback: normalize whatever structured we have (may be empty).
    """
    page_text, structured_events = extractor.fetch_text_and_structured(
        url, schema, query, livecrawl=livecrawl
    )

    # Case 1: structured → unified and return
    if len(structured_events) >= min_structured:
        unified = to_unified_from_structured(structured_events, source_url=url)
        print(f"[{source_name}] Structured OK: {len(structured_events)} -> unified {len(unified)}")
        return page_text, unified

    # Case 2: not structured 
    print(f"[{source_name}] Structured {len(structured_events)} < {min_structured}; trying site parser...")
    fb = parsers.parse_by_name(source_name, page_text or "", url)
    print(f"[{source_name}] Site parser unified events: {len(fb)}")

    if len(fb) > 0:
        return page_text, fb

    # Case 3: minimal regex fallback → normalized to unified
    legacy = _regex_fallback_events(page_text or "", url)
    if len(legacy) > 0:
        unified_from_legacy = to_unified_from_structured(legacy, source_url=url)
        print(f"[{source_name}] Regex fallback events: {len(legacy)} -> unified {len(unified_from_legacy)}")
        return page_text, unified_from_legacy

    # Case 4: 
    unified = to_unified_from_structured(structured_events, source_url=url)
    if not unified:
        print(f"[{source_name}] Fallback empty; returning empty unified list.")
    return page_text, unified
