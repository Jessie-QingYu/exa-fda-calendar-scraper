# FDA Calendar Parsers

This directory contains modular parsers for different FDA calendar sources. Each parser is designed to handle the specific format and structure of its respective source.

## Structure

- `base.py` - Common utilities and base parsing functions
- `main.py` - Main dispatcher that routes to appropriate parsers
- `unusualwhales.py` - Parser for UnusualWhales FDA calendar
- `biopharmcatalyst.py` - Parser for BioPharmCatalyst FDA calendar
- `benzinga.py` - Parser for Benzinga FDA exact dates
- `checkrare.py` - Parser for CheckRare PDUFA dates and FDA approvals
- `fda_advisory.py` - Parser for FDA Advisory Committee Calendar
- `bpiq.py` - Parser for BP IQ PDUFA/Catalyst calendar
- `fdatracker.py` - Parser for FDATracker FDA calendar
- `rttnews.py` - Parser for RTTNews FDA calendar

## Usage

```python
from exa_fda_calendar.parsers import parse_by_name

# Parse data from any supported source
events = parse_by_name('unusualwhales', page_text, source_url)
```

## Supported Sources

- `unusualwhales` - UnusualWhales FDA calendar
- `biopharmcatalyst` or `bpc` - BioPharmCatalyst FDA calendar
- `benzinga` - Benzinga FDA exact dates
- `checkrare` - CheckRare PDUFA dates and FDA approvals
- `fda_advisory` or `fda_gov` - FDA Advisory Committee Calendar
- `bpiq` - BP IQ PDUFA/Catalyst calendar
- `fdatracker` - FDATracker FDA calendar
- `rttnews` - RTTNews FDA calendar

## Data Format

All parsers return a list of dictionaries with the following unified schema:

```python
{
    "drug": str,           # Drug name
    "indication": str,     # Indication/condition
    "company": str,        # Company name
    "pdufa_date": str,     # PDUFA date (YYYY-MM-DD format)
    "fda_date_no_pdufa": str,  # Other FDA date (YYYY-MM-DD format)
    "source_url": str      # Source URL
}
```

## Adding New Parsers

1. Create a new file in this directory (e.g., `newsource.py`)
2. Implement a `parse_newsource(page_text: str, source_url: str) -> List[Dict]` function
3. Add the import and mapping in `main.py`
4. Update the `__init__.py` file to export the new function

## Testing

Each parser has been tested with actual raw data from the respective sources to ensure accurate parsing of the specific formats used by each site.
