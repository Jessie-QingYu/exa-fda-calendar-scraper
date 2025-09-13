import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like, _clean_link

def parse_unusual(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse UnusualWhales FDA Calendar - markdown table format
    Based on actual data structure from unusualwhales_raw.md
    """
    events: List[Dict] = []
    
    # Split by lines and look for table rows
    lines = page_text.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the table section
        if '| Ticker | Event Type | Date | Target Date | Drug | Outcome | Source Link |' in line:
            in_table = True
            continue
            
        if in_table and line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 8:
                ticker = parts[1]
                event_type = parts[2]
                date = parts[3]
                target_date = parts[4]
                drug = parts[5]
                outcome = parts[6]
                source_link = parts[7]
                
                # Skip header row and separator rows
                if ticker in ['Ticker', '---'] or event_type in ['Event Type', '---']:
                    continue
                
                # Extract company from outcome if available
                company = ""
                if outcome and outcome != "Pending" and outcome != "No Source":
                    # Try to extract company name from outcome
                    if "," in outcome:
                        company = outcome.split(",")[0].strip()
                    elif "announced" in outcome.lower():
                        # Extract company name before "announced"
                        match = re.search(r"^([^,]+?)\s+announced", outcome)
                        if match:
                            company = match.group(1).strip()
                
                # Determine the actual date to use
                actual_date = target_date if target_date and target_date != "Not Set" else date
                
                # Clean source link
                _, src_url = _clean_link(source_link)
                if not src_url:
                    src_url = source_url
                
                # Determine if this is a PDUFA event
                is_pdufa = "pdufa" in event_type.lower()
                
                if any([drug, actual_date, company]):
                    events.append(_mk_unified(
                        drug=drug,
                        indication="",
                        company=company,
                        pdufa_date=_iso_date_like(actual_date) if is_pdufa and actual_date else "",
                        fda_no_pdufa=_iso_date_like(actual_date) if not is_pdufa and actual_date else "",
                        source_url=src_url,
                    ))
    
    return events
