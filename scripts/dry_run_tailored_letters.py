#!/usr/bin/env python3
"""
Show what cover letters WOULD be with proper profile templates
"""

import json
from pathlib import Path

# Load the example profile
with open('example_profile.json', 'r') as f:
    profile = json.load(f)

# Sample companies with categories
companies = [
    {'name': 'Anthropic', 'category': 'Machine Learning'},
    {'name': 'OpenAI', 'category': 'Machine Learning'},
    {'name': 'Protocol Labs', 'category': 'Decentralized Web3'},
    {'name': 'Mozilla', 'category': 'Browser Infrastructure'},
    {'name': 'Vercel', 'category': 'Infrastructure'},
    {'name': 'Figma', 'category': 'Design Systems'},
]

def generate_cover_letter(company_name, category, templates):
    """Generate cover letter based on category"""
    category_lower = (category or '').lower()

    if 'decentralized' in category_lower or 'blockchain' in category_lower or 'web3' in category_lower:
        template = templates.get('decentralized_web3', templates.get('default', ''))
        focus_area = 'decentralized protocols and sovereign identity'
    elif 'machine learning' in category_lower or 'ai' in category_lower or 'llm' in category_lower:
        template = templates.get('machine_learning', templates.get('default', ''))
        focus_area = 'machine learning and inference optimization'
    elif 'browser' in category_lower or 'rendering' in category_lower or 'graphics' in category_lower:
        template = templates.get('browser', templates.get('systems_infrastructure', ''))
        focus_area = 'browser engines and GPU rendering'
    elif 'infrastructure' in category_lower or 'devops' in category_lower or 'systems' in category_lower:
        template = templates.get('systems_infrastructure', templates.get('default', ''))
        focus_area = 'systems architecture and infrastructure'
    else:
        template = templates.get('default', '')
        focus_area = 'your mission'

    if not template:
        template = f"I'm interested in joining {company_name}."

    return template.format(
        company_name=company_name,
        focus_area=focus_area
    )

print("="*80)
print("COVER LETTERS - WITH TAILORED TEMPLATES")
print("="*80)
print()

for company in companies:
    letter = generate_cover_letter(
        company['name'],
        company['category'],
        profile['cover_letter_templates']
    )
    print(f"{company['name']} ({company['category']})")
    print("-" * 80)
    print(letter)
    print()
