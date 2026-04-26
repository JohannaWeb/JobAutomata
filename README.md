# Job Automata

Automated job application system for applying to 300 target companies. Scrapes company websites, fetches real mission statements, generates personalized cover letters, and auto-applies with tailored applications.

## Key Features

AI-Generated Cover Letters: Uses Google Gemini Flash to write unique, personalized cover letters for each company (with template fallback)

Personalized Content: Fetches actual company descriptions and uses your full resume for context

URL Scraping: Finds careers pages and detects job board platforms (Greenhouse, Lever, Workable, etc.)

Company Enrichment: Extracts mission statements, meta descriptions, and about page content

LinkedIn Integration: Finds hiring managers and recruiters at target companies

Multi-Board Support: Handles Greenhouse, Lever, Workable, and custom job boards

Dry-Run Mode: Test everything without submitting

Full Logging: Track all applications with timestamps and results

Cached Requests: Avoids duplicate network requests

## Quick Start

Setup (one time):
```
make install
echo "GEMINI_API_KEY=your_key" > .env
```

Quick workflow:
```
make scrape-300
make test-letters
make dry-run
make apply
```

Or with Python directly:
```
python3 run.py --mode init
python3 run.py --mode scrape --markdown target-companies-300.md
python3 run.py --mode test
python3 run.py --mode apply
```

See AI_SETUP.md for detailed AI cover letter configuration.

## Available Commands

Run `make help` to see all commands, or use:

make init: Create profile.json and companies.csv templates

make scrape: Scrape 100 companies (or specify COUNT=300)

make scrape-300: Scrape all 300 companies

make install: Install dependencies (google-generativeai, python-dotenv)

make dry-run: Test applications without submitting

make apply: Apply to all companies in CSV

make test-scraper: Test scraper on single company

make test-letters: Generate and preview cover letters

make clean: Remove generated CSV files

make help: Show all available commands

## System Architecture

### Core Components

run.py: Orchestrator
Runs tools in sequence
Supports modes: init, scrape, hunt, test, apply, full
Configurable markdown input and CSV output

url_scraper.py: Web Scraping and Enrichment
Finds company websites and careers pages
Detects job board platforms
Scrapes company descriptions (og:description, meta description, /about page)
Uses request caching to avoid duplicates
Hardcoded URLs for 80+ major companies to avoid domain guessing errors

auto_apply.py: Application Engine
Headless Chrome browser automation
Generates cover letters (AI-first, falls back to templates)
Tries Gemini Flash API, silently falls back to templates on any error
Supports {company_description} placeholder in templates
Fills application forms with profile data
Logs results to CSV

linkedin_hunter.py: LinkedIn Integration
Logs into LinkedIn
Searches for recruiters at target companies
Extracts contact information
Saves to linkedin_managers.csv

cover_letter_ai.py: AI Cover Letter Generation
Calls Google Gemini Flash API
Uses full resume plus company data
Generates unique 2-3 paragraph letters per company
Graceful fallback to templates if API fails or quota exceeded

## Data Files

### profile.json

Your Application Profile

Contains:
name, email, phone
linkedin_url, github_url, portfolio_url
years_experience, professional_years, summary
core_skills, technical_expertise
recent_projects (with descriptions)
achievement_highlights
company_alignment (per-company notes)
cover_letter_templates (with {placeholders})
education, languages, methodology

Example:
```
{
 "name": "Your Name",
 "email": "your@email.com",
 "phone": "+1-XXX-XXX-XXXX",
 "resume_file": "resume.pdf",
 "cover_letter_templates": {
 "default": "I'm drawn to {company_name} because {company_description}...",
 "machine_learning": "I'm excited about {company_name}'s work: {company_description}..."
 }
}
```

### companies.csv

Company List with Metadata

Fields: name, category, url, careers_url, job_board, description, applied

Example:
```
name,category,url,careers_url,job_board,description,applied
Anthropic,Machine Learning,https://anthropic.com,https://anthropic.com/careers,custom,"AI safety company...",False
```

## Target Companies

300 companies organized into categories:

Web3 / Blockchain (50): Bluesky, Protocol Labs, Solana, Polygon, Uniswap, MakerDAO, Chainlink, etc.

Browser and Rendering (30): Mozilla, Servo, Ladybird, Brave, Arc, Figma, etc.

AI / Machine Learning (50): Anthropic, OpenAI, Meta AI, Stability AI, HuggingFace, Together AI, etc.

Game Development (40): Epic Games, Unity, Godot, Nvidia, Valve, etc.

Infrastructure / DevOps (50): Vercel, Netlify, Docker, Fly.io, Railway, Databricks, etc.

Identity / Security (35): Auth0, Okta, Signal, Mullvad, 1Password, Teleport, etc.

Data / Databases (30): MongoDB, Elastic, Snowflake, ClickHouse, DuckDB, etc.

