from exa_fda_calendar.fallback_parser import fallback_parse_events

SAMPLE_TEXT = """
Upcoming FDA Calendar
Oct 15, 2025  Acme Therapeutics (ACME)  PDUFA for ATX-101 in migraine
Notes: final review expected around mid-October.
Another line that is not relevant.

November 3, 2025  BetaBio Inc. (BBIO)  AdComm for BB-22 for oncology
Likely panel discussion; outcome could shift timelines.
"""

def test_fallback_parser_extracts_multiple_events():
    events = fallback_parse_events(SAMPLE_TEXT, "https://example.com/page")
    assert isinstance(events, list)
    assert len(events) >= 2

    # Check first event fields are present & sane
    ev = events[0]
    assert "date" in ev and ev["date"]  # should be normalized to YYYY-MM-DD if possible
    assert "company" in ev and ev["company"]
    assert "ticker" in ev and ev["ticker"] in ("ACME", "BBIO")
    assert "event_type" in ev and ev["event_type"]
    assert "source_url" in ev and ev["source_url"] == "https://example.com/page"
