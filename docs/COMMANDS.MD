# Commands

Run from the project root.

## Setup

```bash
make venv
source venv/bin/activate
make install
make init
```

## Scrape Companies

```bash
make scrape-2
make scrape
make scrape-300
```

Outputs:

```text
data/companies_2.csv
data/companies.csv
data/companies_300.csv
```

## Dry Run

Test without submitting applications:

```bash
make dry-run CSV=data/companies_2.csv
make dry-run CSV=data/companies.csv
make dry-run CSV=data/companies_300.csv
```

## Apply

Interactive autofill workflow. Opens each job, waits while you solve captcha/login, runs autofill when you press Enter, then asks whether you submitted it before moving to the next row:

```bash
make apply-interactive CSV=data/companies_100.csv
make apply-interactive CSV=data/companies_300_jobs.csv
make apply-interactive CSV=data/companies_2.csv
make apply-interactive CSV=data/companies.csv
make apply-interactive CSV=data/companies_300.csv
```

Controls:

```text
Enter = run autofill
y     = I submitted it
n     = not submitted
q     = quit
```

One-job test command:

```bash
python3 -m job_automata.application.auto_apply --pause-each --one --csv data/companies_100.csv
```

Mark already-applied rows:

```bash
python3 scripts/mark_applied.py --csv data/companies_100.csv --first 5
python3 scripts/mark_applied.py --csv data/companies_100.csv --name "Airbnb"
python3 scripts/sync_applied.py --source data/companies_100.csv --target data/companies_300_jobs.csv --company-token
```

Non-interactive apply flow opener:

```bash
make apply CSV=data/companies_100.csv
make apply CSV=data/companies_300_jobs.csv
make apply CSV=data/companies_2.csv
make apply CSV=data/companies.csv
make apply CSV=data/companies_300.csv
```

## Dashboard

```bash
make dashboard
```

## Useful Tests

```bash
make test-letters
python3 -m job_automata.infrastructure.scraping.url_scraper --company "Anthropic"
pytest
```

## Clean

```bash
make clean
make clean-all
```
