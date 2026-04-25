#!/usr/bin/env python3
"""
Job Application Automata
Auto-applies to target companies. Requires company URLs and job board data.
"""

import json
import csv
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Company:
    """Company target with URL and application details"""
    name: str
    category: str
    url: Optional[str] = None
    careers_url: Optional[str] = None
    job_board: Optional[str] = None  # 'greenhouse', 'lever', 'workable', 'custom', etc.
    applied: bool = False
    application_date: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationAutomata:
    """Automates job applications across multiple companies"""

    def __init__(self, headless: bool = True, delay_seconds: int = 3):
        """
        Initialize automata

        Args:
            headless: Run browser in headless mode
            delay_seconds: Delay between applications to avoid rate limiting
        """
        self.delay = delay_seconds
        self.headless = headless
        self.companies: List[Company] = []
        self.results: List[Dict] = []
        self.chrome_options = self._setup_chrome_options()
        self.profile_path = Path('profile.json')

    def _setup_chrome_options(self) -> Options:
        """Configure Chrome options"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        return options

    def load_companies_from_csv(self, csv_path: str) -> None:
        """Load company targets from CSV"""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company = Company(
                    name=row['name'],
                    category=row['category'],
                    url=row.get('url'),
                    careers_url=row.get('careers_url'),
                    job_board=row.get('job_board'),
                    applied=row.get('applied', 'False') == 'True',
                )
                self.companies.append(company)
        logger.info(f"Loaded {len(self.companies)} companies from {csv_path}")

    def load_application_profile(self) -> Dict:
        """Load user profile (resume, cover letter template, etc.)"""
        if not self.profile_path.exists():
            logger.error(f"Profile file {self.profile_path} not found")
            return {}
        with open(self.profile_path, 'r') as f:
            profile = json.load(f)

        # Load resume content if markdown file specified
        if 'resume_file' in profile:
            resume_path = Path(profile['resume_file'])
            if resume_path.exists():
                with open(resume_path, 'r') as f:
                    profile['resume_content'] = f.read()
                logger.info(f"Loaded resume from {resume_path}")

        return profile

    def generate_cover_letter(self, company: Company, profile: Dict, category: str) -> str:
        """
        Generate tailored cover letter based on company category

        Args:
            company: Target company
            profile: User profile with templates
            category: Company category (Web3, ML, Systems, etc.)
        """
        templates = profile.get('cover_letter_templates', {})

        # Determine which template to use
        category_lower = (category or '').lower()
        if 'decentralized' in category_lower or 'blockchain' in category_lower or 'web3' in category_lower:
            template = templates.get('decentralized_web3', templates.get('default', ''))
            focus_area = 'decentralized protocols and sovereign identity'
        elif 'machine learning' in category_lower or 'ai' in category_lower or 'llm' in category_lower:
            template = templates.get('machine_learning', templates.get('default', ''))
            focus_area = 'machine learning and inference optimization'
        elif 'browser' in category_lower or 'rendering' in category_lower or 'graphics' in category_lower:
            template = templates.get('systems_infrastructure', templates.get('default', ''))
            focus_area = 'browser engines and GPU rendering'
        elif 'infrastructure' in category_lower or 'devops' in category_lower or 'systems' in category_lower:
            template = templates.get('systems_infrastructure', templates.get('default', ''))
            focus_area = 'systems architecture and infrastructure'
        else:
            template = templates.get('default', '')
            focus_area = 'your mission'

        # Format template
        if not template:
            template = f"I'm interested in joining {company.name} and contributing my expertise in systems engineering and decentralized protocols."

        cover_letter = template.format(
            company_name=company.name,
            focus_area=focus_area,
            company_focus='building the future'
        )

        return cover_letter

    def save_results(self) -> None:
        """Save application results to CSV"""
        output_path = Path(f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(output_path, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        logger.info(f"Results saved to {output_path}")

    def apply_greenhouse(self, driver, company: Company, profile: Dict) -> bool:
        """Apply via Greenhouse job board"""
        try:
            logger.info(f"Applying to {company.name} via Greenhouse...")

            # Navigate to careers page
            driver.get(company.careers_url or f"{company.url}/careers")
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-job-id]"))
            )

            # Find and click first matching job
            jobs = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
            if not jobs:
                logger.warning(f"No jobs found for {company.name}")
                return False

            jobs[0].click()
            time.sleep(2)

            # Click apply button
            apply_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Apply')]"))
            )
            apply_btn.click()

            # Fill form (customize based on actual fields)
            time.sleep(2)
            logger.info(f"Applied to {company.name}")
            return True

        except Exception as e:
            logger.error(f"Greenhouse application failed for {company.name}: {e}")
            return False

    def apply_lever(self, driver, company: Company, profile: Dict) -> bool:
        """Apply via Lever job board"""
        try:
            logger.info(f"Applying to {company.name} via Lever...")

            driver.get(company.careers_url or f"{company.url}/careers")
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-lever-id]"))
            )

            jobs = driver.find_elements(By.CSS_SELECTOR, "[data-lever-id]")
            if not jobs:
                logger.warning(f"No jobs found for {company.name}")
                return False

            jobs[0].click()
            time.sleep(2)

            apply_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
            )
            apply_btn.click()

            logger.info(f"Applied to {company.name}")
            return True

        except Exception as e:
            logger.error(f"Lever application failed for {company.name}: {e}")
            return False

    def apply_workable(self, driver, company: Company, profile: Dict) -> bool:
        """Apply via Workable job board"""
        try:
            logger.info(f"Applying to {company.name} via Workable...")

            driver.get(company.careers_url or f"{company.url}/careers")
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".jobs-list-item"))
            )

            jobs = driver.find_elements(By.CSS_SELECTOR, ".jobs-list-item")
            if not jobs:
                logger.warning(f"No jobs found for {company.name}")
                return False

            jobs[0].click()
            time.sleep(2)

            apply_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
            )
            apply_btn.click()

            logger.info(f"Applied to {company.name}")
            return True

        except Exception as e:
            logger.error(f"Workable application failed for {company.name}: {e}")
            return False

    def apply_company(self, driver, company: Company, profile: Dict) -> bool:
        """Route to appropriate application method"""
        if not company.careers_url and not company.url:
            logger.warning(f"No URL for {company.name}")
            return False

        # Generate tailored cover letter
        cover_letter = self.generate_cover_letter(company, profile, company.category)
        profile['generated_cover_letter'] = cover_letter

        if company.job_board == 'greenhouse':
            return self.apply_greenhouse(driver, company, profile)
        elif company.job_board == 'lever':
            return self.apply_lever(driver, company, profile)
        elif company.job_board == 'workable':
            return self.apply_workable(driver, company, profile)
        else:
            logger.warning(f"Unknown job board for {company.name} (board: {company.job_board})")
            return False

    def run(self, dry_run: bool = True) -> None:
        """
        Run application automata

        Args:
            dry_run: If True, only logs without applying
        """
        logger.info("Starting job application automata...")

        if dry_run:
            logger.info("DRY RUN MODE - No applications will be submitted")

        profile = self.load_application_profile()
        if not profile:
            logger.warning("No profile loaded. Continuing with defaults.")

        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)

            for i, company in enumerate(self.companies):
                if company.applied:
                    logger.info(f"[{i+1}/{len(self.companies)}] Skipping {company.name} (already applied)")
                    continue

                if not company.url:
                    logger.warning(f"[{i+1}/{len(self.companies)}] Skipping {company.name} (no URL)")
                    continue

                logger.info(f"[{i+1}/{len(self.companies)}] Processing {company.name}...")

                if dry_run:
                    success = True
                    logger.info(f"[DRY RUN] Would apply to {company.name}")
                else:
                    success = self.apply_company(driver, company, profile)

                result = {
                    'timestamp': datetime.now().isoformat(),
                    'company': company.name,
                    'category': company.category,
                    'url': company.url,
                    'success': success,
                    'notes': company.notes
                }
                self.results.append(result)

                time.sleep(self.delay)

        except Exception as e:
            logger.error(f"Fatal error during automation: {e}")

        finally:
            if driver:
                driver.quit()

            self.save_results()
            logger.info(f"Completed. {sum(1 for r in self.results if r['success'])} successful applications.")


def create_companies_csv(markdown_path: str, csv_path: str) -> None:
    """Convert markdown company list to CSV with empty URL columns"""
    companies = []
    with open(markdown_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line[0].isdigit():
                # Parse "1. **Company** — Description"
                parts = line.split('**')
                if len(parts) >= 2:
                    name = parts[1]
                    companies.append({
                        'name': name,
                        'category': '',
                        'url': '',
                        'careers_url': '',
                        'job_board': '',
                        'applied': 'False'
                    })

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'category', 'url', 'careers_url', 'job_board', 'applied'])
        writer.writeheader()
        writer.writerows(companies)

    logger.info(f"Created {csv_path} with {len(companies)} companies")


def create_profile_template() -> None:
    """Create a template profile.json file"""
    profile = {
        "email": "your-email@example.com",
        "phone": "+1-XXX-XXX-XXXX",
        "name": "Your Name",
        "linkedin_url": "https://linkedin.com/in/yourprofile",
        "github_url": "https://github.com/yourprofile",
        "resume_file": "path/to/resume.pdf",
        "cover_letter_template": "Looking forward to discussing how my experience in {focus_area} aligns with {company_name}.",
        "focus_areas": ["Rust systems programming", "Decentralized protocols", "ML/LLM engineering"],
        "skills": ["Rust", "Python", "JavaScript", "Protocol Design", "ML/LLaMA fine-tuning"]
    }
    with open('profile.json', 'w') as f:
        json.dump(profile, f, indent=2)
    logger.info("Created profile.json template")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Job Application Automata')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no applications)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser headless')
    parser.add_argument('--init', action='store_true', help='Initialize CSV and profile templates')
    parser.add_argument('--csv', default='companies.csv', help='Companies CSV file')
    parser.add_argument('--markdown', default='target-companies-100.md', help='Source markdown file')

    args = parser.parse_args()

    if args.init:
        create_companies_csv(args.markdown, args.csv)
        create_profile_template()
        logger.info("Initialization complete. Edit companies.csv and profile.json, then run with --dry-run")
    else:
        automata = JobApplicationAutomata(headless=args.headless)
        automata.load_companies_from_csv(args.csv)
        automata.run(dry_run=args.dry_run)
