import unittest

from job_automata.application.auto_apply import JobApplicationAutomata
from job_automata.domain import JobSearchCriteria


class FakeJob:
    def __init__(self, text):
        self.text = text

    def get_attribute(self, name):
        return self.text if name == "textContent" else ""


class JobSearchCriteriaTests(unittest.TestCase):
    def test_unconfigured_filters_match_first_job(self):
        automata = JobApplicationAutomata()
        criteria = JobSearchCriteria.from_profile({})
        jobs = [FakeJob("Sales Manager"), FakeJob("Rust Systems Engineer")]

        self.assertIs(automata.select_job(jobs, criteria), jobs[0])

    def test_desired_title_selects_matching_job(self):
        automata = JobApplicationAutomata()
        criteria = JobSearchCriteria.from_profile(
            {"job_search": {"desired_titles": ["rust engineer"]}}
        )
        jobs = [FakeJob("Sales Manager"), FakeJob("Senior Rust Engineer - Remote")]

        self.assertIs(automata.select_job(jobs, criteria), jobs[1])

    def test_excluded_title_rejects_otherwise_matching_job(self):
        criteria = JobSearchCriteria.from_profile(
            {
                "job_search": {
                    "desired_titles": ["engineer"],
                    "excluded_titles": ["intern"],
                }
            }
        )

        self.assertFalse(criteria.matches("Software Engineer Intern"))

    def test_remote_only_requires_remote_text(self):
        criteria = JobSearchCriteria.from_profile(
            {"job_search": {"desired_titles": ["engineer"], "remote_only": True}}
        )

        self.assertFalse(criteria.matches("Backend Engineer - London"))
        self.assertTrue(criteria.matches("Backend Engineer - Remote Europe"))

    def test_location_filter_requires_one_location(self):
        criteria = JobSearchCriteria.from_profile(
            {
                "job_search": {
                    "desired_titles": ["engineer"],
                    "locations": ["portugal", "europe"],
                }
            }
        )

        self.assertFalse(criteria.matches("Backend Engineer - San Francisco"))
        self.assertTrue(criteria.matches("Backend Engineer - Portugal"))


if __name__ == "__main__":
    unittest.main()
