import argparse
from pathlib import Path
from .config import SOURCES
from .normalize import UNIFIED_FIELDS
from .io_utils import save_json, save_csv
from .multi import fetch_one_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-source FDA calendar scraper (Exa).")
    parser.add_argument("--sources", nargs="+", default=["all"], help="Source names or 'all'")
    parser.add_argument("--livecrawl", default="always", choices=["preferred", "always", "fallback", "never"])
    parser.add_argument("--min-structured", type=int, default=5)
    parser.add_argument("--out-json", default="data/fda_calendar.json")
    parser.add_argument("--out-csv", default="data/fda_calendar.csv")
    parser.add_argument("--save-raw", action="store_true")
    args = parser.parse_args()

    # parse sources
    if len(args.sources) == 1 and args.sources[0].lower() == "all":
        selected = SOURCES
    else:
        sel = set(s.lower() for s in args.sources)
        selected = [s for s in SOURCES if s["name"].lower() in sel]
        if not selected:
            raise SystemExit(f"No matching sources for {args.sources}. Available: {[s['name'] for s in SOURCES]}")

    Path("data").mkdir(exist_ok=True)

    all_unified = []
    for src in selected:
        name, url = src["name"], src["url"]
        print(f"==> Fetching [{name}] {url}")
        page_text, unified = fetch_one_source(name=name, url=url, livecrawl=args.livecrawl, min_structured=args.min_structured)
        print(f"[{name}] unified events: {len(unified)}")

        if args.save_raw:
            raw_path = Path(f"data/{name}_raw.md")
            raw_path.write_text(page_text or "[EMPTY RAW TEXT]", encoding="utf-8")
            print(f"[{name}] wrote raw to: {raw_path.resolve()}")

        # output for every url
        save_json(f"data/{name}.json", {"events": unified})
        save_csv(f"data/{name}.csv", unified, field_order=UNIFIED_FIELDS)

        all_unified.append(unified)

    # combine
    from .combine import merge_and_dedupe
    merged = merge_and_dedupe(all_unified)
    print(f"==> Total merged events: {len(merged)}")

    save_json(args.out_json, {"events": merged})
    save_csv(args.out_csv, merged, field_order=UNIFIED_FIELDS)
    print(f"Wrote: {args.out_json}, {args.out_csv}")


if __name__ == "__main__":
    main()
