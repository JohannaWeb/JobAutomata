#!/usr/bin/env python3
"""Compatibility wrapper for AI cover letter generation."""

from job_automata.application.cover_letter_ai import *  # noqa: F403
from job_automata.application.cover_letter_ai import main


if __name__ == "__main__":
    raise SystemExit(main())
