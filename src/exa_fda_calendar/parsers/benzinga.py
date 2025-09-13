import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like, _clean_link

def parse_benzinga(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse Benzinga FDA exact dates
    Based on actual data structure from benzinga_exact_raw.md
    """
    events: List[Dict] = []
    
    # Look for the main table in the content
    lines = page_text.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the table section
        if '| ticker ▲▼ | Company ▲▼ | Price ▲▼ | % change ▲▼ | Name and Treatment ▲▼ | Status ▲▼ | Catalyst Date ▲▼ | Catalyst ▲▼ | Description ▲▼ | Get Alert |' in line:
            in_table = True
            continue
            
        if in_table and line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 10:
                ticker = parts[1]
                company = parts[2]
                name_treatment = parts[5]
                status = parts[6]
                catalyst_date = parts[7]
                catalyst = parts[8]
                description = parts[9]
                
                # Skip header row and separator rows
                if ticker in ['ticker ▲▼', '---'] or company in ['Company ▲▼', '---']:
                    continue
                
                # Extract drug name from name_treatment field
                drug = ""
                if name_treatment:
                    # Look for drug name in bold format **Drug Name**
                    drug_match = re.search(r'\*\*(.*?)\*\*', name_treatment)
                    if drug_match:
                        drug = drug_match.group(1).strip()
                    else:
                        # Fallback: take the first part before any indication
                        drug = name_treatment.split(' ')[0] if name_treatment else ""
                
                # Extract indication from name_treatment field
                indication = ""
                if name_treatment and drug:
                    # Remove the drug name and clean up
                    indication_part = name_treatment.replace(f"**{drug}**", "").strip()
                    if indication_part:
                        indication = indication_part
                
                # Determine if this is a PDUFA event
                is_pdufa = "pdufa" in catalyst.lower() or "pdufa" in status.lower()
                
                # Clean catalyst date
                clean_date = ""
                if catalyst_date and catalyst_date != "—":
                    clean_date = _iso_date_like(catalyst_date)
                
                if any([drug, clean_date, company]):
                    events.append(_mk_unified(
                        drug=drug,
                        indication=indication,
                        company=company,
                        pdufa_date=clean_date if is_pdufa else "",
                        fda_no_pdufa=clean_date if not is_pdufa else "",
                        source_url=source_url,
                    ))
    
    return events
