import re
import csv
from io import StringIO
from datetime import datetime
from typing import List, Dict

# -------------------------
# Helpers
# -------------------------

def _clean_markdown_link(value: str) -> (str, str): # type: ignore
    """
    Parse [text](url) markdown link.
    Returns (text, url). If not a link, returns (value, "").
    """
    m = re.match(r"\[(.*?)\]\((.*?)\)", value.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return value.strip(), ""

# -------------------------
# Markdown table parser
# -------------------------
def parse_markdown_table(text: str, source_url: str) -> List[Dict]:
    """
    Detect and parse markdown-style tables with pipe '|' delimiters.
    Returns a list of event dicts.
    """
    events: List[Dict] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if not lines:
        return events

    # remove leading/trailing pipes
    clean_lines = [ln.strip("| ") for ln in lines]
    sio = StringIO("\n".join(clean_lines))
    reader = csv.reader(sio, delimiter="|")
    rows = [list(map(str.strip, r)) for r in reader]

    # find header row
    header_idx = None
    for i, row in enumerate(rows):
        if any("Ticker" in c for c in row):
            header_idx = i
            break
    if header_idx is None:
        return events

    headers = rows[header_idx]
    for row in rows[header_idx + 1 :]:
        if len(row) < len(headers):
            continue
        rec = dict(zip(headers, row))
        if not rec.get("Ticker") or rec.get("Ticker") == "---":
            continue

        # --- ticker ---
        raw_ticker = rec.get("Ticker", "")
        ticker, ticker_url = _clean_markdown_link(raw_ticker)

        # --- drug ---
        drug = rec.get("Drug") or ""

        # --- event type ---
        event_type = rec.get("Event Type") or ""

        # --- notes/outcome ---
        notes = rec.get("Outcome") or ""
        # try to extract company before first comma
        company = ""
        if notes and "," in notes:
            company = notes.split(",", 1)[0].strip()

        # --- date ---
        date = rec.get("Date") or rec.get("Target Date") or ""

        # --- source link ---
        raw_src = rec.get("Source Link") or source_url
        _, src_url = _clean_markdown_link(raw_src)
        if not src_url:
            src_url = source_url

        events.append(
            {
                "date": date,
                "company": company,
                "ticker": ticker,
                "drug": drug,
                "event_type": event_type,
                "notes": notes,
                "source_url": src_url,
            }
        )
    return events

# -------------------------
# Regex-based fallback parser (kept as backup)
# -------------------------

MONTHS = (
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

DATE_PAT = re.compile(
    rf"(?P<iso>\d{{4}}-\d{{2}}-\d{{2}})"
    rf"|(?P<mdy1>{MONTHS}\s+\d{{1,2}}(?:,\s*\d{{4}})?)"
    rf"|(?P<mdy2>\d{{1,2}}/\d{{1,2}}(?:/\d{{2,4}})?)",
    re.IGNORECASE,
)

TICKER_PAT = re.compile(r"\(([A-Z]{1,5})\)")
EVENT_KEYWORDS = [
    "PDUFA", "ADCOMM", "AD COMM", "ADVISORY", "READOUT",
    "APPROVAL", "CRL", "PHASE", "TRIAL", "MEETING", "DECISION"
]

def _try_parse_dt(s: str, fmts: List[str]) -> str:
    for fmt in fmts:
        try:
            d = datetime.strptime(s, fmt)
            return d.strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""

def normalize_date(s: str) -> str:
    s = s.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    out = _try_parse_dt(s, ["%B %d, %Y", "%b %d, %Y"])
    if out:
        return out
    out = _try_parse_dt(s, ["%B %d", "%b %d"])
    if out:
        y = datetime.utcnow().year
        return f"{y}{out[4:]}"
    if re.fullmatch(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?", s):
        parts = s.split("/")
        m = int(parts[0]); d = int(parts[1])
        if len(parts) == 3:
            y = int(parts[2])
            if y < 100:
                y += 2000
        else:
            y = datetime.utcnow().year
        try:
            return datetime(y, m, d).strftime("%Y-%m-%d")
        except Exception:
            return s
    return s

def guess_event_type(text: str) -> str:
    u = text.upper()
    for kw in EVENT_KEYWORDS:
        if kw in u:
            return "AdComm" if kw == "AD COMM" else kw.title()
    return ""

def _split_lines(text: str) -> List[str]:
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if "|" in ln and ln.count("|") >= 2:
            parts = [p.strip() for p in ln.split("|") if p.strip()]
            if len(parts) >= 2:
                lines.extend(parts)
                continue
        if ln.startswith(("-", "*", "•")):
            ln = ln.lstrip("-*• ").strip()
        lines.append(ln)
    return lines

def regex_parse_events(page_text: str, source_url: str) -> List[Dict]:
    events: List[Dict] = []
    lines = _split_lines(page_text)
    n = len(lines)
    for i, ln in enumerate(lines):
        m = DATE_PAT.search(ln)
        if not m:
            continue
        raw_date = m.group("iso") or m.group("mdy1") or m.group("mdy2")
        date_str = normalize_date(raw_date)

        j = min(i + 6, n)
        context = " ".join(lines[i:j])

        tick = ""
        m2 = TICKER_PAT.search(context)
        if m2:
            tick = m2.group(1)

        company = ""
        after_date = context.split(raw_date, 1)[-1] if raw_date in context else context
        if "(" in after_date:
            company = after_date.split("(", 1)[0].strip(" -—:|,")
        elif "," in after_date:
            company = after_date.split(",", 1)[0].strip(" -—:|")
        else:
            if i + 1 < n:
                company = lines[i + 1].split("(")[0].strip(" -—:|,")
        company = re.sub(r"\s{2,}", " ", company)

        event_type = guess_event_type(context)
        drug = ""
        m3 = re.search(r"\bfor\s+([A-Za-z0-9 \-/]+)", context, re.IGNORECASE)
        if m3:
            drug = m3.group(1).strip(" -—:|,.;")

        notes = re.sub(r"\s{2,}", " ", context)[:240]

        if date_str and (company or tick):
            events.append({
                "date": date_str,
                "company": company,
                "ticker": tick,
                "drug": drug,
                "event_type": event_type or "Event",
                "notes": notes,
                "source_url": source_url
            })
    # dedup
    seen = set()
    out: List[Dict] = []
    for ev in events:
        key = (ev.get("date",""), ev.get("company","").lower(), ev.get("ticker",""), ev.get("event_type","").lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out

# -------------------------
# Unified entry point
# -------------------------
def fallback_parse_events(page_text: str, source_url: str) -> List[Dict]:
    # 1) Try markdown table
    events = parse_markdown_table(page_text, source_url)
    if events:
        return events
    # 2) Fall back to regex parsing
    return regex_parse_events(page_text, source_url)



# import re
# import csv
# from io import StringIO
# from datetime import datetime
# from typing import List, Dict

# # -------------------------
# # Markdown table parser
# # -------------------------
# def parse_markdown_table(text: str, source_url: str) -> List[Dict]:
#     """
#     Detect and parse markdown-style tables with pipe '|' delimiters.
#     Returns a list of event dicts.
#     """
#     events: List[Dict] = []
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
#     if not lines:
#         return events

#     # remove leading/trailing pipes
#     clean_lines = [ln.strip("| ") for ln in lines]
#     sio = StringIO("\n".join(clean_lines))
#     reader = csv.reader(sio, delimiter="|")
#     rows = [list(map(str.strip, r)) for r in reader]

#     # find header row
#     header_idx = None
#     for i, row in enumerate(rows):
#         if any("Ticker" in c for c in row):
#             header_idx = i
#             break
#     if header_idx is None:
#         return events

#     headers = rows[header_idx]
#     for row in rows[header_idx + 1 :]:
#         if len(row) < len(headers):
#             continue
#         rec = dict(zip(headers, row))
#         if not rec.get("Ticker") or rec.get("Ticker") == "---":
#             continue
#         events.append(
#             {
#                 "date": rec.get("Date") or rec.get("Target Date") or "",
#                 "company": "",  # not always available in table
#                 "ticker": rec.get("Ticker"),
#                 "drug": rec.get("Drug"),
#                 "event_type": rec.get("Event Type"),
#                 "notes": rec.get("Outcome") or "",
#                 "source_url": rec.get("Source Link") or source_url,
#             }
#         )
#     return events

# # -------------------------
# # Regex-based fallback parser
# # -------------------------

# MONTHS = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|" \
#          r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

# DATE_PAT = re.compile(
#     rf"(?P<iso>\d{{4}}-\d{{2}}-\d{{2}})"
#     rf"|(?P<mdy1>{MONTHS}\s+\d{{1,2}}(?:,\s*\d{{4}})?)"
#     rf"|(?P<mdy2>\d{{1,2}}/\d{{1,2}}(?:/\d{{2,4}})?)",
#     re.IGNORECASE,
# )


# TICKER_PAT = re.compile(r"\(([A-Z]{1,5})\)")
# EVENT_KEYWORDS = [
#     "PDUFA", "ADCOMM", "AD COMM", "ADVISORY", "READOUT",
#     "APPROVAL", "CRL", "PHASE", "TRIAL", "MEETING", "DECISION"
# ]

# def _try_parse_dt(s: str, fmts: List[str]) -> str:
#     for fmt in fmts:
#         try:
#             d = datetime.strptime(s, fmt)
#             return d.strftime("%Y-%m-%d")
#         except Exception:
#             pass
#     return ""

# def normalize_date(s: str) -> str:
#     s = s.strip()
#     if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
#         return s
#     out = _try_parse_dt(s, ["%B %d, %Y", "%b %d, %Y"])
#     if out:
#         return out
#     out = _try_parse_dt(s, ["%B %d", "%b %d"])
#     if out:
#         y = datetime.utcnow().year
#         return f"{y}{out[4:]}"
#     if re.fullmatch(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?", s):
#         parts = s.split("/")
#         m = int(parts[0]); d = int(parts[1])
#         if len(parts) == 3:
#             y = int(parts[2])
#             if y < 100:
#                 y += 2000
#         else:
#             y = datetime.utcnow().year
#         try:
#             return datetime(y, m, d).strftime("%Y-%m-%d")
#         except Exception:
#             return s
#     return s

# def guess_event_type(text: str) -> str:
#     u = text.upper()
#     for kw in EVENT_KEYWORDS:
#         if kw in u:
#             return "AdComm" if kw == "AD COMM" else kw.title()
#     return ""

# def _split_lines(text: str) -> List[str]:
#     lines = []
#     for ln in text.splitlines():
#         ln = ln.strip()
#         if not ln:
#             continue
#         if "|" in ln and ln.count("|") >= 2:
#             parts = [p.strip() for p in ln.split("|") if p.strip()]
#             if len(parts) >= 2:
#                 lines.extend(parts)
#                 continue
#         if ln.startswith(("-", "*", "•")):
#             ln = ln.lstrip("-*• ").strip()
#         lines.append(ln)
#     return lines

# def regex_parse_events(page_text: str, source_url: str) -> List[Dict]:
#     events: List[Dict] = []
#     lines = _split_lines(page_text)
#     n = len(lines)
#     for i, ln in enumerate(lines):
#         m = DATE_PAT.search(ln)
#         if not m:
#             continue
#         raw_date = m.group("iso") or m.group("mdy1") or m.group("mdy2")
#         date_str = normalize_date(raw_date)

#         j = min(i + 6, n)
#         context = " ".join(lines[i:j])

#         tick = ""
#         m2 = TICKER_PAT.search(context)
#         if m2:
#             tick = m2.group(1)

#         company = ""
#         after_date = context.split(raw_date, 1)[-1] if raw_date in context else context
#         if "(" in after_date:
#             company = after_date.split("(", 1)[0].strip(" -—:|,")
#         elif "," in after_date:
#             company = after_date.split(",", 1)[0].strip(" -—:|")
#         else:
#             if i + 1 < n:
#                 company = lines[i + 1].split("(")[0].strip(" -—:|,")
#         company = re.sub(r"\s{2,}", " ", company)

#         event_type = guess_event_type(context)
#         drug = ""
#         m3 = re.search(r"\bfor\s+([A-Za-z0-9 \-/]+)", context, re.IGNORECASE)
#         if m3:
#             drug = m3.group(1).strip(" -—:|,.;")

#         notes = re.sub(r"\s{2,}", " ", context)[:240]

#         if date_str and (company or tick):
#             events.append({
#                 "date": date_str,
#                 "company": company,
#                 "ticker": tick,
#                 "drug": drug,
#                 "event_type": event_type or "Event",
#                 "notes": notes,
#                 "source_url": source_url
#             })
#     # dedup
#     seen = set()
#     out: List[Dict] = []
#     for ev in events:
#         key = (ev.get("date",""), ev.get("company","").lower(), ev.get("ticker",""), ev.get("event_type","").lower())
#         if key in seen:
#             continue
#         seen.add(key)
#         out.append(ev)
#     return out

# # -------------------------
# # Unified entry point
# # -------------------------
# def fallback_parse_events(page_text: str, source_url: str) -> List[Dict]:
#     # 1) Try markdown table
#     events = parse_markdown_table(page_text, source_url)
#     if events:
#         return events
#     # 2) Fall back to regex parsing
#     return regex_parse_events(page_text, source_url)




# # import re
# # from datetime import datetime
# # from typing import List, Dict

# # MONTHS = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|" \
# #          r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

# # DATE_PAT = re.compile(
# #     rf"(?P<iso>\d{{4}}-\d{{2}}-\d{{2}})|(?P<mdy>{MONTHS}\s+\d{{1,2}}(?:,\s*\d{{4}})?)",
# #     re.IGNORECASE
# # )
# # TICKER_PAT = re.compile(r"\(([A-Z]{1,5})\)")
# # EVENT_KEYWORDS = ["PDUFA", "ADCOMM", "AD COMM", "ADVISORY", "READOUT", "APPROVAL", "CRL", "PHASE", "TRIAL"]

# # def normalize_date(s: str) -> str:
# #     s = s.strip()
# #     if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
# #         return s
# #     for fmt in ["%B %d, %Y", "%b %d, %Y", "%B %d", "%b %d"]:
# #         try:
# #             d = datetime.strptime(s, fmt)
# #             if "%Y" not in fmt:
# #                 d = d.replace(year=datetime.utcnow().year)
# #             return d.strftime("%Y-%m-%d")
# #         except Exception:
# #             continue
# #     return s

# # def guess_event_type(line: str) -> str:
# #     u = line.upper()
# #     for kw in EVENT_KEYWORDS:
# #         if kw in u:
# #             if kw == "AD COMM":
# #                 return "AdComm"
# #             return kw.title() if kw.isalpha() else kw
# #     return ""

# # def fallback_parse_events(page_text: str, source_url: str) -> List[Dict]:
# #     events: List[Dict] = []
# #     lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
# #     n = len(lines)
# #     for i, ln in enumerate(lines):
# #         m = DATE_PAT.search(ln)
# #         if not m:
# #             continue
# #         raw_date = m.group("iso") or m.group("mdy")
# #         date_str = normalize_date(raw_date)

# #         context = " ".join(lines[i : min(i + 3, n)])
# #         tick = ""
# #         m2 = TICKER_PAT.search(context)
# #         if m2:
# #             tick = m2.group(1)

# #         company = ""
# #         after_date = context.split(raw_date, 1)[-1].strip() if raw_date in context else context
# #         if "(" in after_date:
# #             company = after_date.split("(", 1)[0].strip(" -—:|,")
# #         elif "," in after_date:
# #             company = after_date.split(",", 1)[0].strip(" -—:|")
# #         elif i + 1 < n:
# #             company = lines[i + 1].split("(")[0].strip(" -—:|,")
# #         company = re.sub(r"\s{2,}", " ", company)

# #         event_type = guess_event_type(context)
# #         drug = ""
# #         m3 = re.search(r"\bfor\s+([A-Za-z0-9 \-/]+)", context, re.IGNORECASE)
# #         if m3:
# #             drug = m3.group(1).strip(" -—:|,.;")

# #         notes = context[:220]

# #         if date_str or company or tick:
# #             events.append({
# #                 "date": date_str,
# #                 "company": company,
# #                 "ticker": tick,
# #                 "drug": drug,
# #                 "event_type": event_type or "Event",
# #                 "notes": notes,
# #                 "source_url": source_url
# #             })

# #     # Deduplicate
# #     seen = set()
# #     deduped: List[Dict] = []
# #     for ev in events:
# #         key = (ev.get("date",""), ev.get("company","").lower(), ev.get("ticker",""), ev.get("event_type","").lower())
# #         if key in seen:
# #             continue
# #         seen.add(key)
# #         deduped.append(ev)
# #     return deduped
