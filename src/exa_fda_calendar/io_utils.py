import json
import csv
from typing import Any, Dict, List, Optional


def save_json(path: str, data: Dict[str, Any]) -> None:
    """Write JSON with stable formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)


def save_csv(path: str, rows: List[Dict[str, Any]], field_order: Optional[List[str]] = None) -> None:
    """
    Save rows to CSV.
    """
    # headers
    if field_order:
        headers = list(field_order)
    else:
        if rows:
            # combine key
            keys = set()
            for r in rows:
                keys.update(r.keys())
            headers = sorted(keys)
        else:
            headers = []

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows or []:
            writer.writerow({k: r.get(k, "") for k in headers})
