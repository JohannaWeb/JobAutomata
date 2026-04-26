# Job Automata Setup Guide

Complete guide to scrape URLs, find hiring managers, and auto-apply to 100 companies.

---

## Prerequisites

```bash
pip install selenium requests beautifulsoup4
# Also install ChromeDriver for Selenium
brew install chromedriver # macOS
# or download from: https://chromedriver.chromium.org/
```

---

## Step 1: Scrape Company URLs (url_scraper.py)

This tool extracts company websites and careers pages from the markdown list.

### Usage

```bash
# Scrape all companies from markdown and populate companies.csv
python url_scraper.py --markdown target-companies-100.md --csv companies.csv

# Scrape single company
python url_scraper.py --company "Bluesky"
```

### What it does:
- Searches for each company's website
- Finds their careers/jobs page
- Detects which job board they use (Greenhouse, Lever, Workable, etc.)
- Caches results in `url_cache.json` to avoid duplicate requests
- Updates `companies.csv` with URLs and job board info

### Output
Creates/updates `companies.csv`:
```
name,category,url,careers_url,job_board,applied
Bluesky,Web3 / Decentralized,https://bsky.social,https://bsky.social/careers,greenhouse,False
...
```

---

## Step 2: Initialize Application Profile (auto_apply.py)

Create your application profile template.

```bash
python auto_apply.py --init
```

This creates:

### `profile.json`
Edit with your details:
```json
{
 "email": "your-email@example.com",
 "phone": "+1-XXX-XXX-XXXX",
 "name": "Your Name",
 "linkedin_url": "https://linkedin.com/in/yourprofile",
 "github_url": "https://github.com/yourprofile",
 "resume_file": "path/to/resume.pdf",
 "cover_letter_template": "Looking forward to discussing how my experience in {focus_area} aligns with {company_name}.",
 "focus_areas": ["Rust systems programming", "Decentralized protocols", "ML/LLM engineering"],
 "skills": ["Rust", "Python", "JavaScript", "Protocol Design", "ML/LLaMA fine-tuning"],
 "job_search": {
  "desired_titles": ["systems engineer", "rust engineer", "backend engineer"],
  "excluded_titles": ["intern", "student", "sales", "marketing"],
  "locations": ["remote", "europe", "portugal"],
  "remote_only": false
 }
}
```

If `job_search` is omitted, the legacy behavior is preserved and the first listing is opened.

---

## Step 3: Find Hiring Managers (linkedin_hunter.py)

Find hiring managers and recruiters at each company.

### Requirements
- LinkedIn account
- LinkedIn email/password

### Usage

```bash
# Hunt managers for all companies in CSV
python linkedin_hunter.py \
 --email your.email@example.com \
 --csv companies.csv \
 --output linkedin_managers.csv

# Hunt single company
python linkedin_hunter.py \
 --email your.email@example.com \
 --company "Anthropic"
```

### Output: `linkedin_managers.csv`
```
name,title,company,url,email,department,connection_status,location,notes,found_date
Jane Smith,Talent Recruiter,Anthropic,https://linkedin.com/in/janesmith,jane@anthropic.com,People Ops,Not Connected,San Francisco,Hiring for ML roles,2026-04-24T...
...
```

### Important Notes:
- LinkedIn may rate-limit or require 2FA verification
- Email extraction is limited (LinkedIn hides emails by default)
- Use responsibly and respect LinkedIn's ToS
- Consider using LinkedIn Recruiter API for enterprise access

---

## Step 4: Test Auto-Apply (auto_apply.py)

Run in dry-run mode first to test without submitting.

```bash
# Dry run - shows what would be applied
python auto_apply.py --dry-run --csv companies.csv
```

This logs:
```
[1/100] Processing Bluesky...
[DRY RUN] Would apply to Bluesky (Greenhouse)
[2/100] Processing Protocol Labs...
[DRY RUN] Would apply to Protocol Labs (Lever)
...
```

---

## Step 5: Auto-Apply to Companies

Once verified with dry-run, this opens supported application flows in the browser. Final form submission is not verified.

```bash
# Open application flows
python auto_apply.py --csv companies.csv
```

