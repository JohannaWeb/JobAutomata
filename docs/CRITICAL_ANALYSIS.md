# Job Automata: Ruthless Critical Analysis

> Generated 2026-04-26. The point is not to be polite. The point is to ship something that actually works.

## TL;DR

This project is a Potemkin village. The README promises auto-applications to 300 companies with AI-generated cover letters. The reality: it opens a browser, clicks one button on the first job listing it sees, and exits. There is no form filling, no resume upload, no real automation. You wrapped a broken prototype in three different web UIs, two database backends, a Tailwind build pipeline, a Railway config, and 200 lines of orchestration code that calls `subprocess.run`. None of it adds up to a working product. The actual job-application engine is 50 lines that don't do what the docstrings claim.

You shipped scaffolding and called it a system.

---

## SECURITY (the part that should make you stop everything)

### 1. You committed an API key. It is still in the repo.
`RAILWAY_DEPLOYMENT.md` previously contained a plaintext Gemini key. The key value has been removed from the working tree, but the key must still be rotated and scrubbed from Git history with `git filter-repo` before the repo is trusted.

### 2. LinkedIn passwords on the command line.
`Makefile:80-83` reads `LinkedIn email` and `LinkedIn password` then passes them as `--email $$email --password $$password` to a Python script. Passwords on argv are visible in `ps`, `/proc`, shell history, and any logs that snapshot processes. There is no excuse for this in 2026. Use stdin, a credentials file with `0600`, or a keychain.

### 3. The dashboard has no authentication.
`web_app.py` exposes `/api/run-full`, `/api/scrape`, `/api/dry-run`, `/api/cvs/upload` with no auth, no CSRF, and `CORS(app)` set to `*`. Anyone who finds your Railway URL can:
- Trigger 1-hour subprocess invocations of Selenium (DoS)
- Upload arbitrary `.md` files (and the path-traversal check below is laughable)
- Modify your `companies.csv`
- Read your applications history

You are about to deploy a web app that lets the public spend your money and use your identity to spam recruiters. **Do not deploy this.**

