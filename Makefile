.PHONY: help init scrape scrape-300 hunt dry-run test-letters apply clean test-scraper venv cv-ui

# Default target
help:
	@echo "Job Automata - Make Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo " make venv Create virtual environment"
	@echo ""
	@echo "Quick workflow:"
	@echo " make init Initialize profile.json and companies.csv templates"
	@echo " make scrape Scrape 100 companies (use COUNT=300 for all)"
	@echo " make scrape-300 Scrape all 300 companies + descriptions"
	@echo " make dry-run Test applications (generates cover letters)"
	@echo " make apply Apply to all companies"
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
	@echo " make scrape COUNT=50 Scrape first 50 companies only"
	@echo " make apply CSV=companies_100.csv Apply using different CSV"

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
	@. venv/bin/activate 2>/dev/null || true && python3 run.py --mode init
	@echo " Created profile.json and companies.csv"
	@echo " Edit profile.json with your contact info and templates"

# Scrape companies (default 100, customize with COUNT=300)
COUNT ?= 100

scrape:
	@if [ "$(COUNT)" = "300" ] || [ "$(COUNT)" = "all" ]; then \
		echo "Scraping 300 companies..."; \
		MARKDOWN=target-companies-300.md; \
		CSV=companies_300.csv; \
	else \
		echo "Scraping $(COUNT) companies..."; \
		MARKDOWN=target-companies-100.md; \
		CSV=companies.csv; \
	fi && \
	. venv/bin/activate 2>/dev/null || true && python3 run.py --mode scrape --markdown $$MARKDOWN --csv $$CSV
	@echo " Scraped companies."

# Scrape all 300 companies (shorthand)
scrape-300:
	@$(MAKE) scrape COUNT=300

# Hunt LinkedIn managers (requires credentials)
hunt:
	@read -p "Enter LinkedIn email: " email; \
	read -s -p "Enter LinkedIn password: " password; \
	echo ""; \
	. venv/bin/activate 2>/dev/null || true && python3 run.py --mode hunt --email $$email --password $$password

# Test dry run (no applications submitted)
dry-run:
	@if [ -f companies_300.csv ]; then CSV=companies_300.csv; else CSV=companies.csv; fi && \
	echo "Running dry run (no applications submitted)..."; \
	. venv/bin/activate 2>/dev/null || true && python3 run.py --mode test --csv $$CSV; \
	echo " Dry run complete. Check logs for details."

# Test scraper on single company
test-scraper:
	@read -p "Enter company name: " company; \
	. venv/bin/activate 2>/dev/null || true && python3 url_scraper.py --company "$$company"

# Generate and preview cover letters
test-letters:
	@echo "Generating personalized cover letters..."
	@. venv/bin/activate 2>/dev/null || true && python3 test_personalized_letters.py

# Apply to all companies
apply:
	@if [ -f companies_300.csv ]; then CSV=companies_300.csv; else CSV=companies.csv; fi && \
	echo " WARNING: This will submit real applications!" && \
	read -p "Press Enter to continue, Ctrl+C to cancel..." && \
	echo "Applying to companies..." && \
	. venv/bin/activate 2>/dev/null || true && python3 run.py --mode apply --csv $$CSV && \
	echo " Applications submitted. Check applications_*.csv for results."

# Run full workflow (init → scrape → test → apply)
full:
	@echo "Running full workflow..."
	@$(MAKE) init
	@$(MAKE) scrape-300
	@$(MAKE) dry-run
	@read -p "Ready to apply? Press Enter, Ctrl+C to cancel..."
	@$(MAKE) apply CSV=companies_300.csv

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f companies.csv companies_*.csv
	@rm -f applications_*.csv
	@rm -f linkedin_managers.csv
	@echo " Cleaned CSV files"

# Clean all generated files
clean-all: clean
	@echo "Cleaning all generated files..."
	@rm -f *.log
	@rm -f url_cache.json
	@echo " Cleaned all generated files"

# Quick check: list available commands
commands:
	@make help

# CV Manager UI (local dev) - deprecated, use dashboard instead
cv-ui:
	@echo "Starting CV Manager UI..."
	@python3 cv_manager.py

# CV Manager UI (production ready) - deprecated, use dashboard instead
cv-ui-prod:
	@echo "Starting CV Manager (production mode)..."
	@PORT=5000 python3 cv_manager.py

# Dashboard UI (new - with dry run and scraper preview)
dashboard:
	@echo "Starting Job Automata Dashboard..."
	@. venv/bin/activate 2>/dev/null || true && python3 web_app.py

# Dashboard UI (production mode)
dashboard-prod:
	@echo "Starting Job Automata Dashboard (production)..."
	@PORT=5000 . venv/bin/activate 2>/dev/null || true && python3 web_app.py

# Setup and run (all-in-one)
setup-and-run: venv init scrape-300 test-letters
	@echo " Setup complete! Next steps:"
	@echo " 1. Review profile.json"
	@echo " 2. Run: make dry-run"
	@echo " 3. Run: make apply"
