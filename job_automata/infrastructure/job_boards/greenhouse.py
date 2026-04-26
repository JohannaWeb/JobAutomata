from __future__ import annotations

import logging
from typing import Any

from job_automata.domain import Company, JobSearchCriteria
from job_automata.infrastructure.job_boards.base import select_job
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class GreenhouseHandler:
    name = "greenhouse"

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        logger.info("Opening Greenhouse apply flow for %s", company.name)
        driver.get(company.careers_url or f"{company.url}/careers")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-job-id]"))
        )

        jobs = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
        if not jobs:
            logger.warning("No Greenhouse jobs found for %s", company.name)
            return False

        job = select_job(jobs, criteria)
        if job is None:
            return False

        job.click()
        apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Apply')]"))
        )
        apply_button.click()
        return True

