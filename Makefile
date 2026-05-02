.PHONY: help init scrape scrape-2 scrape-300 hunt dry-run test-letters apply apply-interactive clean test-scraper venv cv-ui

# Default target
help:
	@echo "Job Automata - Make Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo " make venv Create virtual environment"
	@echo ""
	@echo "Quick workflow:"
	@echo " make init Initialize data/profile.json and data/companies.csv templates"
	@echo " make scrape Scrape 100 companies (use COUNT=2 for smoke test or COUNT=300 for all)"
	@echo " make scrape-2 Scrape 2 companies for a fast smoke test"
	@echo " make scrape-300 Scrape all 300 companies + descriptions"
	@echo " make dry-run Test applications (generates cover letters)"
	@echo " make apply Open apply flows for all companies"
	@echo " make apply-interactive Open apply flows and pause after each for autofill/review"
	@echo ""
	@echo "Testing & Preview:"
	@echo " make test-scraper Test scraper on single company"
	@echo " make test-letters Generate and preview cover letters"
	@echo " make dashboard Launch modern dashboard with dry run (http://localhost:5000)"
	@echo " make cv-ui Launch legacy CV manager (http://localhost:5000)"
	@echo ""
	@echo "Advanced:"
	@echo " make hunt Find LinkedIn managers (requires credentials)"
	@echo " make full Run complete workflow (init → scrape → test → apply)"
	@echo ""
	@echo "Cleanup:"
	@echo " make clean Remove generated CSV files"
	@echo " make clean-all Remove all generated files (including logs)"
	@echo ""
	@echo "Examples:"
	@echo " make scrape COUNT=2 Scrape 2 companies into data/companies_2.csv"
	@echo " make scrape COUNT=100 Scrape 100 companies into data/companies.csv"
	@echo " make apply CSV=data/companies.csv Use a specific CSV"
	@echo " DASHBOARD_TOKEN=secret make dashboard Run dashboard with token"
	@echo " ENABLE_DANGEROUS_AUTOMATION=true make dashboard Enable browser automation"

# Setup virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt 2>/dev/null || pip install selenium requests beautifulsoup4 google-generativeai python-dotenv
	@echo " Virtual environment created. Run: source venv/bin/activate"

# Install dependencies (shorthand)
install:
	@echo "Installing dependencies..."
	@. venv/bin/activate 2>/dev/null || true && pip install -r requirements.txt
	@echo " Dependencies installed"
	@echo " Create .env file with: GEMINI_API_KEY=your_key (see .env.example)"

# Initialize (create templates)
init:
	@echo "Initializing Job Automata..."
	@. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.workflow --mode init
	@echo " Created data/profile.json and data/companies.csv"
	@echo " Edit data/profile.json with your contact info and templates"

# Scrape companies (default 100, customize with COUNT=2 or COUNT=300)
COUNT ?= 100
CSV ?=

scrape:
	@if [ "$(COUNT)" = "300" ] || [ "$(COUNT)" = "all" ]; then \
		echo "Scraping 300 companies..."; \
		MARKDOWN=data/target-companies-300.md; \
		CSV=data/companies_300.csv; \
	elif [ "$(COUNT)" = "2" ]; then \
		echo "Scraping 2 companies..."; \
		MARKDOWN=data/target-companies-2.md; \
		CSV=data/companies_2.csv; \
	elif [ "$(COUNT)" = "100" ]; then \
		echo "Scraping 100 companies..."; \
		MARKDOWN=data/target-companies-100.md; \
		CSV=data/companies.csv; \
	else \
		echo "Unsupported COUNT=$(COUNT). Use COUNT=2, COUNT=100, or COUNT=300."; \
		exit 1; \
	fi && \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.workflow --mode scrape --markdown $$MARKDOWN --csv $$CSV
	@echo " Scraped companies."

# Scrape 2 companies (shorthand)
scrape-2:
	@$(MAKE) scrape COUNT=2

# Scrape all 300 companies (shorthand)
scrape-300:
	@$(MAKE) scrape COUNT=300

# Hunt LinkedIn managers (requires credentials)
hunt:
	@if [ -z "$$LINKEDIN_EMAIL" ] || [ -z "$$LINKEDIN_PASSWORD" ]; then \
		echo "Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your environment. Credentials are not accepted on argv."; \
		exit 1; \
	fi
	@if [ -n "$(CSV)" ]; then SELECTED_CSV="$(CSV)"; elif [ -f data/companies_300.csv ]; then SELECTED_CSV=data/companies_300.csv; else SELECTED_CSV=data/companies.csv; fi && \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.workflow --mode hunt --linkedin-email "$$LINKEDIN_EMAIL" --csv $$SELECTED_CSV

