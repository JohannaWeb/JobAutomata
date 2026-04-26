#!/usr/bin/env python3
"""Compatibility wrapper for the Job Automata workflow CLI.

Implementation lives in `job_automata.application.workflow`.
"""

from job_automata.application.workflow import (  # noqa: F401
    JobAutomataOrchestrator,
    build_workflow,
    main,
)


if __name__ == "__main__":
    main()
