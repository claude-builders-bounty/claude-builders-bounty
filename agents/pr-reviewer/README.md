# PR Reviewer Agent — Claude Code Sub-Agent

> **Bounty #4 ($150)** — Structured PR review with Markdown output

A Claude Code sub-agent that reviews any GitHub PR and posts a comprehensive,
structured Markdown comment including:

- **Summary** — files changed, lines added/removed, mergeable status
- **Security Scan** — detects credential leaks, sensitive filenames
- **Issues** — oversized files, missing tests, large PR scope
- **Suggestions** — dependency verification, code organization
- **Score** — 1-10 with automatic verdict (APPROVE / REQUEST CHANGES / BLOCK)
- **Checklist** — standard review items

## Quick Install (2 commands)

```bash
# 1. Ensure gh CLI is authenticated
gh auth login

# 2. Run against any PR
python agents/pr-reviewer/pr_review.py https://github.com/owner/repo/pull/123
```

## Sample Output

See `examples/sample-review.md` for a complete review of a real PR.

## Features

| Feature | Description |
|---|---|
| PR metadata | Title, author, branch, draft status |
| File analysis | Per-file additions/deletions/status |
| Security scan | Detects .env, .pem, credentials, tokens |
| Test coverage | Warns if no test files changed |
| Scope check | Flags PRs with >15 changed files |
| Scoring | 1-10 with automatic verdict |
| Structured output | Ready to paste as a PR comment |

## Requirements

- Python 3.8+
- GitHub CLI (`gh`) authenticated
