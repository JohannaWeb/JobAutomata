#!/usr/bin/env python3
"""
Test AI cover letter generation with sample companies
Shows the difference between AI-generated and template-based letters
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from cover_letter_ai import generate_cover_letter_ai, HAS_GENAI
except ImportError:
    HAS_GENAI = False

@dataclass
class Company:
    name: str
    category: str
    description: str
    url: str = ""


def load_profile():
    """Load profile.json"""
    if Path('profile.json').exists():
        with open('profile.json', 'r') as f:
            return json.load(f)
    else:
        print("❌ profile.json not found. Run: make init")
        sys.exit(1)


def test_ai_generation():
    """Test AI cover letter generation"""

    if not HAS_GENAI:
        print("❌ google-generativeai not installed")
        print("   Run: pip install google-generativeai python-dotenv")
        return False

    profile = load_profile()

    # Test companies with real descriptions
    test_companies = [
        Company(
            name='Anthropic',
            category='Machine Learning',
            description='Anthropic is an AI safety and research company that\'s working to build reliable, interpretable, and steerable AI systems.',
            url='https://anthropic.com'
        ),
        Company(
            name='Protocol Labs',
            category='Decentralized Web3',
            description='Protocol Labs is building the next generation of the internet.',
            url='https://protocol.ai'
        ),
        Company(
            name='Vercel',
            category='Infrastructure',
            description='Vercel is the platform for developers who want to build fast.',
            url='https://vercel.com'
        ),
    ]

    print("="*80)
    print("AI COVER LETTER GENERATION TEST")
    print("="*80)
    print()

    success_count = 0
    failed_count = 0

    for company in test_companies:
        print(f"\n{'─'*80}")
        print(f"Company: {company.name} ({company.category})")
        print(f"Description: {company.description[:80]}...")
        print(f"{'─'*80}\n")

        try:
            # Generate AI letter
            letter = generate_cover_letter_ai(company, profile)

            print("✅ AI-Generated Letter:")
            print()
            print(letter)
            print()
            success_count += 1

        except Exception as e:
            print(f"❌ Failed to generate letter: {e}")
            print()
            print("Possible fixes:")
            print("  1. Create .env file: echo 'GEMINI_API_KEY=your_key' > .env")
            print("  2. Verify API key at: https://aistudio.google.com/apikey")
            print("  3. Ensure google-generativeai is installed: pip install google-generativeai")
            print()
            failed_count += 1

    print()
    print("="*80)
    print(f"Results: {success_count} ✅  |  {failed_count} ❌")
    print("="*80)

    if failed_count == 0:
        print("\n✨ AI cover letter generation is working!")
        print("   Next: make dry-run")
        return True
    else:
        return False


if __name__ == '__main__':
    success = test_ai_generation()
    sys.exit(0 if success else 1)