### What auto_apply.py does:
1. Reads `companies.csv` with URLs and job boards
2. Opens each careers page in headless Chrome
3. Finds job postings matching your profile
4. Fills out application forms with:
 - Your name, email, phone
 - Resume attachment
 - Customized cover letter
5. Submits applications
6. Logs results to `applications_YYYYMMDD_HHMMSS.csv`
7. Marks successful browser actions in the source CSV with `applied=True`, `application_date`, and `notes`

### Application Results
```
timestamp,company,category,url,success,notes
2026-04-24T10:15:30.123456,Bluesky,Web3,https://bsky.social,True,Applied for Senior Protocol Engineer
2026-04-24T10:18:45.654321,Protocol Labs,Web3,https://protocol.ai,True,Applied for Rust Engineer
...
```

---

## Complete Workflow

```bash
# 1. Initialize and scrape URLs (15 min)
python auto_apply.py --init
python url_scraper.py

# 2. Edit profile.json with your details
nano profile.json

# 3. Verify companies.csv looks good
head -20 companies.csv

# 4. (Optional) Find hiring managers (30 min - requires LinkedIn)
LINKEDIN_PASSWORD=Y python linkedin_hunter.py --email X --csv companies.csv

# 5. Test dry run (1 min)
python auto_apply.py --dry-run

# 6. Run applications (varies by job board speed, typically 1-2 hours)
python auto_apply.py

# 7. Check results
cat applications_*.csv | tail -20
```

---

## Monitoring & Troubleshooting

### Logs
- `url_scraper.log` - URL scraping results
- `linkedin_hunter.log` - LinkedIn hunting results
- `job_applications.log` - Application attempt logs

### Common Issues

**"No jobs found for Company X"**
- The job board detection may have failed
- Manually update `job_board` column in CSV
- Some companies use custom job boards not in the list

**"Application failed: Timeout"**
- Increase `delay_seconds` in `auto_apply.py` constructor
- Job board may be slow or rate-limiting

**"LinkedIn login failed"**
- Check credentials
- LinkedIn may require 2FA verification (headless mode can't handle it)
- Run with `--headless false` to interact with 2FA

**"Cover letter not filling"**
- Different job boards have different field names
- May need custom form-filling logic for that board

### Manual Adjustments

Edit `companies.csv` to:
- Set `applied=True` for already-applied companies (skip them)
- Correct `job_board` if auto-detection failed
- Fix URLs if they're wrong

---

## Customization

### Resume/Cover Letter
Update `profile.json` to point to your actual files:
```json
{
 "resume_file": "/home/johanna/resume.pdf",
 "cover_letter_template": "As a Rust systems engineer with {years} years of experience in {focus_area}..."
}
```

### Targeting Specific Categories
Filter in `companies.csv` before running:
```bash
# Apply only to Web3 companies
grep "Web3" companies.csv > companies_web3.csv
python auto_apply.py --csv companies_web3.csv
```

### Job Board Preferences
If you only want to apply via certain boards:
```bash
# Only Greenhouse
grep "greenhouse" companies.csv > companies_greenhouse.csv
python auto_apply.py --csv companies_greenhouse.csv
```

---

## Advanced: Headless Mode & Unattended Runs

To run application flow opening unattended:

```bash
# Run in background with nohup
nohup python auto_apply.py --csv companies.csv > apply.log 2>&1 &

# Monitor progress
tail -f apply.log

# Check results after completion
cat applications_*.csv | wc -l # Count applications
```

---

## Rate Limiting & Ethics

The automata includes:
- **3-second delay between applications** (configurable)
- **1-second delay between searches** in URL scraper
- **Request caching** to avoid duplicate searches
- **Headless Chrome** to minimize server load

Be respectful of:
- Don't apply to the same company twice
- Don't apply to roles you're not qualified for
- Space out applications (avoid hammering servers)
- Use real resume/profile data

---

## Next Steps

1. Run URL scraper to populate careers URLs
2. Edit `profile.json` with your details
3. Run `--dry-run` to verify everything works
4. Run actual applications
5. Monitor `linkedin_managers.csv` for follow-up contacts
6. Track responses in `applications_*.csv`

---

## Support

- Check logs for detailed error messages
- Run with `--headless false` to watch browser automation
- Test single company with `url_scraper.py --company "Bluesky"`

Good luck! 
