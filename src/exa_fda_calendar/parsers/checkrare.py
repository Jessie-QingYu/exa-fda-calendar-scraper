import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like

def parse_checkrare(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse CheckRare PDUFA dates and FDA approvals
    Based on actual data structure from checkrare_pdufa_2025_raw.md
    """
    events: List[Dict] = []
    
    # Look for the main table in the content
    lines = page_text.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the table section
        if '| PDUFA Date | Orphan Drug | Indication | Company | Status |' in line:
            in_table = True
            continue
            
        if in_table and line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 6:
                pdufa_date = parts[1]
                orphan_drug = parts[2]
                indication = parts[3]
                company = parts[4]
                status = parts[5]
                
                # Skip header row and separator rows
                if pdufa_date in ['PDUFA Date', '---'] or orphan_drug in ['Orphan Drug', '---']:
                    continue
                
                # Clean up drug name (remove any markdown links)
                drug = orphan_drug
                if drug:
                    # Remove markdown links [text](url) -> text
                    drug = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', drug)
                    drug = drug.strip()
                
                # Clean up company name
                if company:
                    company = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', company)
                    company = company.strip()
                
                # Clean up indication
                if indication:
                    indication = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', indication)
                    indication = indication.strip()
                
                # Clean PDUFA date - extract just the date part
                clean_date = ""
                if pdufa_date and pdufa_date != "—":
                    # Extract date from markdown link format [date](url)
                    date_match = re.search(r'\[([^\]]+)\]\([^)]+\)', pdufa_date)
                    if date_match:
                        clean_date = _iso_date_like(date_match.group(1))
                    else:
                        clean_date = _iso_date_like(pdufa_date)
                
                if any([drug, clean_date, company]):
                    events.append(_mk_unified(
                        drug=drug,
                        indication=indication,
                        company=company,
                        pdufa_date=clean_date,
                        fda_no_pdufa="",
                        source_url=source_url,
                    ))
    
    return events
