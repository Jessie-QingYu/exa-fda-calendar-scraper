import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like

def parse_fda_gov(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse FDA Advisory Committee Calendar
    Based on actual data structure from fda_advisory_calendar_raw.md
    """
    events: List[Dict] = []
    
    # Look for the main table in the content
    lines = page_text.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the table section
        if '| Start Date | End Date | Meeting | Contributing Office | Center |' in line:
            in_table = True
            continue
            
        if in_table and line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 6:
                start_date = parts[1]
                end_date = parts[2]
                meeting = parts[3]
                contributing_office = parts[4]
                center = parts[5]
                
                # Use start date as the primary date
                clean_date = ""
                if start_date and start_date != "—":
                    clean_date = _iso_date_like(start_date)
                
                # Use meeting name as indication/topic
                indication = meeting if meeting else ""
                
                # Extract company from contributing office or center if available
                company = ""
                if contributing_office:
                    company = contributing_office
                elif center:
                    company = center
                
                if clean_date:
                    events.append(_mk_unified(
                        drug="",
                        indication=indication,
                        company=company,
                        pdufa_date="",
                        fda_no_pdufa=clean_date,
                        source_url=source_url,
                    ))
    
    return events
