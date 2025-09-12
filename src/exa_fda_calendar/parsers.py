import re
import csv
from io import StringIO
from typing import List, Dict

# ========== tools ==========

def _clean_link(value: str) -> (str, str):
    """
    parse markdown link [text](url) → (text, url)。
    non url return (value, "")。
    """
    if value is None:
        return "", ""
    m = re.match(r"\[(.*?)\]\((.*?)\)", value.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return value.strip(), ""

def _iso_date_like(s: str) -> str:
    """
    data YYYY-MM-DD：YYYY-MM-DD、MM/DD/YYYY(/YY)、Mon dd, yyyy、Month dd, yyyy。
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
    """unified schema"""
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
    markdown table parser
    try：Drug / Event Type / Date / Target Date / Outcome / Source Link etc，
    unified to（drug/indication/company/pdufa_date/fda_date_no_pdufa/source_url）
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if not lines:
        return []
    clean_lines = [ln.strip("| ") for ln in lines]
    reader = csv.reader(StringIO("\n".join(clean_lines)), delimiter="|")
    rows = [list(map(str.strip, r)) for r in reader]

    # find header
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
        # data：Date / Target Date
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

        # unified
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

# ==========parsers for different web url ==========

def parse_unusual(page_text: str, source_url: str) -> List[Dict]:
    """
    UnusualWhales FDA Calendar —— markdown table
    """
    return _parse_markdown_table(page_text, source_url)

def parse_bpc(page_text: str, source_url: str) -> List[Dict]:
    """
    BioPharmCatalyst FDA calendar 
    """
    return _parse_markdown_table(page_text, source_url)

def parse_rttnews(page_text: str, source_url: str) -> List[Dict]:
    """
    RTTNews FDA calendar 
    """
    return _parse_markdown_table(page_text, source_url)

def parse_fdatracker(page_text: str, source_url: str) -> List[Dict]:
    """
    FDATracker 
    """
    evts = _parse_markdown_table(page_text, source_url)
    if evts:
        return evts
    out: List[Dict] = []
    for block in re.split(r"\n\s*\n", page_text or ""):
        m_d = re.search(r"(?i)\b(PDUFA|FDA)\s*Date[:\s]+(.+?)(?:\n|$)", block)
        if not m_d:
            continue
        dt = _iso_date_like(m_d.group(2).strip())
        out.append(_mk_unified(fda_no_pdufa=dt, source_url=source_url))
    return out

def parse_benzinga(page_text: str, source_url: str) -> List[Dict]:
    """
    Benzinga FDA exact dates 
    """
    evts = _parse_markdown_table(page_text, source_url)
    if evts:
        return evts
    out: List[Dict] = []
    for b in re.split(r"\n\s*\n", page_text or ""):
        m_drug = re.search(r"(?i)\bDrug[:\s]+(.+?)(?:\n|$)", b)
        m_pdu  = re.search(r"(?i)\bPDUFA\s*Date[:\s]+(.+?)(?:\n|$)", b)
        m_comp = re.search(r"(?i)\bCompany[:\s]+(.+?)(?:\n|$)", b)
        m_ind  = re.search(r"(?i)\bIndication[:\s]+(.+?)(?:\n|$)", b)
        drug = m_drug.group(1).strip() if m_drug else ""
        pdu  = _iso_date_like(m_pdu.group(1).strip()) if m_pdu else ""
        comp = m_comp.group(1).strip() if m_comp else ""
        ind  = m_ind.group(1).strip() if m_ind else ""
        if any([drug, pdu, comp, ind]):
            out.append(_mk_unified(drug, ind, comp, pdu, "", source_url))
    return out

def parse_checkrare(page_text: str, source_url: str) -> List[Dict]:
    """
    CheckRare（2025 orphan drugs…）
    """
    out: List[Dict] = []
    # exaple：Drug: X | Indication: Y | Company: Z | PDUFA: mm/dd/yyyy
    for ln in (page_text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = re.search(
            r"(?i)Drug[:\s]+(.+?)\s+[|\-•]\s+Indication[:\s]+(.+?)\s+[|\-•]\s+Company[:\s]+(.+?)\s+[|\-•]\s+(?:PDUFA|Approval|FDA)\s*[:\s]+(.+)$",
            ln
        )
        if m:
            drug = m.group(1).strip()
            ind  = m.group(2).strip()
            comp = m.group(3).strip()
            dt   = _iso_date_like(m.group(4).strip())
            out.append(_mk_unified(drug, ind, comp, dt, "", source_url))
    return out

def parse_fda_gov(page_text: str, source_url: str) -> List[Dict]:
    """
    FDA web Advisory Committee Calendar
    fda_date_no_pdufa；drug/company missing，indication using Topic/Purpose
    """
    out: List[Dict] = []
    for block in re.split(r"\n\s*\n", page_text or ""):
        # Date
        m_date = re.search(r"(?i)\b(Date|Meeting Date)[:\s]+(.+?)(?:\n|$)", block)
        date_str = ""
        if m_date:
            date_str = _iso_date_like(m_date.group(2).strip())
        else:
            # match "Month dd, yyyy"
            m2 = re.search(r"(?i)\b([A-Z][a-z]{2,9}\s+\d{1,2},\s*\d{4})", block)
            if m2:
                date_str = _iso_date_like(m2.group(1).strip())
        if not date_str:
            continue
        # Topic/Purpose as indication
        m_topic = re.search(r"(?i)\b(Topic|Purpose)[:\s]+(.+?)(?:\n|$)", block)
        topic = m_topic.group(2).strip() if m_topic else ""
        out.append(_mk_unified(drug="", indication=topic, company="", pdufa_date="", fda_no_pdufa=date_str, source_url=source_url))
    return out

def parse_bpiq(page_text: str, source_url: str) -> List[Dict]:
    """
    BP IQ（PDUFA/Catalyst calendar）—— need login
    """
    evts = _parse_markdown_table(page_text, source_url)
    if evts:
        return evts
    out: List[Dict] = []
    for b in re.split(r"\n\s*\n", page_text or ""):
        m_drug = re.search(r"(?i)\bDrug[:\s]+(.+?)(?:\n|$)", b)
        m_ind  = re.search(r"(?i)\bIndication[:\s]+(.+?)(?:\n|$)", b)
        m_comp = re.search(r"(?i)\bCompany[:\s]+(.+?)(?:\n|$)", b)
        m_pdu  = re.search(r"(?i)\bPDUFA\s*Date[:\s]+(.+?)(?:\n|$)", b)
        drug = m_drug.group(1).strip() if m_drug else ""
        ind  = m_ind.group(1).strip() if m_ind else ""
        comp = m_comp.group(1).strip() if m_comp else ""
        pdu  = _iso_date_like(m_pdu.group(1).strip()) if m_pdu else ""
        if any([drug, ind, comp, pdu]):
            out.append(_mk_unified(drug, ind, comp, pdu, "", source_url))
    return out

# ========== parse by name ==========

def parse_by_name(name: str, page_text: str, source_url: str) -> List[Dict]:
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
    return _parse_markdown_table(page_text, source_url)
