# src/exa_fda_calendar/cli.py
import argparse
from pathlib import Path
from .config import TARGET_URL, SCHEMA, QUERY
from .pipeline import run_pipeline
from .io_utils import save_json, save_csv

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape FDA calendar via Exa + fallback parsing.")
    parser.add_argument("--url", default=TARGET_URL, help="Target page URL")
    parser.add_argument("--livecrawl", default="preferred", choices=["preferred", "always", "fallback", "never"], help="Livecrawl mode")
    parser.add_argument("--min-structured", type=int, default=5, help="If structured < N, run fallback parser")
    parser.add_argument("--out-json", default="fda_calendar.json", help="Output JSON path")
    parser.add_argument("--out-csv", default="fda_calendar.csv", help="Output CSV path")
    parser.add_argument("--save-raw", action="store_true", help="Save raw page text to page_raw.md")
    args = parser.parse_args()

    page_text, events = run_pipeline(
        url=args.url,
        schema=SCHEMA,
        query=QUERY,
        livecrawl=args.livecrawl,
        min_structured=args.min_structured,
    )

    print(f"[debug] raw text length: {len(page_text)}")
    if page_text:
        print("[debug] raw text preview:", page_text[:200].replace("\n", " ") + "...")

    if args.save_raw:
        md_path = Path("page_raw.md")
        md_path.write_text(page_text or "[EMPTY RAW TEXT]", encoding="utf-8")
        print(f"[debug] wrote raw text to: {md_path.resolve()}")

    save_json(args.out_json, {"events": events})
    save_csv(args.out_csv, events)
    print(f"Extracted events: {len(events)}")
    wrote = f"Wrote: {args.out_json}, {args.out_csv}"
    if args.save_raw:
        wrote += " and page_raw.md"
    print(wrote)

if __name__ == "__main__":
    main()
