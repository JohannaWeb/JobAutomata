import json

from job_automata.application.auto_apply import JobApplicationAutomata


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
