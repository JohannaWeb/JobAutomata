from __future__ import annotations

import logging
from typing import Any

from job_automata.domain import Company, JobSearchCriteria
from job_automata.infrastructure.job_boards.base import select_job
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class LeverHandler:
    name = "lever"

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        logger.info("Opening Lever apply flow for %s", company.name)
        driver.get(company.careers_url or f"{company.url}/careers")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-lever-id]"))
        )

        jobs = driver.find_elements(By.CSS_SELECTOR, "[data-lever-id]")
        if not jobs:
            logger.warning("No Lever jobs found for %s", company.name)
            return False

        job = select_job(jobs, criteria)
        if job is None:
            return False

        job.click()
        apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Apply')]"))
        )
        apply_button.click()
        return True

