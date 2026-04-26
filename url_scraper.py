#!/usr/bin/env python3
"""
URL Scraper for Company Careers Pages
Fetches company websites and careers page URLs
"""

import csv
import logging
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s - %(levelname)s - %(message)s',
 handlers=[
 logging.FileHandler('url_scraper.log'),
 logging.StreamHandler()
 ]
)
logger = logging.getLogger(__name__)

class URLScraper:
 """Scrapes company websites and careers pages"""

 def __init__(self, headless: bool = True):
 self.headless = headless
 self.session = requests.Session()
 self.session.headers.update({
 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
 })
 self.cache_file = Path('url_cache.json')
 self.cache = self._load_cache()

 # Known company URLs (manual mapping for speed)
 self.known_urls = {
 'Bluesky': 'https://bsky.social',
 'Protocol Labs': 'https://protocol.ai',
 'Akash Network': 'https://akash.network',
 'Solana Labs': 'https://solana.com',
 'Polygon': 'https://polygon.technology',
 'Starkware': 'https://starkware.co',
 'Thirdweb': 'https://thirdweb.com',
 'Lens Protocol': 'https://lens.xyz',
 'ENS (Ethereum Name Service)': 'https://ens.domains',
 'Safe{Wallet}': 'https://safe.global',
 'Optimism': 'https://optimism.io',
 'Arbitrum': 'https://arbitrum.io',
 'Aleo': 'https://aleo.org',
 'Status': 'https://status.im',
 'Zcash': 'https://z.cash',
 'Cosmos': 'https://cosmos.network',
 'Servo': 'https://servo.org',
 'Ladybird': 'https://ladybird.org',
 'Igalia': 'https://igalia.com',
 'Firefox/Mozilla': 'https://mozilla.org',
 'Apple WebKit': 'https://webkit.org',
 'Brave': 'https://brave.com',
 'Arc': 'https://arc.net',
 'Zed': 'https://zed.dev',
 'Figma': 'https://figma.com',
 'Tauri': 'https://tauri.app',
 'Dioxus': 'https://dioxuslabs.com',
 'Anthropic': 'https://anthropic.com',
 'OpenAI': 'https://openai.com',
 'Meta AI': 'https://ai.meta.com',
 'Stability AI': 'https://stability.ai',
 'HuggingFace': 'https://huggingface.co',
 'Together AI': 'https://www.together.ai',
 'Modal': 'https://modal.com',
 'Replicate': 'https://replicate.com',
 'Weights & Biases': 'https://wandb.ai',
 'Cohere': 'https://cohere.com',
 'Mistral AI': 'https://mistral.ai',
 'Scale AI': 'https://scale.com',
 'Eleven Labs': 'https://elevenlabs.io',
 'RunwayML': 'https://runwayml.com',
 'Databricks': 'https://databricks.com',
 'Vercel': 'https://vercel.com',
 'Netlify': 'https://netlify.com',
 'Docker': 'https://docker.com',
 'Canonical': 'https://canonical.com',
 'Red Hat': 'https://redhat.com',
 'HashiCorp': 'https://hashicorp.com',
 'CloudFlare': 'https://cloudflare.com',
 'Auth0': 'https://auth0.com',
 'Okta': 'https://okta.com',
 'Zoom': 'https://zoom.us',
 'Signal': 'https://signal.org',
 'Mullvad': 'https://mullvad.net',
 '1Password': 'https://1password.com',
 'Teleport': 'https://goteleport.com',
 'Snyk': 'https://snyk.io',
 'Wiz': 'https://wiz.io',
 'Zscaler': 'https://zscaler.com',
 'Vanta': 'https://vanta.com',
 'Rubrik': 'https://rubrik.com',
 'Fastly': 'https://fastly.com',
 'Akamai': 'https://akamai.com',
 'Cisco': 'https://cisco.com',
 'Arista Networks': 'https://arista.com',
 'Juniper Networks': 'https://juniper.net',
 'PagerDuty': 'https://pagerduty.com',
 'Datadog': 'https://datadoghq.com',
 'Honeycomb.io': 'https://honeycomb.io',
 'Linux Foundation': 'https://linuxfoundation.org',
 # Additional Web3/Blockchain
 'Aptos': 'https://aptos.dev',
 'Sui': 'https://sui.io',
 'Near Protocol': 'https://near.org',
 'Avalanche': 'https://avax.network',
 'Fantom': 'https://fantom.foundation',
 'Hedera': 'https://hedera.com',
 'Chainlink': 'https://chain.link',
 'Uniswap Labs': 'https://uniswap.org',
 'Curve Finance': 'https://curve.fi',
 'Lido': 'https://lido.fi',
 'MakerDAO': 'https://makerdao.com',
 'Compound Labs': 'https://compound.finance',
 'Aave': 'https://aave.com',
 'dYdX': 'https://dydx.trade',
 '0x Protocol': 'https://0x.org',
 'Rainbow Wallet': 'https://rainbow.me',
 'MetaMask (ConsenSys)': 'https://metamask.io',
 'Phantom': 'https://phantom.app',
 'Ledger': 'https://ledger.com',
 'Gnosis': 'https://gnosis.io',
 'Synthetix': 'https://synthetix.io',
 'Yearn Finance': 'https://yearn.finance',
 'Balancer': 'https://balancer.fi',
 'Osmosis': 'https://osmosis.zone',
 'Jupiter': 'https://jup.ag',
 'Raydium': 'https://raydium.io',
 'Magic Eden': 'https://magiceden.io',
 'OpenSea': 'https://opensea.io',
 'Foundation': 'https://foundation.app',
 'SuperRare': 'https://superrare.com',
 'Audius': 'https://audius.co',
 # Game/Graphics
 'Epic Games': 'https://epicgames.com',
 'Unity Technologies': 'https://unity.com',
 'Godot Engine': 'https://godotengine.org',
 'Valve': 'https://valvesoftware.com',
 'Blender': 'https://blender.org',
 'Unreal Engine': 'https://unrealengine.com',
 # Infrastructure/Cloud
 'Fly.io': 'https://fly.io',
 'Replit': 'https://replit.com',
 'Railway': 'https://railway.app',
 'Render': 'https://render.com',
 'DigitalOcean': 'https://digitalocean.com',
 'CoreWeave': 'https://coreweave.com',
 'AWS': 'https://aws.amazon.com',
 'Google Cloud': 'https://cloud.google.com',
 'Microsoft Azure': 'https://azure.microsoft.com',
 # Developer Tools
 'GitHub': 'https://github.com',
 'GitLab': 'https://gitlab.com',
 'Atlassian': 'https://atlassian.com',
 'JetBrains': 'https://jetbrains.com',
 'Slack': 'https://slack.com',
 'Discord': 'https://discord.com',
 'Notion': 'https://notion.so',
 'Airtable': 'https://airtable.com',
 'Stripe': 'https://stripe.com',
 'Twilio': 'https://twilio.com',
 # Databases/Data
 'MongoDB': 'https://mongodb.com',
 'Elastic': 'https://elastic.co',
 'Snowflake': 'https://snowflake.com',
 'ClickHouse': 'https://clickhouse.com',
 'DuckDB': 'https://duckdb.org',
 'InfluxDB': 'https://influxdata.com',
 'TimescaleDB': 'https://timescale.com',
 'Prometheus': 'https://prometheus.io',
 'Grafana': 'https://grafana.com',
 'New Relic': 'https://newrelic.com',
 # ML/AI additions
 'Hugging Face': 'https://huggingface.co',
 'TensorFlow': 'https://tensorflow.org',
 'PyTorch': 'https://pytorch.org',
 'JAX': 'https://jax.readthedocs.io',
 # Remove problematic entries or fix them
 'Bandcamp': 'https://bandcamp.com',
 'Nostr Development': 'https://nostr.com',
 'Interop': 'https://interop.com',
 }

 def _load_cache(self) -> Dict:
 """Load cached URLs to avoid duplicate requests"""
 if self.cache_file.exists():
 with open(self.cache_file, 'r') as f:
 return json.load(f)
 return {}

 def _save_cache(self) -> None:
 """Save cache to file"""
 with open(self.cache_file, 'w') as f:
 json.dump(self.cache, f, indent=2)

 def google_search(self, company_name: str, query_suffix: str = "careers") -> Optional[str]:
 """Try common domain patterns for company URL"""
 cache_key = f"{company_name}_{query_suffix}"
 if cache_key in self.cache:
 return self.cache[cache_key]

 # Generate domain variations
 name_parts = company_name.lower().replace(' ', '-').replace('/', '').replace('{', '').replace('}', '')

 domains_to_try = [
 f"{name_parts}.com",
 f"{name_parts}.io",
 f"{name_parts}.ai",
 f"{name_parts}.xyz",
 f"{name_parts}.co",
 name_parts.replace('-', '').replace('_', '') + ".com", # Remove separators
 name_parts.replace('-', '').replace('_', '') + ".io",
 ]

 for domain in domains_to_try:
 for protocol in ["https://", "http://"]:
 url = f"{protocol}{domain}"
 try:
 response = self.session.head(url, timeout=5, allow_redirects=True)
 if response.status_code < 400:
 self.cache[cache_key] = url
 self._save_cache()
 logger.info(f"Found domain for {company_name}: {url}")
 return url
 except:
 pass

 logger.warning(f"Could not find domain for {company_name}")
 return None

 def find_careers_page(self, base_url: str) -> Optional[str]:
 """Find careers/jobs page on company website"""
 if not base_url:
 return None

 cache_key = f"{base_url}_careers"
 if cache_key in self.cache:
 return self.cache[cache_key]

 # Common careers page paths
 common_paths = [
 '/careers',
 '/jobs',
 '/apply',
 '/hiring',
 '/work-with-us',
 '/join-us',
 '/career',
 '/employment',
 ]

 # Ensure URL has protocol
 if not base_url.startswith('http'):
 base_url = f"https://{base_url}"

 try:
 response = self.session.get(base_url, timeout=10, allow_redirects=True)
 soup = BeautifulSoup(response.content, 'html.parser')

 # Look for careers/jobs links in HTML
 for link in soup.find_all('a', href=True):
 href = link['href'].lower()
 text = link.get_text().lower()

 if any(keyword in href or keyword in text for keyword in ['careers', 'jobs', 'hiring', 'join']):
 careers_url = urljoin(base_url, link['href'])
 self.cache[cache_key] = careers_url
 self._save_cache()
 return careers_url

 # Try common paths
 for path in common_paths:
 test_url = urljoin(base_url, path)
 try:
 test_response = self.session.head(test_url, timeout=5, allow_redirects=True)
 if test_response.status_code == 200:
 self.cache[cache_key] = test_url
 self._save_cache()
 return test_url
 except:
 pass

 except Exception as e:
 logger.warning(f"Failed to find careers page for {base_url}: {e}")

 return None

 def detect_job_board(self, careers_url: str) -> Optional[str]:
 """Detect which job board platform the company uses"""
 if not careers_url:
 return None

 cache_key = f"{careers_url}_board"
 if cache_key in self.cache:
 return self.cache[cache_key]

 try:
 response = self.session.get(careers_url, timeout=10)
 content = response.text.lower()

 # Detect job boards by common identifiers
 boards = {
 'greenhouse': ['greenhouse.io', 'grnhse', 'greenhouse'],
 'lever': ['lever.co', 'lever--', 'lever-jobs'],
 'workable': ['workable.com', 'workable-js', 'apply.workable'],
 'ashby': ['ashby.com', 'ashby-job'],
 'boards': ['boards.greenhouse.io'],
 'jobvite': ['jobvite.com', 'jobvite'],
 'bamboo': ['bamboohr', 'bamboo-hr'],
 'breezy': ['breezy.hr', 'breezy_'],
 'ats': ['applicantstack', 'taleo', 'successfactors'],
 }

 for board, identifiers in boards.items():
 if any(identifier in content for identifier in identifiers):
 self.cache[cache_key] = board
 self._save_cache()
 return board

 except Exception as e:
 logger.warning(f"Failed to detect job board for {careers_url}: {e}")

 self.cache[cache_key] = 'custom'
 self._save_cache()
 return 'custom'

 def scrape_company_description(self, base_url: str) -> Optional[str]:
 """Scrape company mission/description from homepage and about page"""
 if not base_url:
 return None

 cache_key = f"{base_url}_description"
 if cache_key in self.cache:
 return self.cache[cache_key]

 try:
 # Try homepage meta tags first
 response = self.session.get(base_url, timeout=10)
 soup = BeautifulSoup(response.content, 'html.parser')

 # Try og:description (Open Graph, usually best)
 og_desc = soup.find('meta', property='og:description')
 if og_desc and og_desc.get('content'):
 desc = og_desc['content'].strip()
 self.cache[cache_key] = desc
 self._save_cache()
 return desc

 # Fall back to standard meta description
 meta_desc = soup.find('meta', {'name': 'description'})
 if meta_desc and meta_desc.get('content'):
 desc = meta_desc['content'].strip()
 self.cache[cache_key] = desc
 self._save_cache()
 return desc

 # Try first meaningful paragraph on homepage
 paragraphs = soup.find_all('p', limit=3)
 for p in paragraphs:
 text = p.get_text().strip()
 if len(text) > 20 and len(text) < 300:
 self.cache[cache_key] = text
 self._save_cache()
 return text

 # Try /about page
 about_url = urljoin(base_url, '/about')
 try:
 about_response = self.session.get(about_url, timeout=10)
 about_soup = BeautifulSoup(about_response.content, 'html.parser')
 about_paragraphs = about_soup.find_all('p', limit=2)
 for p in about_paragraphs:
 text = p.get_text().strip()
 if len(text) > 20 and len(text) < 300:
 self.cache[cache_key] = text
 self._save_cache()
 return text
 except:
 pass

 except Exception as e:
 logger.warning(f"Failed to scrape description for {base_url}: {e}")

 return None

 def scrape_company(self, company_name: str) -> Dict:
 """Scrape all info for a company"""
 logger.info(f"Scraping {company_name}...")

 # Check known URLs first (instant)
 website = self.known_urls.get(company_name)

 # Fall back to domain guessing if not in known list
 if not website:
 website = self.google_search(company_name)

 if not website:
 logger.warning(f"Could not find website for {company_name}")
 return {'name': company_name, 'url': None, 'careers_url': None, 'job_board': None}

 # Clean up URL
 if not website.startswith('http'):
 website = f"https://{website}"

 parsed = urlparse(website)
 domain = parsed.netloc
 if domain.startswith('www.'):
 domain = domain[4:]

 website = f"https://{domain}"

 time.sleep(0.5) # Reduced rate limiting

 # Find careers page
 careers_url = self.find_careers_page(website)

 # Detect job board
 job_board = self.detect_job_board(careers_url) if careers_url else None

 # Scrape company description
 description = self.scrape_company_description(website) if website else None

 result = {
 'name': company_name,
 'url': website,
 'careers_url': careers_url,
 'job_board': job_board,
 'description': description
 }

 logger.info(f"Found: {result}")
 return result

 def scrape_from_markdown(self, markdown_path: str) -> List[Dict]:
 """Extract company names from markdown and scrape URLs"""
 companies = []
 results = []

 with open(markdown_path, 'r') as f:
 for line in f:
 line = line.strip()
 # Parse "1. **Company**" or "1. **Company** - Description"
 if line and line[0].isdigit() and '**' in line:
 try:
 parts = line.split('**')
 if len(parts) >= 2:
 name = parts[1].strip()
 companies.append(name)
 except Exception:
 continue

 logger.info(f"Found {len(companies)} companies in markdown")

 for i, company in enumerate(companies, 1):
 try:
 logger.info(f"[{i}/{len(companies)}] Scraping {company}...")
 result = self.scrape_company(company)
 results.append(result)
 time.sleep(2) # Rate limiting between searches
 except Exception as e:
 logger.error(f"Error scraping {company}: {e}")
 results.append({'name': company, 'url': None, 'careers_url': None, 'job_board': None})

 logger.info(f"Completed scraping: {len(results)} companies processed")
 return results

 def update_csv(self, results: List[Dict], csv_path: str) -> None:
 """Update CSV file with scraped URLs"""
 # Load existing CSV or create new one
 existing = {}
 if Path(csv_path).exists():
 with open(csv_path, 'r') as f:
 reader = csv.DictReader(f)
 for row in reader:
 existing[row['name']] = row

 # Merge with scraped results
 merged = []
 for result in results:
 row = existing.get(result['name'], {
 'name': result['name'],
 'category': '',
 'applied': 'False'
 })
 row.update(result)
 merged.append(row)

 # Write updated CSV
 fieldnames = ['name', 'category', 'url', 'careers_url', 'job_board', 'description', 'applied']
 with open(csv_path, 'w', newline='') as f:
 writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
 writer.writeheader()
 writer.writerows(merged)

 logger.info(f"Updated {csv_path} with {len(merged)} companies")

if __name__ == '__main__':
 import argparse

 parser = argparse.ArgumentParser(description='URL Scraper for Job Applications')
 parser.add_argument('--markdown', default='target-companies-100.md', help='Source markdown file')
 parser.add_argument('--csv', default='companies.csv', help='Output CSV file')
 parser.add_argument('--company', help='Scrape single company')

 args = parser.parse_args()

 scraper = URLScraper()

 if args.company:
 result = scraper.scrape_company(args.company)
 print(json.dumps(result, indent=2))
 else:
 results = scraper.scrape_from_markdown(args.markdown)
 scraper.update_csv(results, args.csv)
 print(f"\nScraped {len(results)} companies. Check {args.csv}")
