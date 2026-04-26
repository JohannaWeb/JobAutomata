#!/usr/bin/env python3
"""
Dry run - Cover letters only
"""

import csv
from pathlib import Path

# Create sample companies CSV
companies_data = """name,category,url,careers_url,job_board,applied
Anthropic,Machine Learning,https://anthropic.com,https://www.anthropic.com/careers,custom,False
OpenAI,Machine Learning,https://openai.com,https://openai.com/careers,greenhouse,False
Protocol Labs,Decentralized Web3,https://protocol.ai,https://protocol.ai/join/,custom,False
Figma,Design Systems,https://figma.com,https://figma.com/careers,lever,False
Mozilla,Browser Infrastructure,https://mozilla.org,https://careers.mozilla.org,custom,False
Vercel,Infrastructure,https://vercel.com,https://vercel.com/careers,custom,False
"""

# Write sample CSV
csv_path = Path('sample_companies.csv')
with open(csv_path, 'w') as f:
    f.write(companies_data)

# Load and generate cover letters
from auto_apply import JobApplicationAutomata

automata = JobApplicationAutomata()
automata.load_companies_from_csv(str(csv_path))

profile = {
    "name": "Your Name",
    "cover_letter_templates": {}
}

print("="*80)
print("COVER LETTERS - DRY RUN")
print("="*80)

for company in automata.companies:
    cover_letter = automata.generate_cover_letter(company, profile, company.category)
    print(f"\n{company.name} ({company.category})")
    print("-" * 80)
    print(cover_letter)
    print()

# Cleanup
csv_path.unlink()
