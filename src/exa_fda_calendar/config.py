SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "company": {"type": "string"},
                    "ticker": {"type": "string"},
                    "drug": {"type": "string"},
                    "event_type": {"type": "string"},
                    "notes": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["source_url"],
            },
        }
    },
    "required": ["events"],
}

QUERY = "Extract FDA/catalyst calendar events as JSON following the provided schema."

SOURCES = [
    # 1 CheckRare 
    {"name": "checkrare_pdufa_2025", "url": "https://checkrare.com/2025-orphan-drugs-pdufa-dates-and-fda-approvals/", "parser": "checkrare"},
    # 2 FDA.gov
    {"name": "fda_advisory_calendar", "url": "https://www.fda.gov/advisory-committees/advisory-committee-calendar", "parser": "fda_gov"},
    # 3 Benzinga
    {"name": "benzinga_exact", "url": "https://www.benzinga.com/fda-calendar/exact-dates", "parser": "benzinga"},
    # 4 UnusualWhales
    {"name": "unusualwhales", "url": "https://unusualwhales.com/fda-calendar", "parser": "unusual"},
    # 5 RTTNews
    {"name": "rttnews_page6", "url": "https://www.rttnews.com/corpinfo/fdacalendar.aspx?PageNum=6", "parser": "rttnews"},
    # 6 BioPharmCatalyst
    {"name": "biopharmcatalyst", "url": "https://www.biopharmcatalyst.com/calendars/fda-calendar", "parser": "bpc"},
    # 7 FDATracker
    {"name": "fdatracker", "url": "https://www.fdatracker.com/fda-calendar/", "parser": "fdatracker"},
    # 8/9 BP IQ（need login?）
    {"name": "bpiq_pdufa", "url": "https://app.bpiq.com/pdufa-calendar", "parser": "bpiq"},
    {"name": "bpiq_catalyst", "url": "https://app.bpiq.com/catalyst-calendar", "parser": "bpiq"},
]

UNIFIED_FIELDS = ["drug", "indication", "company", "pdufa_date", "fda_date_no_pdufa", "source_url"]
