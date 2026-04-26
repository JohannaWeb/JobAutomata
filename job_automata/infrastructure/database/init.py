#!/usr/bin/env python3
"""Initialize PostgreSQL database and migrate data from CSV files."""

import os
import csv
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from job_automata.config import APPLICATIONS_DIR, DATA_DIR, DATABASE_DIR, STATE_DIR

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/jobautomata')

def init_database():
    """Create database schema"""
    engine = create_engine(DATABASE_URL)

    # Read and execute schema
    schema_path = DATABASE_DIR / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema = f.read()

    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        for statement in schema.split(';'):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()

    print("✓ Database schema created")

def migrate_companies():
    """Migrate companies from CSV to database"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    companies_files = list(DATA_DIR.glob('companies*.csv'))

    for csv_file in companies_files:
        print(f"Migrating {csv_file.name}...")
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Insert or skip if exists
                sql = text("""
                    INSERT INTO companies (name, url, category, careers_url, job_board)
                    VALUES (:name, :url, :category, :careers_url, :job_board)
                    ON CONFLICT (name) DO NOTHING
                """)
                session.execute(sql, {
                    'name': row.get('name', ''),
                    'url': row.get('url', ''),
                    'category': row.get('category', ''),
                    'careers_url': row.get('careers_url', ''),
                    'job_board': row.get('job_board', '')
                })

    session.commit()
    session.close()
    print(f"✓ Migrated companies from {len(companies_files)} files")

def migrate_applications():
    """Migrate applications from CSV to database"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    app_files = list(APPLICATIONS_DIR.glob('applications_*.csv'))

    for csv_file in app_files:
        if 'dry_run' in csv_file.name:
            continue

        print(f"Migrating {csv_file.name}...")
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sql = text("""
                    INSERT INTO applications (company_name, url, success, timestamp, notes)
                    VALUES (:company, :url, :success, :timestamp, :notes)
                """)
                session.execute(sql, {
                    'company': row.get('company', ''),
                    'url': row.get('url', ''),
                    'success': row.get('success', 'False') == 'True',
                    'timestamp': row.get('timestamp', datetime.now()),
                    'notes': row.get('notes', '')
                })

    session.commit()
    session.close()
    print(f"✓ Migrated applications from {len(app_files)} files")

def migrate_run_history():
    """Migrate run history from JSON to database"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    history_file = STATE_DIR / 'run_history.json'
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)

        for run in history.get('runs', []):
            sql = text("""
                INSERT INTO run_history (date, type, companies, successful, duration, status)
                VALUES (:date, :type, :companies, :successful, :duration, :status)
            """)
            session.execute(sql, {
                'date': run.get('date'),
                'type': run.get('type', 'full'),
                'companies': run.get('companies', 0),
                'successful': run.get('successful', 0),
                'duration': run.get('duration', ''),
                'status': run.get('status', 'unknown')
            })

        session.commit()
        session.close()
        print("✓ Migrated run history")

if __name__ == '__main__':
    print("Initializing PostgreSQL database...")

    if not DATABASE_URL or 'localhost' in DATABASE_URL:
        print("⚠️  Using local database (set DATABASE_URL env var for production)")

    try:
        init_database()
        migrate_companies()
        migrate_applications()
        migrate_run_history()
        print("\n✅ Database initialization complete!")
        print("Run: python -m job_automata.presentation.web.app")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
