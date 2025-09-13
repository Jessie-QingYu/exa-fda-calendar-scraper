import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like, _clean_link

def parse_bpc(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse BioPharmCatalyst FDA calendar
    Based on actual data structure from biopharmcatalyst_raw.md
    """
    events: List[Dict] = []
    
    # Look for the main table in the content
    lines = page_text.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the table section
        if '| Ticker | Name | Price % $ | 30 Day Price Change | Drug | NCT Number | Indication | Stage | Status | Options | Next Catalyst | Catalyst Date | Catalyst | Conference | Historical LOA | Historical POP | Bullish or Bearish | Last Updated |' in line:
            in_table = True
            continue
            
        if in_table and line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 18:
                ticker = parts[1]
                name = parts[2]
                drug = parts[5]
                indication = parts[7]
                stage = parts[8]
                catalyst_date = parts[12]
                catalyst = parts[13]
                
                # Skip header row and separator rows
                if ticker in ['Ticker', '---'] or name in ['Name', '---']:
                    continue
                
                # Extract company name from the name field (remove logo info)
                company = ""
                if name:
                    # Remove any image references and clean up
                    company = re.sub(r'!\[.*?\]\(.*?\)', '', name).strip()
                    # Remove any HTML-like content
                    company = re.sub(r'<[^>]+>', '', company).strip()
                
                # Clean up drug name
                if drug:
                    # Remove markdown links and clean up
                    drug = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', drug)
                    drug = re.sub(r'\*\*(.*?)\*\*', r'\1', drug)  # Remove bold formatting
                    drug = drug.strip()
                
                # Clean up indication
                if indication:
                    indication = indication.strip()
                
                # Determine if this is a PDUFA event
                is_pdufa = "pdufa" in stage.lower() or "pdufa" in catalyst.lower()
                
                # Clean catalyst date - extract date from markdown link
                clean_date = ""
                if catalyst_date and catalyst_date != "—":
                    # Extract date from markdown link format [date](url)
                    date_match = re.search(r'\[([^\]]+)\]\([^)]+\)', catalyst_date)
                    if date_match:
                        clean_date = _iso_date_like(date_match.group(1))
                    else:
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
