# Job Automata — Principal Engineering Review

> Date: 2026-05-29. Reviewer perspective: principal-level Python.
> This is a fresh review of the current tree, not a rehash of `CRITICAL_ANALYSIS.md` (2026-04-26).
> Tone is blunt on purpose. Every finding has a file:line and a fix.

---

## Credit where it's due (what got fixed since April)

I want to be fair before I'm brutal, because a lot of the April report is now stale and you should stop worrying about those items:

- **Layered architecture is real now.** `domain / application / infrastructure / presentation` is a clean split. `JobSearchCriteria`, `Company`, the job-board `Protocol` + registry — this is genuinely good structure for a project this size.
- **Indentation/formatting fixed.** 4-space, consistent. The "single-space Python" complaint is gone.
- **Path traversal is handled properly.** `safe_child_path()` (`app.py:166`) uses `secure_filename` + `resolve()` + parent check. That's the correct pattern, not the old one-liner.
- **Credentials off argv.** `Makefile` reads `LINKEDIN_EMAIL/PASSWORD` from env; the hunter takes them from env, not `--password`.
- **`profile.json` and `applications_*.csv` are no longer tracked.** `.gitignore` covers them. Good.
- **Dashboard has an auth layer** (`require_local_or_token`) and a real autofill engine (`infrastructure/ats/autofill.py`) with human-in-the-loop confirmation. The "it pretends to apply" criticism is no longer accurate — the `--pause-each` flow is an honest design.
- **Dockerfile installs Chromium.** The "you forgot the browser" problem is fixed.

So the bones are better. The problems now are sharper and more specific. Several are **regressions or things April flagged that were never actually remediated.**

---

## P0 — Stop and fix today

### P0.1 The leaked Gemini key is STILL in git history
April flagged this. The working tree was scrubbed; **history was not.** It's right here:

```
e49db9a:RAILWAY_DEPLOYMENT.md:  Delete the old key: `AIzaSy_REDACTED_FROM_HISTORY`
e4a380c:RAILWAY_DEPLOYMENT.md:  Delete the old key: `AIzaSy_REDACTED_FROM_HISTORY`
```

Anyone who clones the repo gets the key with `git log -p`. "We deleted it from the file" is not remediation when the value lives in two reachable commits.

**Fix (today, in order):**
1. Rotate the key in Google AI Studio. Assume it is compromised — it has been public in history for a month.
2. `git filter-repo --replace-text <(echo 'AIzaSy_REDACTED_FROM_HISTORY==>REDACTED')` (or BFG).
3. Force-push, and have every collaborator re-clone. **Confirm with whoever owns the remote before force-pushing** — it rewrites history for everyone.

A leaked-but-rotated key is a non-event. A leaked-and-still-valid key is a billing/abuse incident waiting to happen.

### P0.2 Dashboard auth bypass via `X-Forwarded-For`
`app.py:103`:

```python
remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
if remote_addr in LOCAL_ADDRESSES:
    return None
```

When `DASHBOARD_TOKEN` is unset (the default — `make dashboard` passes an empty token), the "local-only" gate trusts a **client-supplied header**. Any remote attacker sends `X-Forwarded-For: 127.0.0.1` and is treated as local. Now combine that with `make dashboard` defaulting `ENABLE_DANGEROUS_AUTOMATION=true` (Makefile) and the bypass reaches `/api/scrape`, `/api/run-full` (spawns Selenium subprocesses), `/api/companies/update`, and `/api/cvs/upload`.

`X-Forwarded-For` is set by *the client* unless a trusted proxy overwrites it. You can't use it for an auth decision.

**Fix:**
- Never derive "is local" from XFF. Use `request.remote_addr` only, and only after putting Flask behind `ProxyFix` with a known trusted-proxy count if you're behind Railway's LB.
- Better: **fail closed.** Require `DASHBOARD_TOKEN` in any non-loopback bind. If the socket peer isn't loopback and no token is configured, return 403 — don't fall back to a spoofable header.

### P0.3 No `.dockerignore` + `COPY . .` ships your secrets and `venv/`
`Dockerfile:20` is `COPY . .` and there is no `.dockerignore`. That means the image bakes in:
- `.git/` — **including the leaked key from P0.1, in every image layer**
- `venv/` — ~500k LOC of vendored site-packages (idna, sqlalchemy, selenium devtools…), making the image enormous and the `pip install` above it pointless
- `.env` if one exists locally
- `node_modules/`

**Fix:** add `.dockerignore`:
```
.git
venv
node_modules
.env
__pycache__
*.pyc
var/
.idea
```
This shrinks the image, speeds builds, and stops secret-bearing layers.

---

## P1 — The headline features don't actually run

### P1.1 AI cover letters are a dead code path
`auto_apply.py:33`:

```python
try:
    from cover_letter_ai import generate_cover_letter_ai
except ImportError:
    generate_cover_letter_ai = None
```

That's a **bare top-level module name**. There is no top-level `cover_letter_ai` module — the real one is `job_automata.application.cover_letter_ai`. Confirmed:

