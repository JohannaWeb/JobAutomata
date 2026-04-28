#!/usr/bin/env python3
"""
Job application automation entry point.

The script keeps the original workflow surface area:
- --init creates profile/companies templates
- --dry-run generates planned application rows without submitting
- non-dry-run preserves the original Selenium click-through behavior

This is a refactor of the original prototype, not a product rewrite.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from job_automata.config import APPLICATIONS_DIR, DEFAULT_COMPANIES, DEFAULT_PROFILE, DEFAULT_TARGET_COMPANIES, LOG_DIR
from job_automata.domain import Company, JobSearchCriteria, normalize_text
from job_automata.infrastructure.ats import fill_application_form
from job_automata.infrastructure.job_boards import get_job_board_handler, select_job
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

try:
    from cover_letter_ai import generate_cover_letter_ai
except ImportError:
    generate_cover_letter_ai = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[],
)
logger = logging.getLogger(__name__)
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.addHandler(logging.FileHandler(LOG_DIR / "job_applications.log"))
logger.addHandler(logging.StreamHandler())


class JobApplicationAutomata:
    """Loads targets, generates application material, and records run results."""

    TEXT_RESUME_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}

    def __init__(self, headless: bool = True, delay_seconds: int = 3, pause_each: bool = False):
        self.delay = delay_seconds
        self.headless = headless and not pause_each
        self.pause_each = pause_each
        self.companies: list[Company] = []
        self.results: list[dict[str, Any]] = []
        self.profile_path = DEFAULT_PROFILE
        self.companies_csv_path: Path | None = None

    def _setup_chrome_options(self) -> Options:
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        return options

    def load_companies_from_csv(self, csv_path: str) -> None:
        self.companies_csv_path = Path(csv_path)
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            self.companies = [
                Company(
                    name=row.get("name", "").strip(),
                    category=row.get("category", "").strip(),
                    url=row.get("url", "").strip(),
                    careers_url=row.get("careers_url", "").strip(),
                    job_board=row.get("job_board", "").strip(),
                    description=row.get("description", "").strip(),
                    applied=row.get("applied", "False") == "True",
                    application_date=row.get("application_date", "").strip(),
                    notes=row.get("notes", "").strip(),
                )
                for row in reader
                if row.get("name", "").strip()
            ]
        logger.info("Loaded %s companies from %s", len(self.companies), csv_path)

    def save_companies_to_csv(self) -> None:
        if self.companies_csv_path is None:
            logger.warning("No source CSV path recorded; skipping company state update")
            return

        fieldnames = [
            "name",
            "category",
            "url",
            "careers_url",
            "job_board",
            "description",
            "applied",
            "application_date",
            "notes",
        ]
        with self.companies_csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for company in self.companies:
                writer.writerow(
                    {
                        "name": company.name,
                        "category": company.category,
                        "url": company.url,
                        "careers_url": company.careers_url,
                        "job_board": company.job_board,
                        "description": company.description,
                        "applied": str(company.applied),
                        "application_date": company.application_date,
                        "notes": company.notes,
                    }
                )
        logger.info("Updated company state in %s", self.companies_csv_path)

    def load_application_profile(self) -> dict[str, Any]:
        if not self.profile_path.exists():
            logger.error("Profile file %s not found", self.profile_path)
            return {}

        with self.profile_path.open() as f:
            profile = json.load(f)

        resume_file = profile.get("resume_file")
        if resume_file:
            resume_path = Path(resume_file)
            if not resume_path.is_absolute():
                resume_path = DEFAULT_PROFILE.parent / resume_path
            if resume_path.exists():
                profile["resume_path"] = str(resume_path)
                resume_content = self._read_resume_text(resume_path)
                if resume_content:
                    profile["resume_content"] = resume_content
                    logger.info("Loaded resume text from %s", resume_path)
                else:
                    logger.info("Using resume file %s without text extraction", resume_path)

        return profile

    @classmethod
    def _read_resume_text(cls, resume_path: Path) -> str:
        if resume_path.suffix.lower() not in cls.TEXT_RESUME_SUFFIXES:
            return ""

        try:
            return resume_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Resume %s is not UTF-8; decoding with replacement characters", resume_path)
            return resume_path.read_text(encoding="utf-8", errors="replace")

    def generate_cover_letter(
        self,
        company: Company,
        profile: dict[str, Any],
        category: str | None = None,
    ) -> str:
        if generate_cover_letter_ai is not None:
            try:
                logger.info("Generating AI cover letter for %s", company.name)
                return generate_cover_letter_ai(company, profile)
            except Exception as exc:
                logger.debug("AI generation failed for %s: %s", company.name, exc)

        templates = profile.get("cover_letter_templates", {})
        template, focus_area = self._select_template(category or company.category, templates)
        if not template:
            template = (
                "I'm interested in joining {company_name} and contributing my "
                "experience in {focus_area}."
            )

        return template.format(
            company_name=company.name,
            focus_area=focus_area,
            company_focus="building the future",
            company_description=company.description or "building innovative technology",
        )

    @staticmethod
    def _select_template(category: str, templates: dict[str, str]) -> tuple[str, str]:
        category_lower = (category or "").lower()
        if any(term in category_lower for term in ("decentralized", "blockchain", "web3")):
            return templates.get("decentralized_web3", templates.get("default", "")), (
                "decentralized protocols and sovereign identity"
            )
        if any(term in category_lower for term in ("machine learning", "ai", "llm")):
            return templates.get("machine_learning", templates.get("default", "")), (
                "machine learning and inference optimization"
            )
        if any(term in category_lower for term in ("browser", "rendering", "graphics")):
            return templates.get("systems_infrastructure", templates.get("default", "")), (
                "browser engines and GPU rendering"
            )
        if any(term in category_lower for term in ("infrastructure", "devops", "systems")):
            return templates.get("systems_infrastructure", templates.get("default", "")), (
                "systems architecture and infrastructure"
            )
        return templates.get("default", ""), "your mission"

    def save_results(self) -> None:
        if not self.results:
            logger.info("No results to save")
            return

        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = APPLICATIONS_DIR / f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.results[0].keys()))
            writer.writeheader()
            writer.writerows(self.results)
        logger.info("Results saved to %s", output_path)

    @staticmethod
    def select_job(jobs: list[Any], criteria: JobSearchCriteria) -> Any | None:
        """Compatibility wrapper for tests and scripts importing this method."""
        return select_job(jobs, criteria)

    def _pause_loop(
        self,
        driver: webdriver.Chrome,
        profile: dict[str, Any],
        cover_letter: str,
    ) -> tuple[list[str], list[str]]:
        """Interactive pause: let user trigger autofill (possibly multiple times), then advance."""
        latest_filled: list[str] = []
        latest_notes: list[str] = []
        prompt = (
            "\n[Enter] run autofill   [n] move to next company   [s] skip this company   [q] quit run: "
        )
        while True:
            try:
                cmd = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                logger.warning("Aborted by user during pause")
                raise
            if cmd == "":
                result = fill_application_form(
                    driver, profile, profile.get("resume_path"), cover_letter
                )
                latest_filled = result.filled
                latest_notes = result.notes
                logger.info(
                    "Autofill: %s filled, %s skipped",
                    len(result.filled), len(result.skipped),
                )
                if result.filled:
                    print(f"Filled {len(result.filled)} field(s):")
                    for f in result.filled:
                        print(f"  + {f}")
                else:
                    print("No fields filled. Likely reasons: form behind captcha/login, fields in nested iframe, or non-standard labels.")
                for n in result.notes:
                    print(f"  ! {n}")
                continue
            if cmd in ("n", "s"):
                if cmd == "s":
                    logger.info("User skipped company")
                return latest_filled, latest_notes
            if cmd == "q":
                logger.warning("User quit run")
                raise KeyboardInterrupt
            print("Unknown command. Use Enter / n / s / q.")

    def apply_company(self, driver: webdriver.Chrome, company: Company, profile: dict[str, Any]) -> bool:
        """Open the first detected application flow for a supported job board."""
        if not company.careers_url and not company.url:
            logger.warning("No URL for %s", company.name)
            return False

        cover_letter = self.generate_cover_letter(company, profile)
        profile["generated_cover_letter"] = cover_letter
        criteria = JobSearchCriteria.from_profile(profile)
        handler = get_job_board_handler(company.job_board)
        if handler is None:
            logger.warning("Unknown job board for %s: %s", company.name, company.job_board)
            return False

        try:
            return handler.open_apply_flow(driver, company, criteria)
        except Exception as exc:
            logger.error("Application flow failed for %s: %s", company.name, exc)
            return False

    def run(self, dry_run: bool = True) -> None:
        logger.info("Starting job application automata")
        if dry_run:
            logger.info("DRY RUN MODE - no applications will be submitted")

        profile = self.load_application_profile()
        if not profile:
            logger.warning("No profile loaded. Continuing with defaults.")

        driver = None
        try:
            if not dry_run:
                driver = webdriver.Chrome(options=self._setup_chrome_options())

            for index, company in enumerate(self.companies, start=1):
                if company.applied:
                    logger.info("[%s/%s] Skipping %s (already applied)", index, len(self.companies), company.name)
                    continue
                if not company.url and not company.careers_url:
                    logger.warning("[%s/%s] Skipping %s (no URL)", index, len(self.companies), company.name)
                    continue

                logger.info("[%s/%s] Processing %s", index, len(self.companies), company.name)
                cover_letter = self.generate_cover_letter(company, profile)
                autofill_filled: list[str] = []
                autofill_notes: list[str] = []
                if dry_run:
                    success = True
                    status = "dry_run_planned"
                    notes = "Dry run only; no browser action taken."
                else:
                    success = self.apply_company(driver, company, profile)
                    status = "opened_apply_flow_not_submitted" if success else "failed"
                    notes = (
                        "Opened the first detected apply flow; no form was submitted."
                        if success
                        else company.notes
                    )
                    if success and self.pause_each:
                        time.sleep(1)
                        print(f"\n--- {company.name} ---")
                        print("Apply page opened. If a captcha or login gate is present, solve it first.")
                        autofill_filled, autofill_notes = self._pause_loop(
                            driver, profile, cover_letter
                        )
                        if autofill_filled:
                            status = "form_autofilled_awaiting_human_submit"
                            notes = f"Autofilled {len(autofill_filled)} field(s); human submitted manually."
                    if success:
                        company.notes = notes

                self.results.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "company": company.name,
                        "category": company.category,
                        "url": company.url,
                        "careers_url": company.careers_url,
                        "job_board": company.job_board,
                        "success": success,
                        "submitted": False,
                        "status": status,
                        "notes": notes,
                        "autofill_filled": "; ".join(autofill_filled),
                        "autofill_notes": "; ".join(autofill_notes),
                        "cover_letter_preview": cover_letter[:500],
                    }
                )
                time.sleep(self.delay)
        finally:
            if driver:
                driver.quit()

        self.save_results()
        if not dry_run:
            self.save_companies_to_csv()
        logger.info("Completed. %s successful browser actions.", sum(1 for r in self.results if r["success"]))


def create_companies_csv(markdown_path: str, csv_path: str) -> None:
    companies = []
    with open(markdown_path) as f:
        for line in f:
            line = line.strip()
            if line and line[0].isdigit() and "**" in line:
                parts = line.split("**")
                if len(parts) >= 2:
                    companies.append(
                        {
                            "name": parts[1],
                            "category": "",
                            "url": "",
                            "careers_url": "",
                            "job_board": "",
                            "description": "",
                            "applied": "False",
                        }
                    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "category", "url", "careers_url", "job_board", "description", "applied"],
        )
        writer.writeheader()
        writer.writerows(companies)

    logger.info("Created %s with %s companies", csv_path, len(companies))


def create_profile_template() -> None:
    profile = {
        "email": "your-email@example.com",
        "phone": "+1-XXX-XXX-XXXX",
        "name": "Your Name",
        "linkedin_url": "https://linkedin.com/in/yourprofile",
        "github_url": "https://github.com/yourprofile",
        "resume_file": "path/to/resume.pdf",
        "cover_letter_templates": {
            "default": (
                "Looking forward to discussing how my experience in {focus_area} "
                "aligns with {company_name}."
            )
        },
        "job_search": {
            "desired_titles": ["systems engineer", "rust engineer", "backend engineer"],
            "excluded_titles": ["intern", "student", "sales", "marketing"],
            "locations": ["remote", "europe", "portugal"],
            "remote_only": False,
        },
        "focus_areas": ["Rust systems programming", "Decentralized protocols", "ML/LLM engineering"],
        "skills": ["Rust", "Python", "JavaScript", "Protocol Design", "ML/LLaMA fine-tuning"],
    }
    DEFAULT_PROFILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_PROFILE.write_text(json.dumps(profile, indent=2) + "\n")
    logger.info("Created %s template", DEFAULT_PROFILE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Application Automata")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no applications)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser headless")
    parser.add_argument("--pause-each", action="store_true", help="Autofill each form, then pause for human review + manual submit (forces non-headless)")
    parser.add_argument("--init", action="store_true", help="Initialize CSV and profile templates")
    parser.add_argument("--csv", default=str(DEFAULT_COMPANIES), help="Companies CSV file")
    parser.add_argument("--markdown", default=str(DEFAULT_TARGET_COMPANIES), help="Source markdown file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.init:
        create_companies_csv(args.markdown, args.csv)
        create_profile_template()
        logger.info("Initialization complete. Edit %s and %s, then run with --dry-run", args.csv, DEFAULT_PROFILE)
        return 0

    automata = JobApplicationAutomata(headless=args.headless, pause_each=args.pause_each)
    automata.load_companies_from_csv(args.csv)
    automata.run(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
