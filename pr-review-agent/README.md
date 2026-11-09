# claude-review — structured PR review agent

A zero-dependency (Python standard library only) agent that reviews a
GitHub pull request and produces a structured Markdown review comment:

- **Summary of changes** (2–3 sentences: size, file mix, biggest files)
- **Identified risks** (severity-ranked: hard-coded secrets, `eval`/`exec`,
  `shell=True`, SQL string building, destructive SQL, disabled TLS/CSRF,
  plus structural risks — migrations, dependency changes, CI changes,
  auth-sensitive files, oversized or deletion-heavy PRs)
- **Improvement suggestions** (tests, SHA pinning, rollback notes, …)
- **Confidence score** — Low / Medium / High, from diff size, signal
  clarity, and truncation

The reviewer is deterministic (pattern + structure analysis), so the same
diff always yields the same review; context heuristics keep false
positives down (SQL keywords inside comments, string literals, or regex
pattern definitions in guard/linter code are reported as informational,
not as executed SQL).

## Option A — CLI

```bash
# 1. Copy claude_review.py anywhere (or clone this repo)
# 2. Review any public PR:
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

More modes:

```bash
python3 claude_review.py --pr <url> --output review.md   # write to file
python3 claude_review.py --diff pr.diff --title "My change" --url <url>
gh pr diff 123 | python3 claude_review.py                # stdin
GITHUB_TOKEN=... python3 claude_review.py --pr <url>     # private repos / higher rate limit
```

## Option B — GitHub Action

1. Copy `claude_review.py` and `.github/workflows/claude-review.yml` into
   your repository.
2. Open a pull request — the workflow posts the review as a PR comment
   and updates that same comment on every push (sticky comment).
3. That is all: it uses only the built-in `GITHUB_TOKEN`, checks out the
   **base** branch (so a PR can never modify the reviewer that grades it),
   and requests least-privilege permissions (`contents: read`,
   `pull-requests: write`).

## Tests

```bash
python3 tests/test_claude_review.py   # 9 tests, all passing
```

## Sample outputs (generated from real PRs, 2026-11-08)

- [`samples/sample-pr-5160.md`](samples/sample-pr-5160.md) — a Claude Code
  PreToolUse security hook PR; the reviewer correctly classifies the
  hook's own DROP TABLE / TRUNCATE *detection patterns* as documentation,
  not executed SQL.
- [`samples/sample-flask-pr-6168.md`](samples/sample-flask-pr-6168.md) —
  pallets/flask "drop support for Python 3.10": flags dependency and CI
  changes, an auth-sensitive file (`sessions.py`), and the deletion-heavy
  profile of the change.

## Honest limitations

- Static review only: it does not run the code or the test suite, and it
  cannot judge business logic. Treat it as a fast first pass that makes a
  human review faster, not a replacement for one.
- Very large diffs may be truncated by the GitHub API; the review says so
  and drops its confidence to Low when that happens.
