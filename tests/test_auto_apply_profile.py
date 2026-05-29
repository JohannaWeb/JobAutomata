import json

from job_automata.application import auto_apply
from job_automata.application.auto_apply import JobApplicationAutomata
from job_automata.domain import Company


def test_load_application_profile_keeps_pdf_resume_as_path(tmp_path):
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF-1.7\n\xda\n")
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps({"resume_file": str(resume_path)}))

    automata = JobApplicationAutomata()
    automata.profile_path = profile_path

    profile = automata.load_application_profile()

    assert profile["resume_path"] == str(resume_path)
    assert "resume_content" not in profile


def test_load_application_profile_decodes_text_resume_with_replacement(tmp_path):
    resume_path = tmp_path / "resume.md"
    resume_path.write_bytes(b"hello \xda world")
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps({"resume_file": str(resume_path)}))

    automata = JobApplicationAutomata()
    automata.profile_path = profile_path

    profile = automata.load_application_profile()

    assert profile["resume_content"] == "hello \ufffd world"


def test_ai_cover_letter_path_is_reachable(monkeypatch):
    company = Company(name="Acme", category="Infrastructure")
    automata = JobApplicationAutomata()

    def fake_generate_cover_letter_ai(received_company, received_profile):
        assert received_company is company
        assert received_profile == {"name": "Applicant"}
        return "AI generated letter"

    monkeypatch.setattr(auto_apply, "generate_cover_letter_ai", fake_generate_cover_letter_ai)

    assert automata.generate_cover_letter(company, {"name": "Applicant"}) == "AI generated letter"


def test_apply_company_reuses_generated_cover_letter(monkeypatch):
    company = Company(name="Acme", url="https://example.com/jobs", job_board="lever")
    automata = JobApplicationAutomata()
    opened = []

    class FakeHandler:
        def open_apply_flow(self, driver, received_company, criteria):
            opened.append((driver, received_company, criteria))
            return True

    def fail_if_called(*args, **kwargs):
        raise AssertionError("cover letter should be generated once in run(), not inside apply_company()")

    monkeypatch.setattr(auto_apply, "get_job_board_handler", lambda board: FakeHandler())
    monkeypatch.setattr(automata, "generate_cover_letter", fail_if_called)

    assert automata.apply_company(object(), company, {}, "Already generated") is True
    assert opened
