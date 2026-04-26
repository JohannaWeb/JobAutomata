#!/usr/bin/env python3
"""
Company URL and careers-page enrichment.

Keeps the original CLI contract:
- --company prints one enriched company record as JSON
- --markdown + --csv enriches markdown company lists into CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from job_automata.config import CACHE_DIR, DEFAULT_COMPANIES, DEFAULT_TARGET_COMPANIES, LOG_DIR


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[],
)
logger = logging.getLogger(__name__)
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.addHandler(logging.FileHandler(LOG_DIR / "url_scraper.log"))
logger.addHandler(logging.StreamHandler())


KNOWN_URLS = {
    "Bluesky": "https://bsky.social",
    "Protocol Labs": "https://protocol.ai",
    "Akash Network": "https://akash.network",
    "Solana Labs": "https://solana.com",
    "Polygon": "https://polygon.technology",
    "Starkware": "https://starkware.co",
    "Thirdweb": "https://thirdweb.com",
    "Lens Protocol": "https://lens.xyz",
    "ENS (Ethereum Name Service)": "https://ens.domains",
    "Safe{Wallet}": "https://safe.global",
    "Optimism": "https://optimism.io",
    "Arbitrum": "https://arbitrum.io",
    "Aleo": "https://aleo.org",
    "Status": "https://status.im",
    "Zcash": "https://z.cash",
    "Cosmos": "https://cosmos.network",
    "Servo": "https://servo.org",
    "Ladybird": "https://ladybird.org",
    "Igalia": "https://igalia.com",
    "Firefox/Mozilla": "https://mozilla.org",
    "Apple WebKit": "https://webkit.org",
    "Brave": "https://brave.com",
    "Arc": "https://arc.net",
    "Zed": "https://zed.dev",
    "Figma": "https://figma.com",
    "Tauri": "https://tauri.app",
    "Dioxus": "https://dioxuslabs.com",
    "Anthropic": "https://anthropic.com",
    "OpenAI": "https://openai.com",
    "Meta AI": "https://ai.meta.com",
    "Stability AI": "https://stability.ai",
    "HuggingFace": "https://huggingface.co",
    "Hugging Face": "https://huggingface.co",
    "Together AI": "https://www.together.ai",
    "Modal": "https://modal.com",
    "Replicate": "https://replicate.com",
    "Weights & Biases": "https://wandb.ai",
    "Cohere": "https://cohere.com",
    "Mistral AI": "https://mistral.ai",
    "Scale AI": "https://scale.com",
    "Eleven Labs": "https://elevenlabs.io",
    "RunwayML": "https://runwayml.com",
    "Databricks": "https://databricks.com",
    "Vercel": "https://vercel.com",
    "Netlify": "https://netlify.com",
    "Docker": "https://docker.com",
    "Canonical": "https://canonical.com",
    "Red Hat": "https://redhat.com",
    "HashiCorp": "https://hashicorp.com",
    "CloudFlare": "https://cloudflare.com",
    "Auth0": "https://auth0.com",
    "Okta": "https://okta.com",
    "Zoom": "https://zoom.us",
    "Signal": "https://signal.org",
    "Mullvad": "https://mullvad.net",
    "1Password": "https://1password.com",
    "Teleport": "https://goteleport.com",
    "Snyk": "https://snyk.io",
    "Wiz": "https://wiz.io",
    "Zscaler": "https://zscaler.com",
    "Vanta": "https://vanta.com",
    "Rubrik": "https://rubrik.com",
    "Fastly": "https://fastly.com",
    "Akamai": "https://akamai.com",
    "Cisco": "https://cisco.com",
    "Arista Networks": "https://arista.com",
    "Juniper Networks": "https://juniper.net",
    "PagerDuty": "https://pagerduty.com",
    "Datadog": "https://datadoghq.com",
    "Honeycomb.io": "https://honeycomb.io",
    "Linux Foundation": "https://linuxfoundation.org",
    "Aptos": "https://aptos.dev",
    "Sui": "https://sui.io",
    "Near Protocol": "https://near.org",
    "Avalanche": "https://avax.network",
    "Chainlink": "https://chain.link",
    "Uniswap Labs": "https://uniswap.org",
    "Aave": "https://aave.com",
    "GitHub": "https://github.com",
    "GitLab": "https://gitlab.com",
    "Atlassian": "https://atlassian.com",
    "JetBrains": "https://jetbrains.com",
    "Slack": "https://slack.com",
    "Discord": "https://discord.com",
    "Notion": "https://notion.so",
    "Stripe": "https://stripe.com",
    "Twilio": "https://twilio.com",
    "MongoDB": "https://mongodb.com",
    "Elastic": "https://elastic.co",
    "Snowflake": "https://snowflake.com",
    "ClickHouse": "https://clickhouse.com",
    "DuckDB": "https://duckdb.org",
    "Prometheus": "https://prometheus.io",
    "Grafana": "https://grafana.com",
}

CAREERS_PATHS = (
    "/careers",
    "/jobs",
    "/apply",
    "/hiring",
    "/work-with-us",
    "/join-us",
    "/career",
    "/employment",
)

JOB_BOARD_MARKERS = {
    "greenhouse": ("greenhouse.io", "grnhse", "greenhouse"),
    "lever": ("lever.co", "lever--", "lever-jobs"),
    "workable": ("workable.com", "workable-js", "apply.workable"),
    "ashby": ("ashby.com", "ashby-job"),
    "jobvite": ("jobvite.com", "jobvite"),
    "bamboo": ("bamboohr", "bamboo-hr"),
    "breezy": ("breezy.hr", "breezy_"),
    "ats": ("applicantstack", "taleo", "successfactors"),
}


class URLScraper:
    """Enriches company names with website, careers page, job board, and description."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; JobAutomata/1.0; +https://example.local)"}
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache_file = CACHE_DIR / "url_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        if not self.cache_file.exists():
            return {}
        try:
            return json.loads(self.cache_file.read_text())
        except json.JSONDecodeError:
            logger.warning("Ignoring invalid cache file: %s", self.cache_file)
            return {}

    def _save_cache(self) -> None:
        self.cache_file.write_text(json.dumps(self.cache, indent=2, sort_keys=True) + "\n")

    def guess_domain(self, company_name: str) -> str | None:
        cache_key = f"{company_name}:domain"
        if cache_key in self.cache:
            return self.cache[cache_key]

        slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
        compact = slug.replace("-", "")
        for host in (f"{slug}.com", f"{slug}.io", f"{slug}.ai", f"{compact}.com", f"{compact}.io"):
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}"
                try:
                    response = self.session.head(url, timeout=5, allow_redirects=True)
                    if response.status_code < 400:
                        normalized = self.normalize_url(response.url)
                        self.cache[cache_key] = normalized
                        self._save_cache()
                        return normalized
                except requests.RequestException:
                    continue
        return None

    @staticmethod
    def normalize_url(url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        host = parsed.netloc.removeprefix("www.")
        return f"https://{host}"

    def find_careers_page(self, base_url: str | None) -> str | None:
        if not base_url:
            return None

        cache_key = f"{base_url}:careers"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(base_url, timeout=10, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to load %s: %s", base_url, exc)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(" ", strip=True).lower()
            if any(term in href.lower() or term in text for term in ("careers", "jobs", "hiring", "join")):
                careers_url = urljoin(base_url, href)
                self.cache[cache_key] = careers_url
                self._save_cache()
                return careers_url

        for path in CAREERS_PATHS:
            candidate = urljoin(base_url, path)
            try:
                response = self.session.head(candidate, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    self.cache[cache_key] = response.url
                    self._save_cache()
                    return response.url
            except requests.RequestException:
                continue

        return None

    def detect_job_board(self, careers_url: str | None) -> str | None:
        if not careers_url:
            return None

        cache_key = f"{careers_url}:board"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(careers_url, timeout=10)
            content = response.text.lower()
        except requests.RequestException as exc:
            logger.warning("Failed to detect job board for %s: %s", careers_url, exc)
            return None

        for board, markers in JOB_BOARD_MARKERS.items():
            if any(marker in content for marker in markers):
                self.cache[cache_key] = board
                self._save_cache()
                return board

        self.cache[cache_key] = "custom"
        self._save_cache()
        return "custom"

    def scrape_company_description(self, base_url: str | None) -> str | None:
        if not base_url:
            return None

        cache_key = f"{base_url}:description"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to load description for %s: %s", base_url, exc)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        description = self._extract_description(soup)
        if description:
            self.cache[cache_key] = description
            self._save_cache()
        return description

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str | None:
        for attrs in ({"property": "og:description"}, {"name": "description"}):
            tag = soup.find("meta", attrs)
            if tag and tag.get("content"):
                return tag["content"].strip()

        for paragraph in soup.find_all("p", limit=5):
            text = paragraph.get_text(" ", strip=True)
            if 20 < len(text) < 300:
                return text
        return None

    def scrape_company(self, company_name: str) -> dict[str, Any]:
        logger.info("Scraping %s", company_name)
        website = KNOWN_URLS.get(company_name) or self.guess_domain(company_name)
        if not website:
            logger.warning("Could not find website for %s", company_name)
            return {
                "name": company_name,
                "url": "",
                "careers_url": "",
                "job_board": "",
                "description": "",
            }

        website = self.normalize_url(website)
        careers_url = self.find_careers_page(website)
        job_board = self.detect_job_board(careers_url)
        description = self.scrape_company_description(website)
        return {
            "name": company_name,
            "url": website,
            "careers_url": careers_url or "",
            "job_board": job_board or "",
            "description": description or "",
        }

    def scrape_from_markdown(self, markdown_path: str) -> list[dict[str, Any]]:
        companies = extract_company_names(Path(markdown_path))
        logger.info("Found %s companies in %s", len(companies), markdown_path)

        results = []
        for index, company in enumerate(companies, start=1):
            logger.info("[%s/%s] Scraping %s", index, len(companies), company)
            try:
                results.append(self.scrape_company(company))
            except Exception as exc:
                logger.error("Error scraping %s: %s", company, exc)
                results.append({"name": company, "url": "", "careers_url": "", "job_board": "", "description": ""})
            time.sleep(1)
        return results

    def update_csv(self, results: list[dict[str, Any]], csv_path: str) -> None:
        existing = {}
        path = Path(csv_path)
        if path.exists():
            with path.open(newline="") as f:
                for row in csv.DictReader(f):
                    existing[row["name"]] = row

        merged = []
        for result in results:
            row = existing.get(result["name"], {"name": result["name"], "category": "", "applied": "False"})
            row.update(result)
            merged.append(row)

        fieldnames = ["name", "category", "url", "careers_url", "job_board", "description", "applied"]
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(merged)

        logger.info("Updated %s with %s companies", csv_path, len(merged))


def extract_company_names(markdown_path: Path) -> list[str]:
    companies = []
    with markdown_path.open() as f:
        for line in f:
            stripped = line.strip()
            if stripped and stripped[0].isdigit() and "**" in stripped:
                parts = stripped.split("**")
                if len(parts) >= 2:
                    companies.append(parts[1].strip())
    return companies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="URL Scraper for Job Applications")
    parser.add_argument("--markdown", default=str(DEFAULT_TARGET_COMPANIES), help="Source markdown file")
    parser.add_argument("--csv", default=str(DEFAULT_COMPANIES), help="Output CSV file")
    parser.add_argument("--company", help="Scrape single company")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scraper = URLScraper()
    if args.company:
        print(json.dumps(scraper.scrape_company(args.company), indent=2))
        return 0

    results = scraper.scrape_from_markdown(args.markdown)
    scraper.update_csv(results, args.csv)
    print(f"\nScraped {len(results)} companies. Check {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
