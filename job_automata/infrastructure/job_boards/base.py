from __future__ import annotations

import logging
from typing import Any, Protocol

from job_automata.domain import Company, JobSearchCriteria, normalize_text

logger = logging.getLogger(__name__)


class JobBoardHandler(Protocol):
    name: str

    def open_apply_flow(self, driver: Any, company: Company, criteria: JobSearchCriteria) -> bool:
        """Open a board-specific apply flow for a matching role."""


def select_job(jobs: list[Any], criteria: JobSearchCriteria) -> Any | None:
    if not jobs:
        return None

    if not criteria.is_configured:
        logger.info("No job filters configured; selecting first listing")
        return jobs[0]

    for job in jobs:
        text = job.text or job.get_attribute("textContent") or ""
        if criteria.matches(text):
            logger.info("Selected matching job listing: %s", normalize_text(text)[:160])
            return job

    logger.warning("No job listing matched configured filters")
    return None

