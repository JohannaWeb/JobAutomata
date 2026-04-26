#!/usr/bin/env python3
"""
LinkedIn Hiring Manager Hunter
Finds and tracks hiring managers at target companies
"""

import csv
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from job_automata.config import DEFAULT_COMPANIES, LOG_DIR

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'linkedin_hunter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class LinkedInManager:
    """Hiring manager profile"""
    name: str
    title: str
    company: str
    url: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    connection_status: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    found_date: Optional[str] = None


class LinkedInHunter:
    """Finds hiring managers on LinkedIn"""

    def __init__(self, email: str, password: str, headless: bool = True):
        """
        Initialize LinkedIn Hunter

        Args:
            email: LinkedIn email
            password: LinkedIn password
            headless: Run browser headless
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.chrome_options = self._setup_chrome()
        self.driver = None
        self.managers: List[LinkedInManager] = []
        self.session_file = Path('linkedin_session.json')

    def _setup_chrome(self) -> Options:
        """Configure Chrome"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        return options

    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            logger.info("Logging into LinkedIn...")
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.get('https://www.linkedin.com/login')

            # Wait for login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )

            # Enter credentials
            email_field = self.driver.find_element(By.ID, 'username')
            password_field = self.driver.find_element(By.ID, 'password')

            email_field.send_keys(self.email)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            # Wait for dashboard
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//nav[@data-test-id='global-nav']"))
            )

            logger.info("Successfully logged into LinkedIn")
            return True

        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False

    def search_company_managers(self, company_name: str, keywords: List[str] = None) -> List[LinkedInManager]:
        """
        Search for managers at a company

        Args:
            company_name: Company name
            keywords: Job title keywords (e.g., ['recruiter', 'hiring', 'manager'])
        """
        if not keywords:
            keywords = ['recruiter', 'talent', 'hiring manager', 'engineering manager', 'hr']

        managers_found = []

        try:
            logger.info(f"Searching for managers at {company_name}...")

            # Search LinkedIn users
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={company_name}&title=recruiter"
            self.driver.get(search_url)

            time.sleep(3)

            # Get results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'base-search-card'))
            )

            results = self.driver.find_elements(By.CLASS_NAME, 'base-search-card')
            logger.info(f"Found {len(results)} potential managers")

            for result in results[:10]:  # Limit to top 10
                try:
                    # Extract name
                    name_elem = result.find_element(By.CLASS_NAME, 'app-aware-link')
                    name = name_elem.get_text().strip()

                    # Extract title
                    title_elem = result.find_element(By.CLASS_NAME, 'sub-header-line')
                    title = title_elem.get_text().strip()

                    # Extract URL
                    profile_url = name_elem.get_attribute('href')

                    # Check if title matches keywords
                    if any(keyword.lower() in title.lower() for keyword in keywords):
                        manager = LinkedInManager(
                            name=name,
                            title=title,
                            company=company_name,
                            url=profile_url,
                            found_date=datetime.now().isoformat()
                        )
                        managers_found.append(manager)
                        logger.info(f"Found: {name} - {title}")

                except Exception as e:
                    logger.warning(f"Error parsing result: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching for managers at {company_name}: {e}")

        return managers_found

    def extract_email(self, profile_url: str) -> Optional[str]:
        """
        Try to extract email from LinkedIn profile
        Note: Direct email extraction from LinkedIn is against ToS
        This method looks for email in profile text if publicly shared
        """
        try:
            self.driver.get(profile_url)
            time.sleep(2)

            # Check if email is displayed (some users make it public)
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            if '@' in page_text:
                # Very basic email extraction - not reliable
                lines = page_text.split('\n')
                for line in lines:
                    if '@' in line and '.' in line:
                        email = line.strip()
                        if len(email) < 100:  # Sanity check
                            return email

        except Exception as e:
            logger.warning(f"Could not extract email from {profile_url}: {e}")

        return None

    def hunt_managers_batch(self, companies: List[str]) -> None:
        """Hunt managers for multiple companies"""
        for company in companies:
            try:
                managers = self.search_company_managers(company)
                self.managers.extend(managers)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error hunting managers for {company}: {e}")

    def save_managers_csv(self, csv_path: str) -> None:
        """Save managers to CSV"""
        with open(csv_path, 'w', newline='') as f:
            fieldnames = [
                'name', 'title', 'company', 'url', 'email',
                'department', 'connection_status', 'location', 'notes', 'found_date'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for manager in self.managers:
                writer.writerow(asdict(manager))

        logger.info(f"Saved {len(self.managers)} managers to {csv_path}")

    def close(self) -> None:
        """Close browser session"""
        if self.driver:
            self.driver.quit()


class LinkedInAPIClient:
    """Alternative: Use LinkedIn Official API (requires credentials)"""

    def __init__(self, access_token: str):
        """Initialize with LinkedIn OAuth access token"""
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self.api_base = 'https://api.linkedin.com/v2'

    def search_employees(self, company_name: str, title_keywords: List[str]) -> List[Dict]:
        """
        Search employees at a company using LinkedIn API
        Requires: LinkedIn Talent Solutions or Recruiter license
        """
        try:
            # This is a placeholder - actual implementation requires LinkedIn API access
            endpoint = f"{self.api_base}/search/blended"

            query = {
                "keywords": f"{company_name} {' OR '.join(title_keywords)}",
                "filters": {
                    "company": company_name
                }
            }

            response = requests.post(
                endpoint,
                headers=self.headers,
                json=query,
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                logger.warning(f"LinkedIn API returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"LinkedIn API search failed: {e}")
            return []


def load_companies_from_csv(csv_path: str) -> List[str]:
    """Load company names from CSV"""
    companies = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('name'):
                companies.append(row['name'])
    return companies


def main() -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(description='LinkedIn Hiring Manager Hunter')
    parser.add_argument('--email', help='LinkedIn email')
    parser.add_argument('--csv', default=str(DEFAULT_COMPANIES), help='Companies CSV')
    parser.add_argument('--output', default='linkedin_managers.csv', help='Output CSV')
    parser.add_argument('--company', help='Hunt single company')
    parser.add_argument('--headless', action='store_true', default=True)

    args = parser.parse_args()
    email = args.email or os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')

    if not email or not password:
        logger.error("LinkedIn credentials required via --email/LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        logger.info("Usage: LINKEDIN_PASSWORD=... python linkedin_hunter.py --email your@email.com")
        return 1

    hunter = LinkedInHunter(email, password, headless=args.headless)

    try:
        if not hunter.login():
            return 1

        if args.company:
            managers = hunter.search_company_managers(args.company)
            hunter.managers = managers
        else:
            companies = load_companies_from_csv(args.csv)
            hunter.hunt_managers_batch(companies)

        if hunter.managers:
            hunter.save_managers_csv(args.output)
            print(f"\nFound {len(hunter.managers)} managers. Saved to {args.output}")
        else:
            print("No managers found")
        return 0

    finally:
        hunter.close()


if __name__ == '__main__':
    raise SystemExit(main())
