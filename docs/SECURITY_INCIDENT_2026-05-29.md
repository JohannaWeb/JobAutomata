# Security Incident: Gemini API Key Leak — 2026-05-29

## What happened

A Gemini API key was committed in plaintext to `RAILWAY_DEPLOYMENT.md`. The immediate
cause was well-intentioned documentation: a cleanup instruction that said "delete the
old key: `<key>`" pasted the literal value into the doc and committed it. The working
tree was scrubbed in April 2026, but the key remained in git history (commits
`e4a380c` and `88141b2`). On 2026-05-29 a review document (`docs/PRINCIPAL_REVIEW.md`)
quoted those commits verbatim, re-introducing the key into a new commit (`a929b36`).

**Root cause:** a documentation convention of "here is the thing to delete" that itself
wrote the secret into a tracked file. The lesson: when documenting a leaked credential,
never paste the literal value — reference it by prefix (e.g., `AIzaSy…`) or by the
Google AI Studio key name only.

## Affected commits (pre-remediation SHAs)

- `e4a380c` — first introduction via `RAILWAY_DEPLOYMENT.md`
- `88141b2` — key still present after file edits
- `a929b36` — re-introduced via review doc quoting the above

All three were reachable from `origin/master` and `origin/chore/fix-maintanibility-issues-phase1`.

## Remediation performed

**Date:** 2026-05-29

1. All literal occurrences of the key removed from working-tree files.
2. `git filter-repo --replace-text` run across all refs to replace the key string with
   `AIzaSy_REDACTED_FROM_HISTORY` in every historical blob.
3. Both local branches (`master`, `chore/fix-maintanibility-issues-phase1`) rewritten.
4. Origin remote re-added after filter-repo stripped it.
5. Force-push of both branches to `origin` to overwrite the public history.

## Still required (human action)

- **Rotate/revoke the key in Google AI Studio.** History rewriting does not invalidate
  the credential. Treat the key as compromised regardless of the scrub.
- **GitHub may cache blobs** from the old commits in its backend for some time even after
  force-push. If the key is not rotated, cached views or forks could still expose it.
  Rotation is the only reliable closure.
- **Notify any collaborators/forks** that history was rewritten and a force-push occurred.
  All clones must be discarded and re-cloned; a `git pull` will produce conflicts.

## Prevention

- Never paste a literal secret into a doc, commit message, or code comment — not even
  in a "this is the thing we deleted" context.
- Add `detect-secrets` or `gitleaks` as a pre-commit hook so secrets in staged files are
  rejected before they ever reach a commit.
- `.env.example` should contain only placeholder tokens (`your_key_here`), which is
  already the case in this repo.
