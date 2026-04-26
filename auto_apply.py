#!/usr/bin/env python3
"""Compatibility wrapper for the application automation CLI.

Implementation lives in `job_automata.application.auto_apply`.
"""

from job_automata.application.auto_apply import (  # noqa: F401
    Company,
    JobApplicationAutomata,
    JobSearchCriteria,
    create_companies_csv,
    create_profile_template,
    main,
)
from job_automata.domain import normalize_terms, normalize_text  # noqa: F401


if __name__ == "__main__":
    raise SystemExit(main())
