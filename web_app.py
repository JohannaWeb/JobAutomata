#!/usr/bin/env python3
"""
Job Automata Web Dashboard
Modern Flask app with dry run and scraping preview capabilities
"""

import json
import csv
import os
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging

app = Flask(__name__, template_folder='templates')
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
RUN_HISTORY_FILE = DATA_DIR / '.run_history.json'

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
    """Aggregate statistics from all application runs"""
    total_apps = 0
    successful = 0
    last_run = None

    app_csvs = sorted(DATA_DIR.glob('applications_*.csv'), reverse=True)

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
        'last_run': last_run or 'Never',
        'companies': 0
    }

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory('templates', 'dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    stats = get_all_stats()

    companies_csv = DATA_DIR / 'companies.csv'
    if companies_csv.exists():
        with open(companies_csv, 'r') as f:
            companies = len(list(csv.DictReader(f)))
            stats['companies'] = companies

    return jsonify(stats)

@app.route('/api/dry-run', methods=['POST'])
def dry_run():
    """Execute dry run simulation"""
    logger.info("Starting dry run simulation")

    results = []
    logs = []

    companies_csv = DATA_DIR / 'companies.csv'
    profile_file = DATA_DIR / 'profile.json'

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
    logger.info("Starting URL scraper")

    try:
        result = subprocess.run(
            ['python3', 'url_scraper.py', '--markdown', 'target-companies-100.md', '--csv', 'companies.csv'],
            cwd=DATA_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )

        companies = []
        companies_csv = DATA_DIR / 'companies.csv'

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
            ['python3', 'auto_apply.py', '--csv', 'companies.csv'],
            cwd=DATA_DIR,
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
    current_cv_file = DATA_DIR / '.current_cv'
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

    current_cv_file = DATA_DIR / '.current_cv'
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

    if not file.filename.endswith('.md'):
        return jsonify({'error': 'Only .md files allowed'}), 400

    try:
        # Save to root or cvs directory
        cv_path = DATA_DIR / file.filename
        file.save(str(cv_path))

        # Set as current CV
        current_cv_file = DATA_DIR / '.current_cv'
        with open(current_cv_file, 'w') as f:
            f.write(file.filename)

        return jsonify({'success': True, 'filename': file.filename, 'current': file.filename})
    except Exception as e:
        logger.error(f"Error uploading CV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cv/<filename>')
def get_cv(filename):
    """Get CV content"""
    cv_path = DATA_DIR / 'cvs' / filename

    if not cv_path.exists():
        cv_path = DATA_DIR / filename

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
    current_file = DATA_DIR / '.current_companies'
    current = 'companies.csv'

    if current_file.exists():
        with open(current_file, 'r') as f:
            current = f.read().strip()

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

    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        return jsonify({'error': 'File not found'}), 404

    current_file = DATA_DIR / '.current_companies'
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
    current_file = DATA_DIR / '.current_companies'
    csv_name = 'companies.csv'

    if current_file.exists():
        with open(current_file, 'r') as f:
            csv_name = f.read().strip()

    csv_path = DATA_DIR / csv_name
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

    current_file = DATA_DIR / '.current_companies'
    csv_name = 'companies.csv'

    if current_file.exists():
        with open(current_file, 'r') as f:
            csv_name = f.read().strip()

    csv_path = DATA_DIR / csv_name

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
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info("Starting Job Automata Web Dashboard")
    logger.info(f"Visit http://0.0.0.0:{port} in your browser")

    app.run(host='0.0.0.0', port=port, debug=debug)
