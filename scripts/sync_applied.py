#!/usr/bin/env python3
"""Copy applied state from one companies CSV to another."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


TRUE_VALUES = {"true", "1", "yes", "y", "applied", "submitted"}


def is_true(value: str | None) -> bool:
    return str(value or "").strip().casefold() in TRUE_VALUES


def greenhouse_token(url: str) -> str:
    match = re.search(r"greenhouse\.io/([^/?#]+)", url or "")
    return match.group(1).casefold() if match else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync applied=True rows between companies CSV files")
    parser.add_argument("--source", required=True, help="CSV with known applied state")
    parser.add_argument("--target", required=True, help="CSV to update")
    parser.add_argument(
        "--company-token",
        action="store_true",
        help="Also mark all target rows for a Greenhouse board token if any source row for that token is applied",
    )
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def main() -> int:
    args = parse_args()
    source_rows, _ = read_rows(Path(args.source))
    target_path = Path(args.target)
    target_rows, fieldnames = read_rows(target_path)

    for field in ("applied", "application_date", "notes"):
        if field not in fieldnames:
            fieldnames.append(field)

    applied_by_url = {}
    applied_tokens = {}
    for row in source_rows:
        if not is_true(row.get("applied")):
            continue
        url = row.get("careers_url", "")
        token = greenhouse_token(url)
        state = {
            "application_date": row.get("application_date", ""),
            "notes": row.get("notes", "Synced applied state"),
        }
        if url:
            applied_by_url[url] = state
        if token:
            applied_tokens[token] = state

    changed = 0
    for row in target_rows:
        if is_true(row.get("applied")):
            continue
        state = applied_by_url.get(row.get("careers_url", ""))
        if state is None and args.company_token:
            state = applied_tokens.get(greenhouse_token(row.get("careers_url", "")))
        if state is None:
            continue
        row["applied"] = "True"
        row["application_date"] = state["application_date"]
        row["notes"] = state["notes"] or "Synced applied state"
        changed += 1

    with target_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(target_rows)

    print(f"Synced {changed} applied row(s) from {args.source} to {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
