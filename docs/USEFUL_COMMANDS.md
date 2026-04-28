# Useful Commands

## Railway & Production Deployment

### 🔐 Security & Access

#### Set Dashboard Access Token
Required for accessing the dashboard when deployed to a remote environment (like Railway).
```bash
# Set this in your environment or Railway Project Settings
DASHBOARD_TOKEN=your-secret-token-here
```
Access the dashboard via: `https://your-app.railway.app/?token=your-secret-token-here`

#### Enable Browser Automation
Required for scraping and auto-apply features on remote servers. Use with caution.
```bash
# Set this in your environment or Railway Project Settings
ENABLE_DANGEROUS_AUTOMATION=true
```

### 🚢 Deployment Commands (Railway CLI)

```bash
# Login to Railway
railway login

# Link current directory to a Railway project
railway link

# View deployment logs
railway logs

# List environment variables
railway variables

# Manually trigger a deployment
railway up

# Open the project in your browser
railway open
```

## Local Development

### 🏃 Running the Dashboard

```bash
# Standard local run
make dashboard

# Run with custom port and automation enabled
PORT=5001 ENABLE_DANGEROUS_AUTOMATION=true make dashboard
```

### 🧹 Cleanup

```bash
# Remove temporary CSV files
make clean

# Full reset (logs, cache, state)
make clean-all
```

## Automation Scripts

```bash
# Test URL scraper for a specific company
python3 -m job_automata.infrastructure.scraping.url_scraper --company "Anthropic"

# Smoke-test the dry-run workflow
python3 scripts/test_dry_run.py

# Generate and preview AI cover letters
python3 scripts/test_personalized_letters.py
```
