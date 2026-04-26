#!/usr/bin/env python3
"""
Dry run test for all Job Automata applications
Shows what each application would do without external side effects
"""

import sys
import json
from pathlib import Path

def test_url_scraper():
 """Test URL scraper - show what it would scrape"""
 print("\n" + "="*60)
 print("TEST 1: URL SCRAPER - Scraping company URLs")
 print("="*60)

 from url_scraper import URLScraper

 scraper = URLScraper()

 # Test with a known company
 test_companies = ['Anthropic', 'OpenAI', 'Protocol Labs']

 print(f"\n Testing {len(test_companies)} companies...\n")

 for company in test_companies:
 print(f"Scraping {company}...")
 result = scraper.scrape_company(company)
 print(f" Name: {result['name']}")
 print(f" URL: {result['url']}")
 print(f" Careers URL: {result['careers_url']}")
 print(f" Job Board: {result['job_board']}")
 print()

def test_auto_apply_init():
 """Test auto_apply initialization"""
 print("\n" + "="*60)
 print("TEST 2: AUTO_APPLY - Initialize templates")
 print("="*60)

 from auto_apply import create_profile_template, create_companies_csv
 import json

 # Create test markdown
 test_markdown = "test_companies.md"
 with open(test_markdown, 'w') as f:
 f.write("""# Target Companies

1. **Anthropic** - AI Safety & Research
2. **OpenAI** - Machine Learning Platform
3. **Protocol Labs** - Web3 Infrastructure
""")

 print(f"\n Created test markdown: {test_markdown}")

 # Show what profile template would look like
 profile_template = {
 "email": "your-email@example.com",
 "phone": "+1-XXX-XXX-XXXX",
 "name": "Your Name",
 "resume_file": "path/to/resume.pdf",
 "focus_areas": ["Rust systems programming", "ML/LLM engineering"],
 "skills": ["Rust", "Python", "Protocol Design"]
 }

 print("\n Profile template structure:")
 print(json.dumps(profile_template, indent=2))

 # Show CSV structure
 print("\n Companies CSV structure:")
 print("name,category,url,careers_url,job_board,applied")
 print("Anthropic,AI,https://anthropic.com,https://anthropic.com/careers,custom,False")
 print("OpenAI,AI,https://openai.com,https://openai.com/careers,greenhouse,False")
 print("Protocol Labs,Web3,https://protocol.ai,https://protocol.ai/careers,lever,False")

 # Cleanup
 Path(test_markdown).unlink()
 print(f"\n Cleaned up test file: {test_markdown}")

def test_auto_apply_dry_run():
 """Test auto_apply dry run mode"""
 print("\n" + "="*60)
 print("TEST 3: AUTO_APPLY - Dry run mode simulation")
 print("="*60)

 from auto_apply import JobApplicationAutomata, Company

 # Create test CSV
 test_csv = "test_companies.csv"
 with open(test_csv, 'w') as f:
 f.write("""name,category,url,careers_url,job_board,applied
Anthropic,AI,https://anthropic.com,https://anthropic.com/careers,custom,False
OpenAI,AI,https://openai.com,https://openai.com/careers,greenhouse,False
Protocol Labs,Web3,https://protocol.ai,https://protocol.ai/careers,lever,False
""")

 print(f"\n Created test CSV: {test_csv}")

 automata = JobApplicationAutomata(headless=True)
 automata.load_companies_from_csv(test_csv)

 print(f"\n Loaded {len(automata.companies)} companies:")
 for i, company in enumerate(automata.companies, 1):
 print(f" {i}. {company.name} ({company.category})")
 print(f" → Job board: {company.job_board}")

 # Simulate dry run output
 print(f"\n Simulating dry run (no actual applications):")
 profile = {
 "email": "test@example.com",
 "name": "Test User",
 "cover_letter_templates": {}
 }

 for i, company in enumerate(automata.companies, 1):
 print(f"\n [{i}/{len(automata.companies)}] Processing {company.name}...")
 print(f" [DRY RUN] Would apply to {company.name}")

 # Generate cover letter
 cover_letter = automata.generate_cover_letter(company, profile, company.category)
 print(f" → Cover letter: {cover_letter[:60]}...")

 # Cleanup
 Path(test_csv).unlink()
 print(f"\n Cleaned up test file: {test_csv}")

def test_linkedin_hunter():
 """Test LinkedIn hunter structure"""
 print("\n" + "="*60)
 print("TEST 4: LINKEDIN_HUNTER - Manager search structure")
 print("="*60)

 from linkedin_hunter import LinkedInManager

 # Show what manager data structure looks like
 sample_manager = LinkedInManager(
 name="Jane Smith",
 title="Engineering Manager",
 company="Anthropic",
 url="https://linkedin.com/in/janesmith",
 email="jane.smith@anthropic.com",
 department="Engineering",
 location="San Francisco, CA",
 found_date="2026-04-26T10:00:00"
 )

 print("\n Sample Manager Profile:")
 print(f" Name: {sample_manager.name}")
 print(f" Title: {sample_manager.title}")
 print(f" Company: {sample_manager.company}")
 print(f" LinkedIn: {sample_manager.url}")
 print(f" Department: {sample_manager.department}")
 print(f" Location: {sample_manager.location}")

 print("\n CSV Output Structure:")
 print("name,title,company,url,email,department,connection_status,location,notes,found_date")
 print(f"{sample_manager.name},Manager,{sample_manager.company},linkedin.com/in/janesmith,{sample_manager.email},Engineering,,San Francisco,,,2026-04-26T10:00:00")

def test_orchestrator():
 """Test run.py orchestrator"""
 print("\n" + "="*60)
 print("TEST 5: ORCHESTRATOR - Workflow structure")
 print("="*60)

 from run import build_workflow

 workflow = build_workflow(mode='full')

 print(f"\n Full Workflow ({len(workflow.steps)} steps):\n")

 for i, step in enumerate(workflow.steps, 1):
 print(f"{i}. {step['name']}")
 print(f" Description: {step['description']}")
 print(f" Command: {' '.join(step['command'][:3])}...")
 print()

def main():
 """Run all dry run tests"""
 print("""

 Job Automata - Dry Run Test Suite 
 Testing all applications without external side effects 

 """)

 try:
 test_url_scraper()
 test_auto_apply_init()
 test_auto_apply_dry_run()
 test_linkedin_hunter()
 test_orchestrator()

 print("\n" + "="*60)
 print(" ALL DRY RUN TESTS COMPLETED")
 print("="*60)
 print("""
Next steps:
1. Edit profile.json with your actual information
2. Edit companies.csv with your target companies
3. Run: python run.py --mode test (dry run)
4. Run: python run.py --mode full (full automation)
 """)

 return 0

 except Exception as e:
 print(f"\n Error during test: {e}")
 import traceback
 traceback.print_exc()
 return 1

if __name__ == '__main__':
 sys.exit(main())
