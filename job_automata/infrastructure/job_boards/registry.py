from __future__ import annotations

from job_automata.infrastructure.job_boards.greenhouse import GreenhouseHandler
from job_automata.infrastructure.job_boards.lever import LeverHandler
from job_automata.infrastructure.job_boards.workable import WorkableHandler

HANDLERS = {
    GreenhouseHandler.name: GreenhouseHandler(),
    LeverHandler.name: LeverHandler(),
    WorkableHandler.name: WorkableHandler(),
}


def get_job_board_handler(name: str):
    return HANDLERS.get((name or "").lower())

