#!/usr/bin/env python3
"""CV Manager Web UI - Switch between different CV variants"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
import os

app = Flask(__name__)
CV_DIR = Path('.')
PROFILE_FILE = Path('profile.json')

def get_cv_files():
    """Get all CV markdown files"""
    cv_files = list(CV_DIR.glob('cv*.md'))
    return sorted([f.name for f in cv_files])

def get_current_cv():
    """Get currently selected CV from profile.json"""
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE) as f:
            profile = json.load(f)
            return profile.get('resume_file', 'cv.md')
    return 'cv.md'

def read_cv(filename):
    """Read CV content"""
    cv_path = CV_DIR / filename
    if cv_path.exists():
        with open(cv_path) as f:
            return f.read()
    return ""

def update_profile_cv(cv_filename):
    """Update profile.json with new CV file"""
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE) as f:
            profile = json.load(f)
        profile['resume_file'] = cv_filename
        with open(PROFILE_FILE, 'w') as f:
            json.dump(profile, f, indent=2)
        return True
    return False

@app.route('/')
def index():
    """Main page"""
    cv_files = get_cv_files()
    current = get_current_cv()

    if not cv_files and current not in cv_files:
        cv_files.append(current)

    return render_template('cv_manager.html', cvs=cv_files, current=current)

@app.route('/api/cv/<filename>')
def get_cv(filename):
    """Get CV content"""
    # Security: only allow .md files in current directory
    if '..' in filename or '/' in filename:
        return {'error': 'Invalid filename'}, 400

    content = read_cv(filename)
    return {
        'filename': filename,
        'content': content,
        'current': filename == get_current_cv()
    }

@app.route('/api/cv/<filename>/switch', methods=['POST'])
def switch_cv(filename):
    """Switch to a different CV"""
    if '..' in filename or '/' in filename:
        return {'error': 'Invalid filename'}, 400

    cv_path = CV_DIR / filename
    if not cv_path.exists():
        return {'error': f'CV file {filename} not found'}, 404

    if update_profile_cv(filename):
        return {'success': True, 'current': filename}
    return {'error': 'Failed to update profile'}, 500

@app.route('/api/cv/<filename>/create-variant', methods=['POST'])
def create_variant(filename):
    """Create a new CV variant from existing one"""
    data = request.json
    new_name = data.get('name', 'cv_variant.md')

    if '..' in new_name or '/' in new_name:
        return {'error': 'Invalid filename'}, 400

    if not new_name.endswith('.md'):
        new_name += '.md'

    # Read source CV
    content = read_cv(filename)
    if not content:
        return {'error': f'Source CV {filename} not found'}, 404

    # Check if variant already exists
    new_path = CV_DIR / new_name
    if new_path.exists():
        return {'error': f'CV variant {new_name} already exists'}, 409

    # Create new variant
    with open(new_path, 'w') as f:
        f.write(content)

    return {'success': True, 'filename': new_name}

@app.route('/api/cvs')
def list_cvs():
    """List all available CVs"""
    cv_files = get_cv_files()
    current = get_current_cv()

    if not cv_files and current not in cv_files:
        cv_files = [current]

    return {
        'cvs': cv_files,
        'current': current
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
