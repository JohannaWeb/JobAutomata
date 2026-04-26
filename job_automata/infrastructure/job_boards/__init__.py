"""Job board automation adapters."""

from job_automata.infrastructure.job_boards.base import JobBoardHandler, select_job
from job_automata.infrastructure.job_boards.registry import get_job_board_handler

__all__ = ["JobBoardHandler", "get_job_board_handler", "select_job"]