### 4. Path-traversal "protection" is a one-liner that misses everything.
```python
if '..' in filename or '/' in filename:
    return error
```
This is in `cv_manager.py` and `web_app.py`. It misses: backslashes (`\`), URL-encoded `..` (`%2e%2e`), null bytes, absolute paths starting with `/etc/passwd` if the leading `/` is stripped by the framework, symlinks pointing out of the directory. Use `Path.resolve()` and check it's a child of the allowed dir. Pretending one `if` line is "security" is worse than no check, because it lets you stop thinking about it.

### 5. `subprocess.run` from HTTP handlers.
`web_app.py:209-217` shells out to `python3 url_scraper.py` from a Flask route. The arguments are hardcoded today, but the pattern is one merge away from `subprocess.run([f'python {user_input}'])`. You also block the request thread for up to **3600 seconds** waiting for the subprocess. Concurrent dashboard users will fork-bomb your Railway dyno. There is no queue. There are no workers. There is no async.

### 6. `profile.json` is committed with personal data.
Real email, real phone, real LinkedIn, real GitHub, embedded in a public repo. Even if the repo is private now, every fork and clone will preserve it. The "example_profile.json" you shipped alongside is just a copy of the real one. The convention - commit a redacted template, gitignore the real file - is a five-minute fix you skipped.

### 7. `applications_*.csv` files committed to git.
You are checking in records of which companies you applied to and when. If a recruiter ever sees this repo they will not be impressed.

---

## CORE FUNCTIONALITY (the part that doesn't actually work)

### 8. `auto_apply.py` does not auto-apply.
Read `apply_greenhouse`, `apply_lever`, `apply_workable`. Each function:
1. Loads the careers page.
2. Clicks `jobs[0]` - **the first job in the list**, regardless of role, level, location, or whether you're qualified.
3. Clicks the "Apply" button.
4. Logs success and returns.

There is **no form filling**. There is **no resume upload**. There is **no cover letter submission**. The cover letter you spend GPU cycles generating with Gemini is stored in `profile['generated_cover_letter']` and **never read again**. The "Apply" button on Greenhouse/Lever/Workable opens a multi-field form. Your code stops at the click and pretends it succeeded.

So the "300 applications" you ran would result in zero submitted applications and a CSV full of `success=True`. The dashboard's "success rate" is meaningless because every entry was a click, not a submission.

### 9. The 17/9-year split needs to be on the resume, not just in your head.
17 years programming (started 2009 at Colégio de Gaia) and 9 years professional (post-ISEP 2017) is a real, defensible split. But on the resume as written, the only date a recruiter sees is "ISEP 2017", and 17 reads as inflated against it. Add a one-line "Programming since 2009" or list the early work explicitly. Otherwise the math looks wrong even though it isn't.

### 10. The "scraper" is a hardcoded dict.
`url_scraper.py` has a hardcoded `Anthropic: https://anthropic.com` lookup. The `target-companies-300.md` is a markdown list someone typed by hand. There is no scraping. Calling it `url_scraper.py` is a marketing decision, not a technical one.

### 11. Cover letter pipeline has three competing implementations.
- `cover_letter_ai.py` (Gemini)
- `auto_apply.py:generate_cover_letter` (templates)
- `dry_run_cover_letters.py`, `dry_run_tailored_letters.py`, `dry_run_content_dump.py`, `test_personalized_letters.py`, `test_ai_letters.py` - five copy-paste variants

None of them get attached to actual applications (see #8). All of them duplicate logic. Pick one. Delete the rest.

### 12. The 3-second sleep is not rate limiting.
`time.sleep(3)` between Selenium runs is not anti-rate-limit, anti-bot, or anti-detection. Job boards fingerprint your headless Chrome by canvas, fonts, WebGL, navigator properties, and timing entropy. They will eat your IP for breakfast. Your User-Agent literally says "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" while running headless on Linux.

---

## CODE QUALITY (the part that's just embarrassing)

### 13. Half the Python files have one-space indentation.
`auto_apply.py`, `url_scraper.py`, `test_dry_run.py`, `dry_run_content_dump.py`, `cover_letter_ai.py` are formatted with single-space indents instead of 4. They run, but reading them makes your eyes bleed. PyCharm offers "Reformat Code" with `Ctrl+Alt+L`. Use it once, ever.

### 14. `main.py` is the PyCharm welcome scaffold.
```python
def print_hi(name):
    print(f'Hi, {name}')
print_hi('PyCharm')
```
You shipped this. In your repo. With a Procfile. Delete it.

### 15. `run.py` is a shell script wearing a Python costume.
240 lines of `subprocess.run` orchestration with custom step/workflow classes. This could be a `Makefile` (which already exists) or a 20-line bash script. The `JobAutomataOrchestrator` class adds zero value over a list of subprocess calls. It just makes errors harder to debug.

### 16. Three web UIs, none of them complete.
- `cv_manager.py` (stdlib `http.server`)
- `web_app.py` (Flask + SQLAlchemy + CORS)
- The legacy templates

They have overlapping endpoints (`/api/cvs`), use different storage (`profile.json` vs `.current_cv`), and disagree on which CV is currently active. Switching CV in one UI doesn't reflect in the other. Pick the Flask one, delete the stdlib one.

### 17. Database setup that doesn't run.
`web_app.py` configures `SQLALCHEMY_DATABASE_URI` defaulting to `sqlite:///jobautomata.db`. `db_init.py` only runs against PostgreSQL and is never invoked in `Procfile`, `railway.json`, or any `make` target. The `db.session.execute(text("SELECT ... FROM applications"))` query in `get_all_stats` will throw on first call because the `applications` table never gets created. The `try/except` swallows the error and returns zeros. Your dashboard reads "0 applications, 0% success" forever.

### 18. CSV as primary store, committed to git.
`companies_300.csv` is 57KB checked in. It will grow. Git diffs of CSVs are useless. Either move to a real DB or treat the CSV as build output (`.gitignore` it, regenerate on demand).

### 19. `node_modules` is not in `.gitignore`.
Your `.gitignore` has `venv/`, `__pycache__/`, `*.pyc`. It does not have `node_modules/`. You have a 76-package npm install in your Python repo. One `git add .` away from disaster.

### 20. Tailwind for one HTML file.
`package.json`, `tailwind.config.js`, `postcss`, `autoprefixer`, 76 transitive deps, a build step (`npm run build`) - all to style **one** dashboard HTML file. The CSS you actually use would fit in 200 lines of vanilla. You traded simplicity for "modern" without getting any benefit.

### 21. The `tests` are not tests.
`test_dry_run.py`, `test_ai_letters.py`, `test_personalized_letters.py` print things and exit. There are no assertions. There is no `pytest` or `unittest` runner. CI cannot tell if they pass. They are demo scripts mislabeled to look like tests so that "we have tests" is technically true.

### 22. `dry_run_content_dump.py`, `dry_run_cover_letters.py`, `dry_run_tailored_letters.py`.
Three copy-pasted scripts, each "dry running" the cover letter pipeline at slightly different verbosity. Delete two. Add a `--verbose` flag to the third.

### 23. The Makefile races the user.
`make dry-run` checks for `companies_300.csv` and uses it if present. `make apply` does the same. `make scrape` regenerates `companies_300.csv`. So the file presence drives behavior across commands invisibly. Run scrape once, forget, run again three months later, surprise: you're applying to a stale list because the cache file still exists. Make this explicit with a flag.

### 24. `applied=True` field never written back.
`auto_apply.py` reads `applied` from CSV, then writes results to a *new* timestamped CSV. The original `companies.csv` is never updated. So next run, it tries to apply to every company again. This is also why your "applications log" can show the same company 12 times.

### 25. Profile.json full of marketing copy.
`"company_alignment": { "anthropic": "Inference optimization research..." }` - hardcoded per-company "alignment" copy. None of it gets used in the actual cover letter generation (see #8 - nothing gets submitted). It's just text you wrote to feel good about. The `methodology.principles` list ("Sovereign computing stack...") is a manifesto, not a profile field.

### 26. `cv.md` instead of `cv.pdf`.
`profile["resume_file"] = "cv.md"`. No employer accepts markdown resumes. Even if the upload code worked (it doesn't), it would upload a `.md` file to a form field that expects PDF. Ship a real PDF.

---

## DEPLOYMENT (the part that's a future disaster)

### 27. Railway will run a Selenium Chrome browser inside a Docker container.
You have not configured Chrome installation in nixpacks. The build will fail or, worse, succeed and crash on first request because Chromium isn't installed. There is no `nixpacks.toml`, no `apt-get install chromium`, no `webdriver-manager`. You are deploying a Selenium app and forgot Selenium needs a browser.

### 28. `Procfile` runs `web_app:app`. There is no module exporting `app` correctly.
`web_app.py` defines `app = Flask(...)` at module level, so `gunicorn web_app:app` works. But the dashboard endpoints all assume the working directory contains `companies.csv`, `profile.json`, etc. On Railway, the deploy drops you in `/app` with no companies CSV, no profile, no API key file. First request: 404 or 500.

### 29. `instance/` and `.current_companies` and `.current_cv` and `.run_history.json`.
These are file-based state in the working directory. Railway containers are ephemeral - state will reset every deploy and possibly every container restart. You are storing user state on a filesystem that vanishes. The `db_init.py` script you wrote knows this. The `web_app.py` you actually run does not.

### 30. `DEBUG` env var read but never used to gate logging output, error pages, etc.
`debug=os.getenv('DEBUG', 'False').lower() == 'true'` controls Flask's debug mode (which exposes a Werkzeug shell to attackers). It does not control what gets logged. So in "prod" you still log full request data through Python's default logger. Fix or remove.

---

## FRAUD AND ETHICAL HAZARDS

### 31. This is application spam.
Applying to the *first job listing* at 300 companies regardless of fit is what recruiters block, what ATS systems flag, and what gets you on internal "do not hire" lists. If it actually worked (it doesn't, see #8), you would burn your reputation across the entire industry in one weekend. Even the dry-run logs say "Applied for Senior Protocol Engineer" for every company - the same generic role, regardless of what's posted.

### 32. The big claims are real - but some are time-bound.
Confirmed real and reproducible: the 51x speedup (17.96s / 5.6 tok/s -> 0.35s / 286.6 tok/s, HN post by JohannaAlmeida, 40 points, benchmarks documented), the 25.6M parameter byte-level Rust LM, the HybridAttention architecture, the codeberg repo at `JohannaJuntos/Sisyphus`. These are competitive advantages, not risks. Lead with them.

The risks left are smaller and about *phrasing*, not honesty:
- "Ranked #2 on Google for 'Hybrid Attention'" - SEO rankings drift. If a recruiter checks and you're #5 that week, the claim looks shaky even though it was true. Either drop the rank, screenshot it with a date, or rephrase: "indexed and surfaced in Google AI Overview for 'Hybrid Attention'".
- "Hacker News front page (40+ points)" - true, but "front page" implies present tense. Better: "40 points on Hacker News, front page (April 2026)" - locks the claim in time.
- "Featured in Google AI Overview" - same time-bound issue.
- "Recognized by Servo core team (Josh Matthews, Nico Burns)" - **fully verified**: Servo Zulip thread `Vendored servoshell for fun` (channel `263398-general`, message id 582403361). jdm (Josh Matthews) replied directly with "cool project!" plus substantive feedback on whether to vendor or fork servoshell. Nico Burns engaged on the wgpu-interop angle. Narfinger and webbeef also weighed in. This is a real technical exchange about your Gisberta project (github.com/JohannaWeb/Gisberta), not a passing namedrop. Link the thread on the resume.

Lock everything to a permalink (HN post URL, codeberg repo, Zulip thread, GitHub repo) and the verification works for you instead of against.

**One small thing:** Zulip lists you as "Joana Almeida", HN as "JohannaAlmeida", profile.json as "Johanna Almeida". If "Joana" is the legal/Portuguese form and "Johanna" the professional form, fine - just be consistent across the resume, GitHub, and any place a recruiter cross-references. Don't make them wonder if they're looking at two people.

### 33. LinkedIn ToS violation, deliberate.
`linkedin_hunter.py` automates login, search, and contact extraction via Selenium. LinkedIn explicitly bans this. They detect it. They will lock the account. They have sued for less (`hiQ Labs v. LinkedIn`). The README's "respect LinkedIn's ToS" disclaimer doesn't make the script not violate them.

---

## PRIORITIZED FIX LIST

If you only do ten things, do these in order:

1. **Rotate the Gemini API key. Scrub it from `RAILWAY_DEPLOYMENT.md`. `git filter-repo` to scrub from history. Force push.** (today)
2. **Delete `profile.json`, `applications_*.csv` from git. Add to `.gitignore`. Commit a redacted `example_profile.json`.** (today)
3. **Add auth to the dashboard or make it bind to localhost only.** (before any deploy)
4. **Fix `auto_apply.py` to actually fill forms - or delete the auto-apply feature and reposition the project as a "tracking + cover letter generator" tool.** (this week)
5. **Pick one web app. Delete the other two. `cv_manager.py` (stdlib HTTPServer) goes.** (this week)
6. **Reformat all Python with `black` or `ruff format`. One command. Stop shipping single-space indented Python.** (one minute)
7. **Replace CSV state with SQLite. Stop committing data files. Wire `db_init.py` into the deploy.** (a day)
8. **Add `node_modules/`, `.env`, `applications_*.csv`, `profile.json` to `.gitignore`.** (one minute)
9. **Move LinkedIn credentials off argv. Read from env or stdin.** (one hour)
10. **Delete `main.py`, the three `dry_run_*` scripts, `cv_manager.py`, the fake "test" scripts. Replace with one tested entry point.** (an afternoon)

If you do all of the above the project becomes a *small, honest, working* tool. Right now it is a large, dishonest, broken one. The size is the problem - every additional file is another thing not working.

---

## ONE-LINE VERDICT

You spent your time building the wrapper, the dashboard, the deploy config, the CV swapper, and the AI integration. You did not spend your time making the auto-applier auto-apply. Reverse that.
