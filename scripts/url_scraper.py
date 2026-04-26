#!/usr/bin/env python3
"""Compatibility wrapper for company URL enrichment.

Implementation lives in `job_automata.infrastructure.scraping.url_scraper`.
"""

from job_automata.infrastructure.scraping.url_scraper import (  # noqa: F401
    JOB_BOARD_MARKERS,
    KNOWN_URLS,
    URLScraper,
    extract_company_names,
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
