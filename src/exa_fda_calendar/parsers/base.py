import re
import csv
from io import StringIO
from typing import List, Dict

def _clean_link(value: str) -> tuple[str, str]:
    """
    Parse markdown link [text](url) → (text, url).
    Non-url return (value, "").
    """
    if value is None:
        return "", ""
    m = re.match(r"\[(.*?)\]\((.*?)\)", value.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return value.strip(), ""

def _iso_date_like(s: str) -> str:
    """
    Convert date to YYYY-MM-DD format: YYYY-MM-DD, MM/DD/YYYY(/YY), Mon dd, yyyy, Month dd, yyyy.
    """
    if not s:
        return ""
    s = s.strip()
    # 2025-02-13
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    # 02/13/2025 or 2/13/25
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yy < 100:
            yy += 2000
        try:
            from datetime import date
            return date(yy, mm, dd).strftime("%Y-%m-%d")
        except Exception:
            return s
    # Mon dd, yyyy / Month dd, yyyy
    try:
        from datetime import datetime
        for fmt in ("%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except Exception:
                pass
    except Exception:
        pass
    return s

def _mk_unified(
    drug: str = "",
    indication: str = "",
    company: str = "",
    pdufa_date: str = "",
    fda_no_pdufa: str = "",
    source_url: str = "",
) -> Dict:
    """Create unified schema record"""
    return {
        "drug": (drug or "").strip(),
        "indication": (indication or "").strip(),
        "company": (company or "").strip(),
        "pdufa_date": _iso_date_like(pdufa_date) if pdufa_date else "",
        "fda_date_no_pdufa": _iso_date_like(fda_no_pdufa) if fda_no_pdufa else "",
        "source_url": (source_url or "").strip(),
    }

def _parse_markdown_table(text: str, source_url: str) -> List[Dict]:
    """
    Parse markdown table format
    Try: Drug / Event Type / Date / Target Date / Outcome / Source Link etc,
    unified to (drug/indication/company/pdufa_date/fda_date_no_pdufa/source_url)
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if not lines:
        return []
    clean_lines = [ln.strip("| ") for ln in lines]
    reader = csv.reader(StringIO("\n".join(clean_lines)), delimiter="|")
    rows = [list(map(str.strip, r)) for r in reader]

    # Find header
    header_idx = None
    for i, row in enumerate(rows):
        if any(h in row for h in ("Ticker", "Drug", "Event Type", "Date", "Outcome", "Source Link")):
            header_idx = i
            break
    if header_idx is None:
        return []

    headers = rows[header_idx]
    events: List[Dict] = []
    for row in rows[header_idx + 1:]:
        if len(row) < len(headers):
            continue
        rec = dict(zip(headers, row))

        # Drug
        drug = rec.get("Drug") or ""
        # Event type
        ev_type = (rec.get("Event Type") or "").lower()
        # Date: Date / Target Date
        d1 = rec.get("Date") or ""
        d2 = rec.get("Target Date") or ""
        date = d1 or d2
        date = _iso_date_like(date) if date else ""
        # Outcome
        outcome = rec.get("Outcome") or ""
        company = ""
        if outcome and "," in outcome:
            company = outcome.split(",", 1)[0].strip()
        # Source Link
        src = rec.get("Source Link") or source_url
        _, src_url = _clean_link(src)
        if not src_url:
            src_url = source_url

        # PDUFA 
        if "pdufa" in ev_type:
            pdufa = date
            other = ""
        else:
            pdufa = ""
            other = date

        # Unified
        if any([drug, pdufa, other, company]):
            events.append(_mk_unified(
                drug=drug,
                indication="",
                company=company,
                pdufa_date=pdufa,
                fda_no_pdufa=other,
                source_url=src_url,
            ))
    return events
