---
name: claude-review
description: Claude Code agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.
---

# claude-review — PR Review Agent

Reviews any GitHub PR and outputs a structured Markdown review with **Summary / Risks / Suggestions / Confidence**.

## Setup (3 steps)

1. **Clone this PR** (or just copy `claude-review.py` anywhere)
2. No dependencies — pure Python 3.10+ stdlib (no `pip install`)
3. *(Optional)* Install [Claude Code CLI](https://claude.ai/cli) for deep AI-powered reviews (auto-detected at runtime)

## Usage

```bash
# Static risk scan (no API key needed, works offline)
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python claude-review.py --pr https://github.com/owner/repo/pull/456 -o review.md

# With Claude CLI (auto-detected, produces deep AI review)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --claude

# Review a local diff file
python claude-review.py --diff path/to/changes.diff
```

## Output format

```markdown
## Summary
- **PR:** [title](url) by @author (merged/open)
- **Branch:** `feature` → `main` | mergeable: clean | files: 5
- **Diff stats:** +120/-45 lines across 5 files
- **Confidence:** Medium

## Identified Risks
⚠ Hardcoded secret/credential detected: `password = 'x'`
⚠ SQL injection possible: raw string interpolation in query

## Improvement Suggestions
No test files modified — consider adding unit tests.
Large PR (600 lines) — consider splitting.

## Confidence
Medium
```

## What it detects (15+ risk patterns)

| Pattern | Risk |
|---------|------|
| `password = "..."` in source | Hardcoded credential |
| `exec()` / `child_process` | Dynamic code execution |
| `catch(e) {}` | Swallowed exception |
| `rm -rf` / `rimraf` | Destructive file operation |
| `console.log(secret)` | Sensitive data logged |
| `TODO` / `FIXME` / `HACK` | Unfinished marker |
| Raw SQL + string interpolation | Injection risk |
| No test files changed | Missing test coverage |
| PR > 500 lines | Needs splitting |

## Sample outputs

See `sample-review-auth.md` (caught TODOs, no tests) and `sample-review-profile.md` (caught `exec(rm -rf)`, `any` type, zero tests).

## GitHub Action (bonus)

Add `.github/workflows/review.yml`:

```yaml
name: claude-review
on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python claude-review.py --pr ${{ github.event.pull_request.html_url }} -o review.md
      - uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: review.md
```

## License

MIT