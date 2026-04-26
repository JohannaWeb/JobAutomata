#!/usr/bin/env python3
"""Print a readable example of dry-run application content."""

from __future__ import annotations

from auto_apply import Company, JobApplicationAutomata


def sample_profile() -> dict:
    return {
        "name": "Sample Candidate",
        "email": "candidate@example.com",
        "phone": "+1-555-0123",
        "linkedin_url": "https://linkedin.com/in/example",
        "github_url": "https://github.com/example",
        "focus_areas": ["Rust systems programming", "Decentralized protocols", "ML/LLM engineering"],
        "skills": ["Rust", "Python", "JavaScript", "Protocol Design", "Systems Architecture"],
        "cover_letter_templates": {
            "default": "I'm interested in joining {company_name} and contributing to {focus_area}.",
            "machine_learning": (
                "With experience in {focus_area}, I'm interested in {company_name}'s work "
                "on {company_description}."
            ),
            "decentralized_web3": (
                "I'm excited about {company_name}'s mission around {company_description} "
                "and would like to contribute to {focus_area}."
            ),
        },
    }


def sample_companies() -> list[Company]:
    return [
        Company(
            name="Anthropic",
            category="Machine Learning",
            url="https://anthropic.com",
            careers_url="https://www.anthropic.com/careers",
            job_board="custom",
            description="AI safety and research",
        ),
        Company(
            name="Protocol Labs",
            category="Decentralized Web3",
            url="https://protocol.ai",
            careers_url="https://protocol.ai/join/",
            job_board="custom",
            description="decentralized web infrastructure",
        ),
        Company(
            name="OpenAI",
            category="Machine Learning",
            url="https://openai.com",
            careers_url="https://openai.com/careers",
            job_board="greenhouse",
            description="AI products and research",
        ),
    ]


def show_dry_run_applications() -> None:
    profile = sample_profile()
    automata = JobApplicationAutomata()

    print("\n" + "=" * 80)
    print("DRY RUN: EXAMPLE CONTENT")
    print("=" * 80)
    print(f"Candidate: {profile['name']} <{profile['email']}>")
    print(f"Skills: {', '.join(profile['skills'])}")

    for index, company in enumerate(sample_companies(), start=1):
        cover_letter = automata.generate_cover_letter(company, profile)
        print("\n" + "#" * 80)
        print(f"APPLICATION #{index}: {company.name}")
        print("#" * 80)
        print(f"Category: {company.category}")
        print(f"Careers URL: {company.careers_url}")
        print(f"Job board: {company.job_board}")
        print("\nCover letter preview:")
        print(cover_letter)
        print("\nDry-run status: no form submitted, no resume uploaded.")


def show_batch_statistics() -> None:
    companies = len(sample_companies())
    print("\n" + "=" * 80)
    print("BATCH PROCESSING ESTIMATE")
    print("=" * 80)
    print(f"Companies: {companies}")
    print("Mode: dry-run only")
    print("Submitted applications: 0")


if __name__ == "__main__":
    show_dry_run_applications()
    show_batch_statistics()
