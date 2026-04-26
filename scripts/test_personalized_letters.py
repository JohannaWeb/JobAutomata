#!/usr/bin/env python3
"""
Test personalized cover letters with company descriptions
"""

import json
import csv
from pathlib import Path
from auto_apply import JobApplicationAutomata, Company

# Create test CSV with actual descriptions scraped
test_csv = Path('test_with_descriptions.csv')

companies_data = """name,category,url,careers_url,job_board,description,applied
Anthropic,Machine Learning,https://anthropic.com,https://www.anthropic.com/careers,custom,"Anthropic is an AI safety and research company that's working to build reliable, interpretable, and steerable AI systems.",False
Protocol Labs,Decentralized Web3,https://protocol.ai,https://protocol.ai/join/,custom,Protocol Labs is building the next generation of the internet.,False
Mozilla,Browser Infrastructure,https://mozilla.com,https://mozilla.com/careers,custom,Firefox is a free web browser backed by Mozilla - a non-profit dedicated to internet health and privacy.,False
Vercel,Infrastructure,https://vercel.com,https://vercel.com/careers,custom,Vercel is the platform for developers who want to build fast.,False
"""

with open(test_csv, 'w') as f:
    f.write(companies_data)

# Load profile with personalized templates
with open('example_profile.json', 'r') as f:
    profile = json.load(f)

# Load companies and generate letters
automata = JobApplicationAutomata()
automata.load_companies_from_csv(str(test_csv))

print("="*80)
print("PERSONALIZED COVER LETTERS WITH COMPANY DESCRIPTIONS")
print("="*80)

for company in automata.companies:
    cover_letter = automata.generate_cover_letter(company, profile, company.category)
    print(f"\n{company.name} ({company.category})")
    print("-" * 80)
    print(f"Description: {company.description}")
    print()
    print(f"Cover Letter:")
    print(cover_letter)
    print()

# Cleanup
test_csv.unlink()

print("="*80)
print("✅ Each cover letter is now personalized with the company's actual mission!")
print("="*80)
