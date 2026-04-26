from dataclasses import dataclass


@dataclass
class Company:
    """Company target with URL and application metadata."""

    name: str
    category: str = ""
    url: str = ""
    careers_url: str = ""
    job_board: str = ""
    description: str = ""
    applied: bool = False
    application_date: str = ""
    notes: str = ""