Developer Tools (30): GitHub, GitLab, JetBrains, VSCode, Replit, etc.

Other (35): Robotics, hardware, open source foundations, etc.

See target-companies-300.md for the complete list.

## Workflow Modes

### Mode: init

Creates template files. Run this first.

```
python3 run.py --mode init
```

Creates:
profile.json (your application profile)
companies.csv (empty company list)

### Mode: scrape

Fetches company data and descriptions.

```
python3 run.py --mode scrape --markdown target-companies-300.md --csv companies_300.csv
```

For each company:
Finds website domain
Locates careers page
Detects job board platform
Fetches company description (scraped from website)
Caches results

Output: companies.csv with populated URLs and descriptions.

### Mode: hunt

Finds hiring managers on LinkedIn (optional).

```
python3 run.py --mode hunt --linkedin-email your@email.com --linkedin-password yourpass
```

Output: linkedin_managers.csv

### Mode: test

Dry run. Generates cover letters and logs without applying.

```
python3 run.py --mode test --csv companies.csv
```

Output: Preview of what would be sent to each company.

### Mode: apply

Submits real applications via browser automation.

```
python3 run.py --mode apply --csv companies.csv
```

Output: applications_YYYYMMDD_HHMMSS.csv with results.

### Mode: full

Runs all steps in sequence.

```
python3 run.py --mode full --linkedin-email X --linkedin-password Y
```

## Cover Letter Generation

### AI Generation (with Gemini Flash)

If GEMINI_API_KEY is set in .env:
Loads your full resume from cv.md
Fetches company description (scraped from their website)
Calls Gemini Flash with a custom prompt
Generates a 2-3 paragraph, 150-200 word personalized letter
Unique per company (not templated)

### Template Fallback

If AI is disabled, unavailable, or fails:
Uses category-based templates
Customizes with company description
Maintains personalization without API costs

## Configuration

### Environment Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Gemini API Configuration (Optional)

Create .env file:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key at: https://aistudio.google.com/apikey

If you hit the rate limit (429 error), the system automatically falls back to templates. No cost, no worries.

### Key Settings

Rate Limiting:
3 seconds between applications (configurable in auto_apply.py)
1-2 seconds between URL searches
Request caching to avoid duplicates

Browser:
Headless mode by default
Chrome/Chromium required
ChromeDriver auto-detected

Profiles:
Multiple CSV files supported (companies.csv, companies_100.csv, companies_300.csv)
Cache stored in url_cache.json (survives restarts)

## Output Files

### companies.csv

```
name,category,url,careers_url,job_board,description,applied
Anthropic,Machine Learning,https://anthropic.com,...,"AI safety company...",False
```

### linkedin_managers.csv (if using hunt mode)

```
name,title,company,url,email,department,location,found_date
Jane Smith,Engineering Manager,Anthropic,...,jane@anthropic.com,Engineering,SF,2026-04-26T...
```

### applications_YYYYMMDD_HHMMSS.csv

```
timestamp,company,category,url,success,notes
2026-04-26T10:15:30,Anthropic,ML,https://anthropic.com,True,Applied
2026-04-26T10:18:45,Protocol Labs,Web3,https://protocol.ai,True,Applied
```

## Debugging

### Check Logs

```
tail -f job_applications.log
tail -f url_scraper.log
tail -f linkedin_hunter.log
```

### Watch Browser

```
python3 run.py --mode test --headless false
```

### Test Single Company

```
python3 url_scraper.py --company "Anthropic"
```

### Preview Cover Letters

```
make test-letters
```

## Important Notes

### LinkedIn

May require 2FA verification (use --headless false)
Email extraction is limited (LinkedIn hides emails)
Respect LinkedIn's Terms of Service

### Job Boards

Some platforms may require human verification
Applications can be rate-limited
Check output CSV for success/failure status

### Responsible Use

Only apply to roles you're genuinely qualified for
Don't apply to the same company twice
Space out applications to avoid appearing spammy
Review each generated cover letter before applying

### API Rate Limits

Gemini Flash has a free tier with rate limits
If you hit the limit (429 error), the system automatically uses templates
No cost, no worries. You can still apply.
Optional: Add billing at https://console.cloud.google.com/billing for more requests

## Next Steps

1. Edit profile.json: Add your contact info, skills, resume, cover letter templates

2. Run scraper: make scrape-300 (fetches all company data + descriptions)

3. Preview letters: make test-letters (see generated cover letters, or just uses templates)

4. Test dry run: make dry-run (final check before applying)

5. Apply: make apply (submit real applications)

6. Track results: Check applications_*.csv for status

## Support

Issues? Check logs: tail -f *.log

Single company test? python3 url_scraper.py --company "YourCompany"

Cover letter preview? python3 test_ai_letters.py (or make test-letters)

AI setup? See AI_SETUP.md

---