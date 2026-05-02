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


class GreenhouseHandler:
    name = "greenhouse"

    JOB_SELECTORS = (
        "a[href*='/jobs/']",        # new job-boards.greenhouse.io layout
        ".job-post a",              # alt new layout
        "[data-job-id]",            # legacy boards.greenhouse.io
        ".opening a",               # older legacy
    )

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        logger.info("Opening Greenhouse apply flow for %s", company.name)
        target_url = company.careers_url or f"{company.url}/careers"
        driver.get(target_url)

        if "/jobs/" in target_url:
            self._click_apply_if_available(driver)
            return True

        jobs = self._find_jobs(driver)
        if not jobs:
            logger.warning("No Greenhouse jobs found for %s", company.name)
            return False

        job = select_job(jobs, criteria)
        if job is None:
            return False

        href = job.get_attribute("href") or ""
        if href:
            driver.get(href)
        else:
            job.click()

        # Form is usually already on the job page in the new layout; clicking Apply is best-effort.
        self._click_apply_if_available(driver)
        return True

    @staticmethod
    def _click_apply_if_available(driver: Any) -> None:
        try:
            apply_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Apply')] | //button[contains(., 'Apply')]"))
            )
            apply_button.click()
        except TimeoutException:
            logger.info("No separate Apply button — form likely inline on job page")

    def _find_jobs(self, driver: Any) -> list[Any]:
        for selector in self.JOB_SELECTORS:
            try:
                WebDriverWait(driver, 8).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
            except TimeoutException:
                continue
            els = driver.find_elements(By.CSS_SELECTOR, selector)
            visible = [e for e in els if e.is_displayed()]
            if visible:
                logger.info("Found %s job links via selector %r", len(visible), selector)
                return visible
        return []
