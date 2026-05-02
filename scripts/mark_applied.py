#!/usr/bin/env python3
"""Mark companies as applied in a companies CSV."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark rows as applied in a companies CSV")
    parser.add_argument("--csv", required=True, help="Companies CSV to update")
    parser.add_argument("--first", type=int, help="Mark the first N rows as applied")
    parser.add_argument("--name", action="append", default=[], help="Company name to mark as applied")
    parser.add_argument("--note", default="Marked applied manually", help="Note to write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.csv)
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not fieldnames:
        raise SystemExit(f"No CSV header found in {path}")

    for field in ("applied", "application_date", "notes"):
        if field not in fieldnames:
            fieldnames.append(field)

    names = {name.casefold() for name in args.name}
    now = datetime.now().isoformat()
    changed = 0
    for index, row in enumerate(rows, start=1):
        should_mark = bool(args.first and index <= args.first) or row.get("name", "").casefold() in names
        if not should_mark:
            continue
        row["applied"] = "True"
        row["application_date"] = row.get("application_date") or now
        row["notes"] = args.note
        changed += 1

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Marked {changed} row(s) applied in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
