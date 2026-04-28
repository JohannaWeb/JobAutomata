from __future__ import annotations

import logging
from typing import Any

from job_automata.domain import Company, JobSearchCriteria
from job_automata.infrastructure.job_boards.base import select_job
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class GemHandler:
    name = "gem"

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        logger.info("Opening Gem apply flow for %s", company.name)
        driver.get(company.careers_url or company.url)

        jobs = self._job_links(driver)
        if not jobs:
            logger.warning("No Gem jobs found for %s", company.name)
            return False

        job = select_job(jobs, criteria)
        if job is None:
            return False

        job.click()
        self._click_apply_if_available(driver)
        return True

    @staticmethod
    def _job_links(driver: Any) -> list[Any]:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='jobs.gem.com']"))
            )
        except TimeoutException:
            return []

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='jobs.gem.com']")
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
            logger.info("Gem job detail opened; no separate apply button found")
