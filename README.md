# 🤖 Job Automata

Automated job application system for applying to 100 target companies. Scrapes URLs, finds hiring managers on LinkedIn, and auto-applies with AI-generated, company-specific cover letters.

## Quick Start

```bash
# 1. Scrape company URLs and job board info
python3 run.py --mode scrape

# 2. Test with dry run (no applications submitted)
python3 run.py --mode test

# 3. Find hiring managers on LinkedIn (optional)
python3 run.py --mode full --linkedin-email your@email.com --linkedin-password yourpass

# 4. Run full auto-apply
python3 run.py --mode apply
```

## Features

✅ **URL Scraping** — Automatically finds careers pages and detects job board platforms (Greenhouse, Lever, Workable, etc.)

✅ **LinkedIn Integration** — Finds hiring managers and recruiters at target companies

✅ **Tailored Applications** — Generates company-specific cover letters based on:
- Your CV (integrated from cv.md)
- Company category (Web3, ML, Systems, etc.)
- Your technical focus areas

✅ **Multi-Board Support** — Handles Greenhouse, Lever, Workable, and custom job boards

✅ **Dry-Run Mode** — Test everything without submitting

✅ **Full Logging** — Track all applications with timestamps and results

## System Components

### `profile.json`
Your application profile with:
- Contact info and links
- 17 years of experience summary
- Technical expertise (Rust, GPU programming, ML, cryptography)
- Recent major projects (Sisyphus, Aurora, Juntos, ProjectFalcon)
- 46-day sprint with 38 repositories
- Tailored cover letter templates

### `auto_apply.py`
Main automation engine:
- Headless Chrome browser automation
- Fills application forms with your profile
- Generates tailored cover letters
- Logs results to CSV

### `url_scraper.py`
Scrapes company data:
- Finds company websites
- Locates careers pages
- Detects job board platforms
- Caches results to avoid duplicate requests

### `linkedin_hunter.py`
LinkedIn integration:
- Logs into LinkedIn
- Searches for recruiters at target companies
- Extracts hiring manager contact info
- Saves to linkedin_managers.csv

### `run.py`
Orchestrator:
- Runs tools in sequence
- Supports different modes: init, scrape, hunt, test, apply, full
- Provides progress tracking

## Modes

```bash
# Initialize (create templates)
python run.py --mode init

# Scrape company URLs
python run.py --mode scrape

# Find LinkedIn managers
python run.py --mode hunt --linkedin-email X --linkedin-password Y

# Test dry run
python run.py --mode test

# Apply to companies
python run.py --mode apply

# Full workflow (all steps)
python run.py --mode full --linkedin-email X --linkedin-password Y
```

## Your Profile

**Name:** Johanna Almeida  
**Experience:** 17 years programming, 9+ years professional  
**Location:** Porto, Portugal  
**GitHub:** https://github.com/JohannaWeb  
**Portfolio:** https://juntos.chat  

### Core Expertise
- **Languages:** Rust, Python, TypeScript, Java, C
- **Systems:** Browser engines, emulators, GPU programming (CUDA, Triton, wgpu)
- **AI/ML:** Language model training, inference optimization (51x speedup), PyTorch
- **Cryptography:** secp256k1, ES256K, ECDSA, AT Protocol
- **Infrastructure:** Kubernetes, AWS, GCP, JVM ecosystem

### Recent Highlights
- **Sisyphus:** 25.6M parameter LLM with 51x inference speedup
- **Aurora:** Rust browser engine with full rendering pipeline
- **Juntos:** Live decentralized chat on AT Protocol
- **ProjectFalcon:** First JVM AT Protocol SDK
- **46-Day Sprint:** 38 public repositories

## Target Companies (100)

Organized by fit:

**Tier 1 (Perfect fit):** Bluesky, Protocol Labs, Servo, Anthropic, Stability AI, HuggingFace, Igalia, Ladybird

**Tier 2 (Strong alignment):** Solana, Akash, Polygon, Thirdweb, Brave, Tauri, Together AI, RunwayML

**Tier 3 (Adjacent skills):** Epic Games, Nvidia, Fly.io, Cloudflare, Teleport, Railway

See `target-companies-100.md` for full list.

## Example Outputs

### companies.csv
```
name,category,url,careers_url,job_board,applied
Bluesky,Web3 / Decentralized,https://bsky.social,https://bsky.social/careers,greenhouse,False
Aurora (Mozilla),Systems,https://mozilla.org,https://mozilla.org/careers,greenhouse,False
...
```

### linkedin_managers.csv
```
name,title,company,url,location,found_date
Jane Smith,Talent Recruiter,Bluesky,https://linkedin.com/in/janesmith,San Francisco,2026-04-24T...
...
```

### applications_YYYYMMDD_HHMMSS.csv
```
timestamp,company,category,url,success,notes
2026-04-24T10:15:30,Bluesky,Web3,https://bsky.social,True,Applied for Senior Protocol Engineer
2026-04-24T10:18:45,Protocol Labs,Web3,https://protocol.ai,True,Applied for Rust Engineer
...
```

## Configuration

### Environment
- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver

### Dependencies
```bash
pip install selenium requests beautifulsoup4
```

### Rate Limiting
- 3 seconds between applications (configurable)
- 1 second between URL searches
- Request caching to avoid duplicates

## Support

- Check logs: `job_applications.log`, `url_scraper.log`, `linkedin_hunter.log`
- Run with `--headless false` to watch browser automation
- Test single company: `python url_scraper.py --company "Bluesky"`

## Important Notes

⚠️ **LinkedIn:**
- May require 2FA verification (use --headless false)
- Email extraction is limited (LinkedIn hides emails)
- Respect LinkedIn's ToS

⚠️ **Job Boards:**
- Some platforms may require human verification
- Applications can be rate-limited
- Check each application's success in output CSV

⚠️ **Responsibly:**
- Only apply to roles you're qualified for
- Don't apply to the same company twice
- Space out applications to avoid appearing spammy

## Next Steps

1. **Review profile.json** — Verify your info is correct
2. **Run scraper** — `python run.py --mode scrape`
3. **Test dry run** — `python run.py --mode test`
4. **Apply** — `python run.py --mode apply`
5. **Track results** — Check `applications_*.csv`

---

**Built with 🤖 Claude Code** — Your CV is fully integrated and ready to use.
