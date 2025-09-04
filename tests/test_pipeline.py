from exa_fda_calendar.pipeline import run_pipeline
from exa_fda_calendar.config import SCHEMA

SAMPLE_TEXT = """
Oct 15, 2025  Acme Therapeutics (ACME)  PDUFA for ATX-101 in migraine
November 3, 2025  BetaBio Inc. (BBIO)  AdComm for BB-22 for oncology
"""

def test_pipeline_uses_fallback_when_structured_too_small(monkeypatch):
    # Simulate extractor returning 0 structured events, but with raw page text
    def fake_fetch(url, schema, query, livecrawl="preferred"):
        return SAMPLE_TEXT, []  # (page_text, structured_events)

    # Patch the function run_pipeline calls internally
    from exa_fda_calendar import extractor
    monkeypatch.setattr(extractor, "fetch_text_and_structured", fake_fetch)

    page_text, events = run_pipeline(
        url="https://example.com",
        schema=SCHEMA,
        query="Extract all events",
        livecrawl="preferred",
        min_structured=5,  # so 0 triggers fallback
    )

    assert page_text.strip()
    assert len(events) >= 2   # fallback should find 2+ events

def test_pipeline_keeps_structured_when_enough(monkeypatch):
    # Simulate extractor returning enough structured events
    structured_events = [
        {
            "date": "2025-10-15",
            "company": "Acme Therapeutics",
            "ticker": "ACME",
            "drug": "ATX-101",
            "event_type": "PDUFA",
            "notes": "Structured entry",
            "source_url": "https://example.com"
        },
        {
            "date": "2025-11-03",
            "company": "BetaBio Inc.",
            "ticker": "BBIO",
            "drug": "BB-22",
            "event_type": "AdComm",
            "notes": "Structured entry 2",
            "source_url": "https://example.com"
        },
        {
            "date": "2025-12-01",
            "company": "Gamma Pharma",
            "ticker": "GMPH",
            "drug": "GP-10",
            "event_type": "Approval",
            "notes": "Structured entry 3",
            "source_url": "https://example.com"
        },
        {
            "date": "2026-01-10",
            "company": "Delta Bio",
            "ticker": "DBIO",
            "drug": "DX-9",
            "event_type": "CRL",
            "notes": "Structured entry 4",
            "source_url": "https://example.com"
        },
        {
            "date": "2026-02-05",
            "company": "Epsilon Health",
            "ticker": "EPSN",
            "drug": "EH-1",
            "event_type": "Readout",
            "notes": "Structured entry 5",
            "source_url": "https://example.com"
        },
    ]

    def fake_fetch(url, schema, query, livecrawl="preferred"):
        return "RAW TEXT IGNORED", structured_events

    from exa_fda_calendar import extractor
    monkeypatch.setattr(extractor, "fetch_text_and_structured", fake_fetch)

    # min_structured=5: since we have 5 structured items already, fallback should not run
    page_text, events = run_pipeline(
        url="https://example.com",
        schema=SCHEMA,
        query="Extract all events",
        livecrawl="preferred",
        min_structured=5,
    )

    assert len(events) == 5
    # Ensure that these are exactly the structured events we provided
    assert events[0]["company"] == "Acme Therapeutics"
    assert events[-1]["company"] == "Epsilon Health"
