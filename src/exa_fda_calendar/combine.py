from typing import List, Dict, Tuple

def _k(ev: Dict) -> Tuple:
    # remove duplicate (drug, company, pdufa_date / fda_date_no_pdufa) 
    return (
        (ev.get("drug") or "").strip().lower(),
        (ev.get("company") or "").strip().lower(),
        (ev.get("pdufa_date") or ev.get("fda_date_no_pdufa") or "").strip(),
    )

def merge_and_dedupe(lists_: List[List[Dict]]) -> List[Dict]:
    seen = set()
    out: List[Dict] = []
    for L in lists_:
        for ev in L:
            key = _k(ev)
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
    # sort: data, PDUFA, no-PDUFA
    def _sort_key(e: Dict):
        d = e.get("pdufa_date") or e.get("fda_date_no_pdufa") or "9999-12-31"
        return (d, e.get("drug",""))
    out.sort(key=_sort_key)
    return out
