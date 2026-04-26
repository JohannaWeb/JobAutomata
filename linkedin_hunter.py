#!/usr/bin/env python3
"""Compatibility wrapper for LinkedIn manager hunting."""

from job_automata.infrastructure.linkedin.hunter import *  # noqa: F403
from job_automata.infrastructure.linkedin.hunter import main


if __name__ == "__main__":
    raise SystemExit(main())

