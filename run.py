#!/usr/bin/env python3
"""
Job Automata Orchestrator
Runs the full workflow: scrape URLs → find managers → auto-apply
"""

import subprocess
import sys
import time
import json
from pathlib import Path
import logging

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
        print(f"\n{'='*60}")
        print(f"[{step_num}/{total}] {step['name']}")
        print(f"{'='*60}")
        if step['description']:
            print(f"📝 {step['description']}")

        try:
            result = subprocess.run(
                step['command'],
                capture_output=False,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {step['name']} completed")
                return True
            else:
                print(f"❌ {step['name']} failed (exit code: {result.returncode})")
                return False
        except Exception as e:
            print(f"❌ {step['name']} error: {e}")
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
                time.sleep(2)  # Pause between steps
            else:
                failed += 1
                logger.warning(f"Step {step['name']} failed. Continue? (y/n)")
                if input().lower() != 'y':
                    break

        print(f"\n{'='*60}")
        print(f"WORKFLOW COMPLETE: {completed}/{len(self.steps)} steps passed")
        if failed > 0:
            print(f"⚠️  {failed} steps failed")
        print(f"{'='*60}\n")

        return failed == 0


def build_workflow(
    mode: str = 'full',
    csv_file: str = 'companies.csv',
    markdown_file: str = 'target-companies-100.md',
    linkedin_email: str = None,
    linkedin_password: str = None
) -> JobAutomataOrchestrator:
    """
    Build workflow based on mode

    Modes:
        - 'init': Initialize profile and CSV
        - 'scrape': Scrape URLs only
        - 'hunt': Hunt LinkedIn managers
        - 'test': Test dry run
        - 'apply': Full auto-apply
        - 'full': All steps (init → scrape → hunt → test → apply)
    """
    o = JobAutomataOrchestrator()

    if mode in ['init', 'full']:
        o.step(
            'Initialize Profile',
            [sys.executable, 'auto_apply.py', '--init'],
            'Creates profile.json and companies.csv templates'
        )

    if mode in ['scrape', 'full']:
        o.step(
            'Scrape Company URLs',
            [sys.executable, 'url_scraper.py', '--markdown', markdown_file, '--csv', csv_file],
            'Finds careers pages and job board platforms'
        )

    if mode in ['hunt', 'full']:
        if linkedin_email and linkedin_password:
            o.step(
                'Hunt LinkedIn Managers',
                [
                    sys.executable, 'linkedin_hunter.py',
                    '--email', linkedin_email,
                    '--password', linkedin_password,
                    '--csv', csv_file
                ],
                'Finds hiring managers at target companies'
            )
        else:
            logger.warning("LinkedIn email/password not provided. Skipping manager hunt.")

    if mode in ['test', 'full']:
        o.step(
            'Test Dry Run',
            [sys.executable, 'auto_apply.py', '--dry-run', '--csv', csv_file],
            'Test applications without submitting'
        )

    if mode in ['apply', 'full']:
        o.step(
            'Auto-Apply to Companies',
            [sys.executable, 'auto_apply.py', '--csv', csv_file],
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
  python run.py --mode init

  # Scrape URLs only
  python run.py --mode scrape

  # Run dry test
  python run.py --mode test

  # Full workflow (init → scrape → hunt → test → apply)
  python run.py --mode full --linkedin-email your@email.com --linkedin-password pass

  # Just auto-apply (assumes CSV already populated)
  python run.py --mode apply
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
        default='companies.csv',
        help='Companies CSV file'
    )
    parser.add_argument(
        '--markdown',
        default='target-companies-100.md',
        help='Source markdown file'
    )
    parser.add_argument(
        '--linkedin-email',
        help='LinkedIn email for manager hunting'
    )
    parser.add_argument(
        '--linkedin-password',
        help='LinkedIn password for manager hunting'
    )

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════╗
║         🤖 Job Automata - Application Orchestrator         ║
╚════════════════════════════════════════════════════════════╝
    """)

    logger.info(f"Starting workflow: {args.mode}")

    workflow = build_workflow(
        mode=args.mode,
        csv_file=args.csv,
        markdown_file=args.markdown,
        linkedin_email=args.linkedin_email,
        linkedin_password=args.linkedin_password
    )

    success = workflow.run_workflow(args.mode)

    if success:
        logger.info("✅ All steps completed successfully!")
        logger.info(f"📊 Check these files for results:")
        logger.info(f"  - {args.csv} (company URLs and job boards)")
        logger.info(f"  - linkedin_managers.csv (hiring managers)")
        logger.info(f"  - applications_*.csv (application results)")
        sys.exit(0)
    else:
        logger.error("❌ Workflow failed. Check logs above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
