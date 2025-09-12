from typing import Dict, List

UNIFIED_FIELDS = [
    "drug",
    "indication",
    "company",
    "pdufa_date",
    "fda_date_no_pdufa",
    "source_url",
]


def to_unified_from_structured(structured: List[Dict], source_url: str) -> List[Dict]:
    """
    Map legacy structured fields (date/company/ticker/drug/event_type/notes/source_url)
    into the unified schema.
    """
    unified: List[Dict] = []
    if not structured:
        return unified

    for r in structured:
        drug = (r.get("drug") or "").strip()
        company = (r.get("company") or "").strip()
        src = (r.get("source_url") or source_url or "").strip()
        event_type = (r.get("event_type") or "").strip().lower()
        date = (r.get("date") or "").strip()

        # event_type with pdufa → pdufa_date；else fda_date_no_pdufa
        pdufa_date = date if ("pdufa" in event_type) else ""
        fda_no_pdufa = "" if pdufa_date else date

        unified.append({
            "drug": drug,
            "indication": "",         
            "company": company,
            "pdufa_date": pdufa_date,
            "fda_date_no_pdufa": fda_no_pdufa,
            "source_url": src,
        })

    return unified
