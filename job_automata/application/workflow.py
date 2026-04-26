#!/usr/bin/env python3
"""
Job Automata Orchestrator
Runs the full workflow: scrape URLs → find managers → auto-apply
"""

import subprocess
import sys
import time
import json
import os
import logging

from job_automata.config import APPLICATIONS_DIR, DEFAULT_COMPANIES, DEFAULT_TARGET_COMPANIES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobAutomataOrchestrator:
    """Orchestrates the full job application workflow"""

    def __init__(self):
        self.steps = []

    def step(self, name: str, command: list, description: str = ""):
        """Register a workflow step"""
        self.steps.append({
            'name': name,
            'command': command,
            'description': description
        })

    def run_step(self, step: dict, step_num: int, total: int) -> bool:
        """Execute a single step"""
        print(f"\n{'='*70}")
        print(f"STEP {step_num}/{total}: {step['name']}")
        print(f"{'='*70}")
        if step['description']:
            print(f"Description: {step['description']}")
            print()

        try:
            result = subprocess.run(
                step['command'],
                capture_output=False,
                text=True
            )
            if result.returncode == 0:
                print()
                print(f"SUCCESS: {step['name']} completed")
                return True
            else:
                print()
                print(f"FAILED: {step['name']} (exit code: {result.returncode})")
                return False
        except Exception as e:
            print()
            print(f"ERROR: {step['name']}: {e}")
            return False

    def run_workflow(self, mode: str = 'full'):
        """
        Run the full workflow

        Args:
            mode: 'init', 'scrape', 'hunt', 'test', or 'apply'
        """
        completed = 0
        failed = 0

        for i, step in enumerate(self.steps, 1):
            success = self.run_step(step, i, len(self.steps))
            if success:
                completed += 1
                time.sleep(2)
            else:
                failed += 1
                logger.warning(f"Step {step['name']} failed. Continue? (y/n)")
                try:
                    should_continue = input().lower() == 'y'
                except EOFError:
                    should_continue = False
                if not should_continue:
                    break

        print(f"\n{'='*70}")
        print(f"WORKFLOW COMPLETE")
        print(f"Passed: {completed}/{len(self.steps)} steps")
        if failed > 0:
            print(f"Failed: {failed} steps")
        print(f"{'='*70}\n")

        return failed == 0


def build_workflow(
    mode: str = 'full',
    csv_file: str = str(DEFAULT_COMPANIES),
    markdown_file: str = str(DEFAULT_TARGET_COMPANIES),
    linkedin_email: str = None,
) -> JobAutomataOrchestrator:
    """
    Build workflow based on mode

    Modes:
        - 'init': Initialize profile and CSV
        - 'scrape': Scrape URLs only
        - 'hunt': Hunt LinkedIn managers
        - 'test': Test dry run
        - 'apply': Full auto-apply
        - 'full': All steps (init - scrape - hunt - test - apply)
    """
    o = JobAutomataOrchestrator()

    if mode in ['init', 'full']:
        o.step(
            'Initialize Profile',
            [sys.executable, '-m', 'job_automata.application.auto_apply', '--init'],
            'Creates data/profile.json and data/companies.csv templates'
        )

    if mode in ['scrape', 'full']:
        o.step(
            'Scrape Company URLs',
            [sys.executable, '-m', 'job_automata.infrastructure.scraping.url_scraper', '--markdown', markdown_file, '--csv', csv_file],
            'Finds careers pages and job board platforms'
        )

    if mode in ['hunt', 'full']:
        if linkedin_email and os.getenv('LINKEDIN_PASSWORD'):
            o.step(
                'Hunt LinkedIn Managers',
                [
                    sys.executable, '-m', 'job_automata.infrastructure.linkedin.hunter',
                    '--email', linkedin_email,
                    '--csv', csv_file
                ],
                'Finds hiring managers at target companies'
            )
        else:
            logger.warning("LINKEDIN_EMAIL/LINKEDIN_PASSWORD not provided. Skipping manager hunt.")

    if mode in ['test', 'full']:
        o.step(
            'Test Dry Run',
            [sys.executable, '-m', 'job_automata.application.auto_apply', '--dry-run', '--csv', csv_file],
            'Test applications without submitting'
        )

    if mode in ['apply', 'full']:
        o.step(
            'Auto-Apply to Companies',
            [sys.executable, '-m', 'job_automata.application.auto_apply', '--csv', csv_file],
            'Submit applications to all companies'
        )

    return o


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Job Automata Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize everything
  python -m job_automata.application.workflow --mode init

  # Scrape URLs only
  python -m job_automata.application.workflow --mode scrape

  # Run dry test
  python -m job_automata.application.workflow --mode test

  # Full workflow (init - scrape - hunt - test - apply)
  LINKEDIN_PASSWORD=... python -m job_automata.application.workflow --mode hunt --linkedin-email your@email.com

  # Open apply flows for supported job boards
  python -m job_automata.application.workflow --mode apply
        """
    )

    parser.add_argument(
        '--mode',
        choices=['init', 'scrape', 'hunt', 'test', 'apply', 'full'],
        default='init',
        help='Workflow mode'
    )
    parser.add_argument(
        '--csv',
        default=str(DEFAULT_COMPANIES),
        help='Companies CSV file'
    )
    parser.add_argument(
        '--markdown',
        default=str(DEFAULT_TARGET_COMPANIES),
        help='Source markdown file'
    )
    parser.add_argument(
        '--linkedin-email',
        help='LinkedIn email for manager hunting'
    )

    args = parser.parse_args()

    print("""
Job Automata - Application Orchestrator
    """)

    logger.info(f"Starting workflow: {args.mode}")

    workflow = build_workflow(
        mode=args.mode,
        csv_file=args.csv,
        markdown_file=args.markdown,
        linkedin_email=args.linkedin_email
    )

    success = workflow.run_workflow(args.mode)

    if success:
        logger.info("All steps completed successfully!")
        logger.info(f"Check these files for results:")
        logger.info(f"  - {args.csv} (company URLs and job boards)")
        logger.info(f"  - linkedin_managers.csv (hiring managers)")
        logger.info(f"  - {APPLICATIONS_DIR}/applications_*.csv (application results)")
        sys.exit(0)
    else:
        logger.error("Workflow failed. Check logs above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
