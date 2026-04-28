from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from job_automata.domain import Company, JobSearchCriteria
from job_automata.infrastructure.job_boards.base import select_job
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class GetroHandler:
    name = "getro"

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        logger.info("Opening Getro apply flow for %s", company.name)

        for listing_url in self._listing_urls(company, criteria):
            driver.get(listing_url)
            jobs = self._job_links(driver)
            if not jobs:
                continue

            job = select_job(jobs, criteria)
            if job is None:
                continue

            job.click()
            self._click_apply_if_available(driver)
            return True

        logger.warning("No Getro job listing matched %s", company.name)
        return False

    @staticmethod
    def _listing_urls(company: Company, criteria: JobSearchCriteria) -> list[str]:
        base_url = company.careers_url or f"{company.url}/jobs"
        urls = []
        for title in criteria.desired_titles:
            urls.append(_with_query(base_url, {"q": title}))
        urls.append(base_url)
        return list(dict.fromkeys(urls))

    @staticmethod
    def _job_links(driver: Any) -> list[Any]:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/companies/'][href*='/jobs/']"))
            )
        except TimeoutException:
            return []

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/companies/'][href*='/jobs/']")
        seen = set()
        jobs = []
        for link in links:
            href = link.get_attribute("href")
            if href and href not in seen and link.is_displayed():
                seen.add(href)
                jobs.append(link)
        return jobs

    @staticmethod
    def _click_apply_if_available(driver: Any) -> None:
        try:
            apply_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//a[contains(., 'Apply') or contains(., 'apply')]"
                        "|//button[contains(., 'Apply') or contains(., 'apply')]",
                    )
                )
            )
            apply_button.click()
        except TimeoutException:
            logger.info("Getro job detail opened; no separate apply button found")


def _with_query(url: str, params: dict[str, str]) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/jobs"
    if path == "/":
        path = "/jobs"
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(params), parts.fragment))
