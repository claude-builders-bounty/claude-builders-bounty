## What
`claude-review` — a zero-dependency Node CLI + GitHub Action that takes a pull request (URL, or `owner/repo #N`), analyzes its diff via the public GitHub API, and emits — or posts — a structured Markdown review: summary, diff stats, risk flags, and a checklist.

## Files
- `pr-reviewer/bin/claude-review.mjs` — the CLI (Node 18+, built-in fetch, zero npm deps)
- `pr-reviewer/claude-review` / `pr-reviewer/claude-review.cmd` — POSIX + Windows wrappers
- `pr-reviewer/.github/workflows/pr-review.yml` — GitHub Action workflow
- `pr-reviewer/test/run-tests.mjs` + `test/fixtures/sample.diff` — offline test suite
- `pr-reviewer/examples/` — two live review outputs captured from real public PRs
- `pr-reviewer/README.md` — usage, env vars, AC mapping

## Usage
```bash
node bin/claude-review.mjs --pr https://github.com/expressjs/express/pull/7544
node bin/claude-review.mjs --repo expressjs/express --number 7555
node bin/claude-review.mjs --pr <url> --json
GITHUB_TOKEN=... node bin/claude-review.mjs --pr <url> --comment   # post the review as an issue comment
```

## Verification
- Offline suite: 14 passed, 0 failed (URL parsing, fixture diff analysis, required sections, confidence values, error handling)
- Live runs against real public PRs (`expressjs/express` #7544, #7555) using the unauthenticated API
- Risk heuristics flag auth/payment/config file touches, large diffs, and test deletions
- `--engine auto|claude|heuristic` switch: uses Claude via `ANTHROPIC_API_KEY` when present, falls back to a deterministic heuristic engine otherwise
- Clean rate-limit / 404 / missing-token error messages

## Acceptance criteria mapping
- Works against the public GitHub API ✓
- Structured Markdown report to stdout ✓
- `--json` machine-readable output ✓
- Graceful API error handling ✓
- `package.json` bin entry + README ✓
