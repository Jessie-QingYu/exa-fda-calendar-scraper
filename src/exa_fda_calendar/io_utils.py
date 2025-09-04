import json
import csv
from typing import Any, Dict, List

def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)

def save_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fields = ["date", "company", "ticker", "drug", "event_type", "notes", "source_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            record = {k: r.get(k, "") for k in fields}
            if not record.get("source_url"):
                record["source_url"] = ""
            writer.writerow(record)
