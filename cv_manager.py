#!/usr/bin/env python3
"""CV Manager API - Production ready, Railway deployable"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
import mimetypes

CV_DIR = Path('.')
PROFILE_FILE = Path('profile.json')

class CVManagerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/':
            self.serve_html()
        elif path == '/api/cvs':
            self.get_cvs()
        elif path.startswith('/api/cv/'):
            filename = path.split('/api/cv/')[1].split('/')[0]
            self.get_cv(filename)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/cv/') and '/switch' in path:
            filename = path.split('/api/cv/')[1].split('/switch')[0]
            self.switch_cv(filename)
        elif path.startswith('/api/cv/') and '/create-variant' in path:
            filename = path.split('/api/cv/')[1].split('/create-variant')[0]
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            self.create_variant(filename, body)
        else:
            self.send_error(404)

    def serve_html(self):
        html_path = Path(__file__).parent / 'templates' / 'cv_manager.html'
        if not html_path.exists():
            self.send_error(404, 'HTML template not found')
            return

        with open(html_path, 'rb') as f:
            content = f.read()

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)

    def get_cvs(self):
        cv_files = sorted([f.name for f in CV_DIR.glob('cv*.md')])
        current = self.get_current_cv()

        if not cv_files and current not in cv_files:
            cv_files = [current]

        response = json.dumps({'cvs': cv_files, 'current': current})
        self.send_json(response)

    def get_cv(self, filename):
        if '..' in filename or '/' in filename:
            self.send_error(400, 'Invalid filename')
            return

        cv_path = CV_DIR / filename
        if not cv_path.exists():
            self.send_error(404, f'CV {filename} not found')
            return

        with open(cv_path) as f:
            content = f.read()

        response = json.dumps({
            'filename': filename,
            'content': content,
            'current': filename == self.get_current_cv()
        })
        self.send_json(response)

    def switch_cv(self, filename):
        if '..' in filename or '/' in filename:
            self.send_error(400, 'Invalid filename')
            return

        cv_path = CV_DIR / filename
        if not cv_path.exists():
            self.send_error(404, f'CV {filename} not found')
            return

        if self.update_profile_cv(filename):
            response = json.dumps({'success': True, 'current': filename})
            self.send_json(response)
        else:
            self.send_error(500, 'Failed to update profile')

    def create_variant(self, filename, body):
        try:
            data = json.loads(body)
            new_name = data.get('name', 'cv_variant.md')
        except:
            self.send_error(400, 'Invalid JSON')
            return

        if '..' in new_name or '/' in new_name:
            self.send_error(400, 'Invalid filename')
            return

        if not new_name.endswith('.md'):
            new_name += '.md'

        cv_path = CV_DIR / filename
        if not cv_path.exists():
            self.send_error(404, f'Source CV {filename} not found')
            return

        new_path = CV_DIR / new_name
        if new_path.exists():
            self.send_error(409, f'CV {new_name} already exists')
            return

        try:
            with open(cv_path) as f:
                content = f.read()
            with open(new_path, 'w') as f:
                f.write(content)
            response = json.dumps({'success': True, 'filename': new_name})
            self.send_json(response)
        except Exception as e:
            self.send_error(500, str(e))

    @staticmethod
    def get_current_cv():
        if PROFILE_FILE.exists():
            try:
                with open(PROFILE_FILE) as f:
                    profile = json.load(f)
                    return profile.get('resume_file', 'cv.md')
            except:
                return 'cv.md'
        return 'cv.md'

    @staticmethod
    def update_profile_cv(cv_filename):
        try:
            if PROFILE_FILE.exists():
                with open(PROFILE_FILE) as f:
                    profile = json.load(f)
                profile['resume_file'] = cv_filename
                with open(PROFILE_FILE, 'w') as f:
                    json.dump(profile, f, indent=2)
                return True
        except:
            pass
        return False

    def send_json(self, data):
        data_bytes = data.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(data_bytes))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data_bytes)

    def log_message(self, format, *args):
        print(f'[{self.log_date_time_string()}] {format % args}', file=sys.stderr)


def run_server(port=None):
    if port is None:
        port = int(os.environ.get('PORT', 5000))

    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, CVManagerHandler)
    print(f'CV Manager running at http://localhost:{port}')
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
