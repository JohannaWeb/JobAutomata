from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
DATABASE_DIR = PROJECT_ROOT / "database"
VAR_DIR = PROJECT_ROOT / "var"
APPLICATIONS_DIR = VAR_DIR / "applications"
CACHE_DIR = VAR_DIR / "cache"
LOG_DIR = VAR_DIR / "log"
STATE_DIR = VAR_DIR / "state"

DEFAULT_PROFILE = DATA_DIR / "profile.json"
DEFAULT_COMPANIES = DATA_DIR / "companies.csv"
DEFAULT_TARGET_COMPANIES = DATA_DIR / "target-companies-100.md"
DEFAULT_TARGET_COMPANIES_300 = DATA_DIR / "target-companies-300.md"
