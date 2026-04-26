#!/usr/bin/env python3
"""
Job Automata Web Dashboard
Modern Flask app with dry run and scraping preview capabilities
PostgreSQL-backed for data persistence
"""

import json
import csv
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging
from werkzeug.utils import secure_filename
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from job_automata.config import (
    APPLICATIONS_DIR,
    DATA_DIR,
    DEFAULT_COMPANIES,
    DEFAULT_PROFILE,
    DEFAULT_TARGET_COMPANIES,
    PROJECT_ROOT,
    STATE_DIR,
)

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / 'templates'),
    static_folder=str(PROJECT_ROOT / 'static'),
    static_url_path='/static',
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)
APPLICATIONS_TOTAL = Gauge(
    'jobautomata_applications_total',
    'Total job applications'
)
APPLICATIONS_SUCCESSFUL = Gauge(
    'jobautomata_applications_successful',
    'Successful job applications'
)
SUCCESS_RATE = Gauge(
    'jobautomata_success_rate',
    'Application success rate percentage'
)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///jobautomata.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

STATE_DIR.mkdir(parents=True, exist_ok=True)
APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
RUN_HISTORY_FILE = STATE_DIR / 'run_history.json'  # Fallback for local dev
DANGEROUS_AUTOMATION_ENABLED = os.getenv('ENABLE_DANGEROUS_AUTOMATION') == 'true'
DASHBOARD_TOKEN = os.getenv('DASHBOARD_TOKEN')
LOCAL_ADDRESSES = {'127.0.0.1', '::1', 'localhost'}


@app.before_request
def require_local_or_token():
    """Fail closed for remote dashboard/API access unless an explicit token is configured."""
    if request.path.startswith('/static/'):
        return None

    if DASHBOARD_TOKEN:
        supplied = request.headers.get('X-Dashboard-Token')
        auth = request.headers.get('Authorization', '')
        bearer = auth.removeprefix('Bearer ').strip() if auth.startswith('Bearer ') else None
        if supplied == DASHBOARD_TOKEN or bearer == DASHBOARD_TOKEN:
            return None
        return jsonify({'error': 'Unauthorized'}), 401

    remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    if remote_addr in LOCAL_ADDRESSES:
        return None

    return jsonify({
        'error': 'Dashboard is local-only unless DASHBOARD_TOKEN is set'
    }), 403


@app.before_request
def track_request_start():
    """Track request start for metrics."""
    request._start_time = time.time()
    ACTIVE_REQUESTS.inc()


@app.after_request
def track_request_end(response):
    """Track request metrics."""
    ACTIVE_REQUESTS.dec()

    if hasattr(request, '_start_time'):
        latency = time.time() - request._start_time
        endpoint = request.endpoint or 'unknown'
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)

    return response


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    from flask import Response
    return Response(generate_latest(), mimetype='text/plain')


def dangerous_automation_disabled():
    return jsonify({
        'error': 'Browser automation from HTTP is disabled. Set ENABLE_DANGEROUS_AUTOMATION=true only for a trusted local environment.'
    }), 403


def current_companies_name():
    current_file = STATE_DIR / 'current_companies'
    if current_file.exists():
        name = current_file.read_text().strip()
        if name:
            return name
    return DEFAULT_COMPANIES.name


def _module_command(module: str, *args: str) -> list[str]:
    return [os.environ.get("PYTHON", "python3"), "-m", module, *args]


def safe_child_path(base_dir: Path, filename: str, suffixes: set[str]) -> Path:
    """Resolve a user-selected file and verify it stays under base_dir."""
    safe_name = secure_filename(filename or '')
    if safe_name != filename or Path(safe_name).name != safe_name:
        raise ValueError('Invalid filename')
    if Path(safe_name).suffix.lower() not in suffixes:
        raise ValueError(f'Invalid file type. Allowed: {", ".join(sorted(suffixes))}')

    base = base_dir.resolve()
    candidate = (base / safe_name).resolve()
    if base != candidate.parent:
        raise ValueError('Invalid file path')
    return candidate

def load_run_history():
    """Load run history from file"""
    if RUN_HISTORY_FILE.exists():
        with open(RUN_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'runs': []}