# Test dry run (no applications submitted)
dry-run:
	@if [ -n "$(CSV)" ]; then SELECTED_CSV="$(CSV)"; elif [ -f data/companies_300.csv ]; then SELECTED_CSV=data/companies_300.csv; else SELECTED_CSV=data/companies.csv; fi && \
	echo "Running dry run with $$SELECTED_CSV (no applications submitted)..."; \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.workflow --mode test --csv $$SELECTED_CSV; \
	echo " Dry run complete. Check logs for details."

# Test scraper on single company
test-scraper:
	@read -p "Enter company name: " company; \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.infrastructure.scraping.url_scraper --company "$$company"

# Generate and preview cover letters
test-letters:
	@echo "Generating personalized cover letters..."
	@. venv/bin/activate 2>/dev/null || true && python3 scripts/test_personalized_letters.py

# Apply to all companies
apply:
	@if [ -n "$(CSV)" ]; then SELECTED_CSV="$(CSV)"; elif [ -f data/companies_300.csv ]; then SELECTED_CSV=data/companies_300.csv; else SELECTED_CSV=data/companies.csv; fi && \
	echo " WARNING: This opens real application flows from $$SELECTED_CSV in a browser." && \
	echo " It does not verify final form submission." && \
	printf "Press Enter to continue, Ctrl+C to cancel..." && \
	read CONFIRM && \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.workflow --mode apply --csv $$SELECTED_CSV

# Interactive apply: open each flow, autofill on Enter, then wait for human review/manual submit
apply-interactive:
	@if [ -n "$(CSV)" ]; then SELECTED_CSV="$(CSV)"; elif [ -f data/companies_300.csv ]; then SELECTED_CSV=data/companies_300.csv; else SELECTED_CSV=data/companies.csv; fi && \
	echo " WARNING: This opens visible browser application flows from $$SELECTED_CSV." && \
	echo " Controls: Enter=autofill, y=I submitted it, n=not submitted, q=quit." && \
	echo " You review and submit manually; the script marks applied only after y." && \
	printf "Press Enter to continue, Ctrl+C to cancel..." && \
	read CONFIRM && \
	. venv/bin/activate 2>/dev/null || true && python3 -m job_automata.application.auto_apply --pause-each --csv $$SELECTED_CSV

# Run full workflow (init → scrape → test → apply)
full:
	@echo "Running full workflow..."
	@$(MAKE) init
	@$(MAKE) scrape-300
	@$(MAKE) dry-run
	@read -p "Ready to open apply flows? Press Enter, Ctrl+C to cancel..."
	@$(MAKE) apply CSV=data/companies_300.csv

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f data/companies.csv data/companies_*.csv
	@rm -f var/applications/*.csv
	@rm -f linkedin_managers.csv
	@echo " Cleaned CSV files"

# Clean all generated files
clean-all: clean
	@echo "Cleaning all generated files..."
	@rm -f var/log/*.log
	@rm -f var/cache/url_cache.json
	@rm -f var/state/*
	@echo " Cleaned all generated files"

# Quick check: list available commands
commands:
	@make help

# CV Manager UI (local dev) - deprecated, use dashboard instead
cv-ui:
	@echo "Starting CV Manager UI..."
	@python3 -m job_automata.presentation.web.cv_manager

# CV Manager UI (production ready) - deprecated, use dashboard instead
cv-ui-prod:
	@echo "Starting CV Manager (production mode)..."
	@PORT=5000 python3 -m job_automata.presentation.web.cv_manager

# Dashboard UI (new - with dry run and scraper preview)
dashboard:
	@echo "Starting Job Automata Dashboard..."
	@. venv/bin/activate 2>/dev/null || true && \
	ENABLE_DANGEROUS_AUTOMATION=$${ENABLE_DANGEROUS_AUTOMATION:-true} \
	DASHBOARD_TOKEN=$${DASHBOARD_TOKEN} \
	python3 -m job_automata.presentation.web.app

# Dashboard UI (production mode)
dashboard-prod:
	@echo "Starting Job Automata Dashboard (production)..."
	@. venv/bin/activate 2>/dev/null || true && \
	PORT=$${PORT:-5000} \
	ENABLE_DANGEROUS_AUTOMATION=$${ENABLE_DANGEROUS_AUTOMATION:-false} \
	DASHBOARD_TOKEN=$${DASHBOARD_TOKEN} \
	python3 -m job_automata.presentation.web.app

# Setup and run (all-in-one)
setup-and-run: venv init scrape-300 test-letters
	@echo " Setup complete! Next steps:"
	@echo " 1. Review data/profile.json"
	@echo " 2. Run: make dry-run"
	@echo " 3. Run: make apply"
