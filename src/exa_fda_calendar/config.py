from typing import Any, Dict

TARGET_URL = "https://unusualwhales.com/fda-calendar"

QUERY = (
    "Extract ALL FDA calendar entries visible on this page. "
    "Return every row/item (do not summarize). "
    "For each event, capture: date (YYYY-MM-DD if possible), company, ticker (if any), "
    "drug (if any), event_type (e.g., PDUFA, AdComm, Approval, CRL, data readout), "
    "notes (10-40 words), source_url (set to page URL if none on the row)."
)

SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "FDAEvents",
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date":       {"type": "string", "description": "YYYY-MM-DD if available"},
                    "company":    {"type": "string"},
                    "ticker":     {"type": "string"},
                    "drug":       {"type": "string"},
                    "event_type": {"type": "string"},
                    "notes":      {"type": "string"},
                    "source_url": {"type": "string"}
                },
                "required": ["company", "event_type"]
            }
        }
    },
    "required": ["events"]
}
