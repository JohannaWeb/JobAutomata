from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class JobSearchCriteria:
    """Optional filters used before clicking a job listing."""

    desired_titles: list[str]
    excluded_titles: list[str]
    locations: list[str]
    remote_only: bool = False

    @classmethod
    def from_profile(cls, profile: dict[str, Any]) -> "JobSearchCriteria":
        config = profile.get("job_search", {})
        return cls(
            desired_titles=normalize_terms(config.get("desired_titles", [])),
            excluded_titles=normalize_terms(config.get("excluded_titles", [])),
            locations=normalize_terms(config.get("locations", [])),
            remote_only=bool(config.get("remote_only", False)),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.desired_titles or self.excluded_titles or self.locations or self.remote_only)

    def matches(self, job_text: str) -> bool:
        normalized = normalize_text(job_text)
        if not normalized:
            return False

        if self.excluded_titles and any(term in normalized for term in self.excluded_titles):
            return False

        if self.desired_titles and not any(term in normalized for term in self.desired_titles):
            return False

        if self.remote_only and "remote" not in normalized:
            return False

        if self.locations and not any(term in normalized for term in self.locations):
            return False

        return True


def normalize_text(value: str) -> str:
    return " ".join((value or "").lower().split())


def normalize_terms(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return [normalized for value in values if (normalized := normalize_text(str(value)))]