def save_run_history(history):
    """Save run history to file"""
    with open(RUN_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def parse_applications_csv(csv_path):
    """Parse an applications CSV file"""
    companies = []
    if Path(csv_path).exists():
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append({
                    'company': row.get('company', ''),
                    'success': row.get('success', 'False') == 'True',
                    'timestamp': row.get('timestamp', '')
                })
    return companies

def get_all_stats():
    """Aggregate statistics from database or CSV files"""
    try:
        if 'postgresql' in DATABASE_URL or 'mysql' in DATABASE_URL:
            # Get from database
            result = db.session.execute(text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful,
                    MAX(timestamp) as last_run
                FROM applications
            """)).fetchone()

            total_apps = result[0] or 0
            successful = result[1] or 0
            last_run = result[2]
        else:
            # Fallback to CSV for local dev
            total_apps = 0
            successful = 0
            last_run = None

            app_csvs = sorted(APPLICATIONS_DIR.glob('applications_*.csv'), reverse=True)
            for csv_file in app_csvs:
                if 'dry_run' in csv_file.name:
                    continue
                apps = parse_applications_csv(str(csv_file))
                for app in apps:
                    total_apps += 1
                    if app['success']:
                        successful += 1
                    if last_run is None:
                        last_run = app['timestamp']

        success_rate = int((successful / total_apps * 100)) if total_apps > 0 else 0

        return {
            'total_applications': total_apps,
            'successful_applies': successful,
            'success_rate': success_rate,
            'last_run': str(last_run) if last_run else 'Never',
            'companies': 0
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'total_applications': 0,
            'successful_applies': 0,
            'success_rate': 0,
            'last_run': 'Never',
            'companies': 0
        }

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory(PROJECT_ROOT / 'templates', 'dashboard.html')


@app.route('/favicon.ico')
def favicon():
    """Silence browser favicon 404 noise."""
    return ('', 204)

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    stats = get_all_stats()

    companies_csv = DATA_DIR / current_companies_name()
    if companies_csv.exists():
        with open(companies_csv, 'r') as f:
            companies = len(list(csv.DictReader(f)))
            stats['companies'] = companies

    # Update Prometheus metrics
    APPLICATIONS_TOTAL.set(stats['total_applications'])
    APPLICATIONS_SUCCESSFUL.set(stats['successful_applies'])
    SUCCESS_RATE.set(stats['success_rate'])

    return jsonify(stats)

@app.route('/api/dry-run', methods=['POST'])
def dry_run():
    """Execute dry run simulation"""
    logger.info("Starting dry run simulation")

    results = []
    logs = []

    companies_csv = DATA_DIR / current_companies_name()
    profile_file = DEFAULT_PROFILE

    if not companies_csv.exists():
        return jsonify({'error': 'Companies CSV not found'}), 404

    profile = {}
    if profile_file.exists():
        with open(profile_file, 'r') as f:
            profile = json.load(f)

    logs.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'info',
        'message': 'Dry run simulation started'
    })

    company_count = 0
    with open(companies_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_count += 1
            company_name = row.get('name', 'Unknown')
            url = row.get('url', '')
            careers_url = row.get('careers_url', '')

            logs.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': f'Processing {company_name}...'
            })

            result = {
                'company': company_name,
                'action': 'apply',
                'status': 'simulated'
            }

            if careers_url:
                logs.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'Found careers page for {company_name}'
                })
            else:
                logs.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'level': 'warning',
                    'message': f'No careers URL for {company_name}'
                })

            results.append(result)

    logs.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'success',
        'message': f'Dry run complete. Would process {company_count} companies.'
    })

    return jsonify({
        'results': results,
        'logs': logs,
        'companies_count': company_count
    })

@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Start scraping URLs"""
    if not DANGEROUS_AUTOMATION_ENABLED:
        return dangerous_automation_disabled()

    logger.info("Starting URL scraper")

    try:
        result = subprocess.run(
            _module_command(
                'job_automata.infrastructure.scraping.url_scraper',
                '--markdown',
                str(DEFAULT_TARGET_COMPANIES),
                '--csv',
                str(DEFAULT_COMPANIES),
            ),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )

        companies = []
        companies_csv = DEFAULT_COMPANIES

        if companies_csv.exists():
            with open(companies_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    companies.append({
                        'name': row.get('name', ''),
                        'category': row.get('category', ''),
                        'url': row.get('url', ''),
                        'careers_url': row.get('careers_url', ''),
                        'job_board': row.get('job_board', '')
                    })

        return jsonify({
            'success': result.returncode == 0,
            'companies': companies,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Scraping timeout'}), 408
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-full', methods=['POST'])
def run_full():
    """Start full automation workflow"""
    if not DANGEROUS_AUTOMATION_ENABLED:
        return dangerous_automation_disabled()

    logger.info("Starting full automation workflow")

    history = load_run_history()

    run_entry = {
        'date': datetime.now().isoformat(),
        'type': 'full',
        'companies': 0,
        'successful': 0,
        'duration': '—',
        'status': 'running'
    }

    history['runs'].insert(0, run_entry)
    save_run_history(history)

    try:
        result = subprocess.run(
            _module_command(
                'job_automata.application.auto_apply',
                '--csv',
                str(DEFAULT_COMPANIES),
            ),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600
        )

        run_entry['status'] = 'completed' if result.returncode == 0 else 'failed'
        save_run_history(history)

        return jsonify({
            'success': result.returncode == 0,
            'status': run_entry['status']
        })
    except subprocess.TimeoutExpired:
        run_entry['status'] = 'timeout'
        save_run_history(history)
        return jsonify({'error': 'Workflow timeout'}), 408
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        run_entry['status'] = 'error'
        save_run_history(history)
        return jsonify({'error': str(e)}), 500

@app.route('/api/cvs')
def get_cvs():
    """Get list of CV variants"""
    cv_dir = DATA_DIR / 'cvs'
    current_cv_file = STATE_DIR / 'current_cv'
    current_cv = 'cv_main.md'

    if current_cv_file.exists():
        with open(current_cv_file, 'r') as f:
            current_cv = f.read().strip()

    cvs = []
    if cv_dir.exists():
        cvs = [f.name for f in cv_dir.glob('cv_*.md')]

    # Also check for CV files in root
    root_cvs = list(DATA_DIR.glob('cv_*.md'))
    for cv in root_cvs:
        if cv.name not in cvs:
            cvs.append(cv.name)

    return jsonify({
        'cvs': sorted(cvs) if cvs else ['cv_main.md'],
        'current': current_cv
    })

@app.route('/api/cvs/select', methods=['POST'])
def select_cv():
    """Set the current CV to use"""
    data = request.get_json()
    cv_name = data.get('cv')

    if not cv_name:
        return jsonify({'error': 'CV name required'}), 400

    try:
        safe_child_path(DATA_DIR, cv_name, {'.md', '.pdf'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    current_cv_file = STATE_DIR / 'current_cv'
    with open(current_cv_file, 'w') as f:
        f.write(cv_name)

    return jsonify({'success': True, 'current': cv_name})

@app.route('/api/cvs/upload', methods=['POST'])
def upload_cv():
    """Upload a new CV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        cv_path = safe_child_path(DATA_DIR, file.filename, {'.md', '.pdf'})
        file.save(str(cv_path))

        # Set as current CV
        current_cv_file = STATE_DIR / 'current_cv'
        with open(current_cv_file, 'w') as f:
            f.write(file.filename)

        return jsonify({'success': True, 'filename': file.filename, 'current': file.filename})
    except Exception as e:
        logger.error(f"Error uploading CV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cv/<filename>')
def get_cv(filename):
    """Get CV content"""
    try:
        cv_path = safe_child_path(DATA_DIR / 'cvs', filename, {'.md', '.pdf'})
    except ValueError:
        try:
            cv_path = safe_child_path(DATA_DIR, filename, {'.md', '.pdf'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    if not cv_path.exists():
        try:
            cv_path = safe_child_path(DATA_DIR, filename, {'.md', '.pdf'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    if not cv_path.exists():
        return jsonify({'error': 'CV not found'}), 404

    with open(cv_path, 'r') as f:
        content = f.read()

    return jsonify({
        'content': content,
        'current': filename == 'cv_main.md'
    })

@app.route('/api/history')
def get_history():
    """Get run history"""
    history = load_run_history()
    return jsonify(history)

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear run history"""
    save_run_history({'runs': []})
    return jsonify({'success': True})

@app.route('/api/companies')
def get_companies_list():
    """Get list of available companies CSV files and current selection"""
    current = current_companies_name()

    companies_files = []
    for csv_file in sorted(DATA_DIR.glob('companies*.csv')):
        companies_files.append({
            'name': csv_file.name,
            'size': csv_file.stat().st_size,
            'current': csv_file.name == current
        })

    return jsonify({
        'files': companies_files,
        'current': current
    })

@app.route('/api/companies/select', methods=['POST'])
def select_companies():
    """Set the current companies CSV to use"""
    data = request.get_json()
    csv_name = data.get('file')

    if not csv_name:
        return jsonify({'error': 'CSV name required'}), 400

    try:
        csv_path = safe_child_path(DATA_DIR, csv_name, {'.csv'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if not csv_path.exists():
        return jsonify({'error': 'File not found'}), 404

    current_file = STATE_DIR / 'current_companies'
    with open(current_file, 'w') as f:
        f.write(csv_name)

    # Count companies in file
    count = 0
    try:
        with open(csv_path, 'r') as f:
            count = len(list(csv.DictReader(f)))
    except:
        pass

    return jsonify({'success': True, 'current': csv_name, 'count': count})

@app.route('/api/companies/view')
def view_companies():
    """Get the current companies list"""
    csv_name = current_companies_name()
    try:
        csv_path = safe_child_path(DATA_DIR, csv_name, {'.csv'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    companies = []

    if csv_path.exists():
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append(row)

    return jsonify({'file': csv_name, 'companies': companies, 'count': len(companies)})

@app.route('/api/companies/update', methods=['POST'])
def update_companies():
    """Update companies list"""
    data = request.get_json()
    companies = data.get('companies', [])

    csv_name = current_companies_name()
    try:
        csv_path = safe_child_path(DATA_DIR, csv_name, {'.csv'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if not companies:
        return jsonify({'error': 'No companies provided'}), 400

    try:
        # Write companies back to CSV
        fieldnames = list(companies[0].keys()) if companies else []
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(companies)

        return jsonify({'success': True, 'count': len(companies)})
    except Exception as e:
        logger.error(f"Error updating companies: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('DASHBOARD_HOST', '127.0.0.1')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info("Starting Job Automata Web Dashboard")
    logger.info(f"Visit http://{host}:{port} in your browser")

    app.run(host=host, port=port, debug=debug)