```
$ python3 -c "import cover_letter_ai"
ModuleNotFoundError: No module named 'cover_letter_ai'
```

So when you run `python -m job_automata.application.auto_apply`, `generate_cover_letter_ai` is **always `None`**, the `try` in `generate_cover_letter()` is skipped, and you silently fall back to string templates. The README's #1 feature ("AI-Generated Cover Letters: Uses Google Gemini Flash") **never executes in the packaged path.** You're paying for Gemini in your head and shipping `"I'm interested in joining {company_name}…"`.

**Fix:** `from job_automata.application.cover_letter_ai import generate_cover_letter_ai`. Then add a test that asserts the AI path is reachable (mock the genai client) so this can't silently rot again.

### P1.2 LinkedIn hunter throws on every result
`hunter.py:149` and `:152`:

```python
name = name_elem.get_text().strip()
title = title_elem.get_text().strip()
```

`get_text()` is a **BeautifulSoup** method. These are Selenium `WebElement`s, which expose `.text`, not `.get_text()`. Every iteration raises `AttributeError`, gets swallowed by the `except` at `:170`, logs "Error parsing result", and continues. Net result: `search_company_managers` returns `[]` for every company. The feature is dead on arrival, independent of the LinkedIn-ToS problem.

**Fix:** use `name_elem.text` / `title_elem.text`. But honestly — see P3.1, this whole module is a liability.

### P1.3 Cover letter is generated twice per company
In a non-dry-run, `generate_cover_letter()` is called at `auto_apply.py:438` (in `run`) **and** again at `:372` (inside `apply_company`). The first result is discarded. When P1.1 is fixed, that's **two Gemini calls per company** — double the cost, double the latency, double the log lines, for a value you throw away.

**Fix:** generate once in `run`, pass the string into `apply_company(driver, company, profile, cover_letter)`. Delete the call at `:372`.

---

## P2 — Deploy-time correctness

### P2.1 The database is decorative
`app.py:71` constructs `db = SQLAlchemy(app)`, and `get_all_stats()` (`app.py:209`) queries `applications` **only** when the URL contains `postgresql`/`mysql`. But:
- `database/init.py` (schema creation + CSV migration) is **never invoked** by `Dockerfile`, `Procfile`, or `railway.json`.
- So on Railway-with-Postgres the `applications` table doesn't exist, the `SELECT` throws, the bare `except` at `:249` swallows it, and the dashboard reports **0 applications / 0% forever.**
- On SQLite/local it never touches the DB at all and reads CSVs.

You have a DB layer that is wired to nothing. Either make it real or delete it.

**Fix:** if you want the DB, run `python -m job_automata.infrastructure.database.init` in the container `CMD`/release step and make `get_all_stats` actually depend on it. If you don't, rip out SQLAlchemy + `database/` and own that this is a CSV/file tool.

### P2.2 Prometheus metrics are wrong under gunicorn
`app.py:40-65` defines module-level `Counter/Histogram/Gauge`. `Procfile`/`Dockerfile` run gunicorn with `--workers 2`. Each worker has its own process-local registry, so `/metrics` returns **whichever worker the scrape happened to hit** — request counts and the application gauges will flap between two unrelated views. This isn't observability, it's noise.

**Fix:** either run a single worker for the metrics to be meaningful, or set up `prometheus_client` multiprocess mode (`PROMETHEUS_MULTIPROC_DIR` + `MultiProcessCollector` in the `/metrics` handler). If you don't need metrics, drop the dependency — right now it's unpinned in `docs/requirements.txt` too.

