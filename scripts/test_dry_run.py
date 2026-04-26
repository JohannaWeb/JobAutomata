#!/usr/bin/env python3
"""Smoke-test the dry-run workflow without submitting applications."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from auto_apply import JobApplicationAutomata
from linkedin_hunter import LinkedInManager
from run import build_workflow
from url_scraper import URLScraper


def test_url_scraper() -> None:
    print("\nTEST 1: URL scraper")
    scraper = URLScraper()
    for company in ["Anthropic", "OpenAI", "Protocol Labs"]:
        result = scraper.scrape_company(company)
        print(json.dumps(result, indent=2))


def test_auto_apply_dry_run() -> None:
    print("\nTEST 2: auto_apply dry run")
    test_csv = Path("test_companies.csv")
    with test_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "category", "url", "careers_url", "job_board", "description", "applied"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "name": "Anthropic",
                    "category": "AI",
                    "url": "https://anthropic.com",
                    "careers_url": "https://anthropic.com/careers",
                    "job_board": "custom",
                    "description": "AI safety",
                    "applied": "False",
                },
                {
                    "name": "Protocol Labs",
                    "category": "Web3",
                    "url": "https://protocol.ai",
                    "careers_url": "https://protocol.ai/join",
                    "job_board": "custom",
                    "description": "decentralized infrastructure",
                    "applied": "False",
                },
            ]
        )

    try:
        automata = JobApplicationAutomata(headless=True, delay_seconds=0)
        automata.load_companies_from_csv(str(test_csv))
        print(f"Loaded {len(automata.companies)} companies")
        for company in automata.companies:
            print(f"- {company.name}: {company.job_board}")
    finally:
        test_csv.unlink(missing_ok=True)


def test_linkedin_hunter_shape() -> None:
    print("\nTEST 3: LinkedIn manager data shape")
    manager = LinkedInManager(
        name="Jane Smith",
        title="Engineering Manager",
        company="Anthropic",
        url="https://linkedin.com/in/janesmith",
        email="jane.smith@example.com",
        department="Engineering",
        location="San Francisco, CA",
        found_date="2026-04-26T10:00:00",
    )
    print(manager)


def test_orchestrator() -> None:
    print("\nTEST 4: Orchestrator structure")
    workflow = build_workflow(mode="test")
    for index, step in enumerate(workflow.steps, start=1):
        print(f"{index}. {step['name']}: {' '.join(step['command'])}")


def main() -> int:
    try:
        test_url_scraper()
        test_auto_apply_dry_run()
        test_linkedin_hunter_shape()
        test_orchestrator()
        print("\nDry-run smoke tests completed.")
        return 0
    except Exception as exc:
        print(f"\nError during dry-run smoke test: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
