import re
from typing import List, Dict
from .base import _mk_unified, _iso_date_like

def parse_bpiq(page_text: str, source_url: str) -> List[Dict]:
    """
    Parse BP IQ (PDUFA/Catalyst calendar) - requires login
    Based on actual data structure from bpiq_catalyst_raw.md and bpiq_pdufa_raw.md
    """
    events: List[Dict] = []
    
    # Since the raw data shows mostly login prompts and limited content,
    # we'll implement a basic parser that looks for any structured data
    
    lines = page_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Look for any date patterns that might indicate events
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{4}-\d{2}-\d{2})',       # YYYY-MM-DD
            r'([A-Z][a-z]{2,9}\s+\d{1,2},\s*\d{4})',  # Month dd, yyyy
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group(1)
                clean_date = _iso_date_like(date_str)
                
                if clean_date:
                    # Try to extract additional context from the line
                    indication = ""
                    company = ""
                    
                    # Look for common biotech terms
                    biotech_terms = ['pdufa', 'fda', 'approval', 'clinical', 'trial', 'drug', 'therapy']
                    if any(term in line.lower() for term in biotech_terms):
                        indication = line[:100]  # Use first 100 chars as context
                    
                    events.append(_mk_unified(
                        drug="",
                        indication=indication,
                        company=company,
                        pdufa_date=clean_date if "pdufa" in line.lower() else "",
                        fda_no_pdufa=clean_date if "pdufa" not in line.lower() else "",
                        source_url=source_url,
                    ))
                break
    
    return events