### P2.3 Ephemeral filesystem state on Railway
`var/state/current_cv`, `current_companies`, `run_history.json` are file-based state in the container FS. Railway containers are ephemeral; this resets on every deploy/restart. The committed `var/state/*` files (they're tracked!) will also overwrite real state on each deploy. This is the same gap as April #29 and it's still here.

**Fix:** move this state into the Postgres you already provisioned (the `config`/`run_history` tables in `schema.sql` exist for exactly this), and `git rm --cached var/state/*`.

---

## P3 — Design and maintainability

### P3.1 The LinkedIn hunter should be deleted, not fixed
Even after P1.2, this module (a) automates LinkedIn login + scraping, which is a flat ToS violation they actively detect and litigate (`hiQ` notwithstanding), (b) hardcodes a `linkedin_session.json` path in CWD, and (c) is built on class-name selectors (`base-search-card`, `sub-header-line`) that LinkedIn rotates constantly. It will get the account locked and it will break weekly. The honest move is to remove it and, if you want hiring-manager data, use a sanctioned source.

### P3.2 Personal business logic is hardcoded and duplicated
The "block Google" rule lives in **two** places — `auto_apply.py:49-76` and `url_scraper.py:158-181` — with copy-pasted `BLOCKED_DOMAINS` tuples. And `"google" in company.name.casefold()` (`auto_apply.py:66`) over-matches (any name containing "google"). A personal do-not-apply filter shouldn't be hardcoded into shipped library code in two spots.

**Fix:** one source of truth — a config/env list (`BLOCKED_COMPANIES`, `BLOCKED_DOMAINS`) loaded once, consumed by both modules. Match on exact name/host, not substring.

### P3.3 `--headless` is a no-op flag
`auto_apply.py:585`: `--headless` has `default=True` with no inverse, and `__init__` computes `headless = headless and not pause_each` (`:86`). There is no way to run headed except via `--pause-each`. A flag that can't be turned off is a lie in `--help`.

**Fix:** `--headless` with `action=argparse.BooleanOptionalAction` (gives you `--no-headless`), default True.

### P3.4 `url_scraper.py` is mostly a hardcoded dict
`KNOWN_URLS` (`:39-134`) is ~95 hand-typed domains. The actual `guess_domain` fallback just probes `name.com/.io/.ai`. That's fine as a heuristic, but calling the module a "scraper" oversells it — and the dict is unmaintainable as the company list grows. Consider a data file (`data/known_domains.json`) instead of a literal in source, so non-engineers can edit it and you can diff it cleanly.

### P3.5 Two web servers still coexist
`presentation/web/app.py` (Flask, the real one) and `presentation/web/cv_manager.py` (stdlib `http.server`, marked "deprecated" in the Makefile) both exist with overlapping `/api/cv*` surface and **different** path-handling code. The stdlib one is dead weight and a second, weaker security surface. Delete `cv_manager.py` and its Makefile targets.

---

## P4 — Hygiene (low effort, do in a batch)

- **`requirements.txt` lives in `docs/`.** Tools expect it at the repo root; `Dockerfile:17` copies `docs/requirements.txt`, which works but surprises everyone. Move it to root (or adopt `pyproject.toml`). Pin `prometheus-client` — it's the only unpinned dep.
- **Token via URL query param** (`app.py:95`, `?token=`) leaks into access logs, browser history, and `Referer`. Drop the query-param path; header/bearer only.
- **Token compared with `==`** (`app.py:99`). Use `hmac.compare_digest` to avoid the timing side-channel. Minor, but you're a security-adjacent candidate showing this code to security-adjacent companies.
- **Inconsistent Selenium error handling.** `greenhouse.py` catches `TimeoutException` around its waits; `lever.py:21` and `workable.py:21` don't, so a slow/changed page throws straight out. Make them consistent.
- **User-Agent says Windows while running headless Linux** (`auto_apply.py:100`, `hunter.py:80`). Trivial bot tell. Either match reality or don't bother spoofing.
- **PII still tracked:** `data/cv.pdf` is your real resume in the repo. That may be intentional, but know that it's permanent once pushed. `var/state/*` likewise shouldn't be tracked.

---

## Testing — the gap that would have caught half of this

You have exactly two real test files (`tests/test_job_search.py`, `tests/test_auto_apply_profile.py`). They're good — real asserts, `tmp_path` fixtures. But:
- The `scripts/test_*.py` files are demo scripts with no assertions. Don't name them `test_` — `pytest` will try to collect them.
- **There is no test for anything that's actually broken above.** A single test importing `generate_cover_letter_ai` through the real path would have caught P1.1. A test hitting `/api/stats` with `X-Forwarded-For: 1.2.3.4` would have caught P0.2. A test on `autofill._classify` would lock in the field-matching behavior that's the core value of the tool now.

**Highest-leverage tests to add:** (1) AI cover-letter path reachability (mock genai), (2) dashboard auth — assert a spoofed XFF is rejected, (3) `autofill._classify` / `_classify_with_type` table-driven cases.

---

## Prioritized punch list

| # | Severity | Item | Effort |
|---|----------|------|--------|
| 1 | P0 | Rotate Gemini key + scrub from git history | hours |
| 2 | P0 | Fix XFF auth bypass; fail closed without token | hours |
| 3 | P0 | Add `.dockerignore` | minutes |
| 4 | P1 | Fix AI cover-letter import (`job_automata.application.cover_letter_ai`) | minutes |
| 5 | P1 | Fix `WebElement.text` in hunter (or delete hunter) | minutes |
| 6 | P1 | Generate cover letter once, not twice | minutes |
| 7 | P2 | Make the DB real (wire `database/init`) or delete it | half day |
| 8 | P2 | Fix or remove Prometheus multiprocess metrics | hours |
| 9 | P2 | Move runtime state to DB; untrack `var/state/*` | hours |
| 10 | P3 | Delete LinkedIn hunter + stdlib `cv_manager.py` | hours |
| 11 | P3 | De-dupe blocklist into config; fix `--headless` flag | hours |
| 12 | P4 | requirements to root, constant-time token, drop `?token=`, `.dockerignore`, UA | batch, ~1hr |

---

## One-line verdict

The skeleton is now solid and the autofill-with-human-confirmation design is honest — but your two headline features (AI cover letters, LinkedIn hunting) are **silently dead due to import/API bugs**, the dashboard has a real auth bypass, and the month-old leaked key is still in history. Fix the four one-line bugs first (P0.3, P1.1, P1.2, P1.3) — they're minutes of work and they turn "looks impressive, does nothing" into "actually works." Then close the two security holes. Everything else is cleanup.
