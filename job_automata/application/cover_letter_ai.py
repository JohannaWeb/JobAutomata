#!/usr/bin/env python3
"""
AI-powered cover letter generation using Gemini Flash
Generates personalized cover letters using the full resume and company data
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

from job_automata.config import DEFAULT_PROFILE

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@dataclass
class Company:
    """Simplified Company dataclass for type hints"""
    name: str
    category: str
    description: Optional[str] = None
    url: Optional[str] = None


def load_env():
    """Load environment variables from .env file"""
    if HAS_DOTENV:
        load_dotenv()


def get_gemini_key() -> Optional[str]:
    """Get Gemini API key from environment"""
    load_env()
    return os.getenv('GEMINI_API_KEY')


def generate_cover_letter_ai(company: Company, profile: dict) -> str:
    """
    Generate a personalized cover letter using Gemini Flash

    Args:
        company: Company dataclass with name, category, description
        profile: User profile dict with resume_content, summary, skills, projects

    Returns:
        Generated cover letter text (2-3 paragraphs, ~150-200 words)

    Raises:
        RuntimeError: If Gemini API key not found or call fails
    """

    if not HAS_GENAI:
        raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

    api_key = get_gemini_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set. Create .env file with your key.")

    # Configure API
    genai.configure(api_key=api_key)

    # Extract resume data
    resume_content = profile.get('resume_content', '')
    name = profile.get('name', 'Applicant')
    summary = profile.get('summary', '')
    core_skills = profile.get('core_skills', [])
    recent_projects = profile.get('recent_projects', [])

    # Format skills
    skills_text = ', '.join(core_skills[:8]) if core_skills else 'various technical skills'

    # Format projects
    projects_text = ''
    if recent_projects:
        projects_text = '\n'.join([
            f"- {p.get('name', 'Project')}: {p.get('description', '')[:100]}"
            for p in recent_projects[:3]
        ])

    # Build prompt with context
    prompt = f"""Write a compelling, personalized cover letter for a job application.

APPLICANT PROFILE:
Name: {name}
Summary: {summary}

Key Skills: {skills_text}

Recent Work:
{projects_text}

Full Resume:
{resume_content}

---

TARGET COMPANY:
Name: {company.name}
Category: {company.category}
Description: {company.description or 'No description available'}
Website: {company.url or 'Website not provided'}

---

TASK:
Write a 2-3 paragraph cover letter (150-200 words) that:
1. Opens with genuine interest in the company based on their mission/description
2. Highlights 1-2 specific skills or projects from the resume that align with their category
3. Closes with enthusiasm about contributing to their goals

The letter should feel personal and authentic, not generic. Use the applicant's voice and background.
Do NOT include salutation (Dear X) or closing (Sincerely, X). Just the body paragraphs.
Do NOT mention specific job titles or positions - keep it general.
"""

    try:
        # Use Gemini Flash (faster, cheaper)
        model = genai.GenerativeModel('gemini-2.0-flash')

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500,
                top_p=0.9,
            ),
        )

        cover_letter = response.text.strip()
        logger.info(f"Generated AI cover letter for {company.name} ({len(cover_letter)} chars)")
        return cover_letter

    except Exception as e:
        logger.error(f"Failed to generate cover letter via Gemini: {e}")
        raise RuntimeError(f"Gemini API call failed: {e}")


def main() -> int:
    # Test mode
    import json

    test_company = Company(
        name='Anthropic',
        category='Machine Learning',
        description='Anthropic is an AI safety and research company building reliable, interpretable AI systems.',
        url='https://anthropic.com'
    )

    # Load test profile
    if DEFAULT_PROFILE.exists():
        with DEFAULT_PROFILE.open('r') as f:
            test_profile = json.load(f)
    else:
        test_profile = {
            'name': 'Test User',
            'summary': 'Software engineer with AI/ML expertise',
            'core_skills': ['Python', 'ML', 'Systems'],
            'resume_content': 'Sample resume content',
            'recent_projects': []
        }

    try:
        letter = generate_cover_letter_ai(test_company, test_profile)
        print(f"\n{'='*60}")
        print(f"Generated Cover Letter for {test_company.name}")
        print(f"{'='*60}\n")
        print(letter)
        print(f"\n{'='*60}")
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nTo test, ensure:")
        print("  1. pip install google-generativeai python-dotenv")
        print("  2. Create .env file with: GEMINI_API_KEY=your_key")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
