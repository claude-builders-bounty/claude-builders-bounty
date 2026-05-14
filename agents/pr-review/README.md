# claude-review — Claude Code PR Review Sub-agent

A zero-dependency Python CLI (and optional GitHub Action) that fetches a GitHub
PR diff, analyses it with static pattern matching, optionally enriches the
analysis with the Claude API, and returns a structured Markdown review comment.

## Quick Start

```bash
# Set your GitHub token (or use `gh auth login`)
export GITHUB_TOKEN=ghp_...

# Optional: set Anthropic key for Claude-powered narrative
export ANTHROPIC_API_KEY=sk-ant-...

# Review any public PR
python agents/pr-review/claude_review.py \
  --pr https://github.com/psf/requests/pull/7441
```

### Post the review as a comment

```bash
python agents/pr-review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment
```

### Save to a file

```bash
python agents/pr-review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

### JSON output (for programmatic use)

```bash
python agents/pr-review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --json
```

## Output format

```markdown
## 🤖 Claude Code Review

> **PR**: [PR title](url)
> **Author**: @author
> **Changes**: +N / -N across N file(s)

### 📋 Summary
2-3 sentence overview of what the PR does.

### ⚠️ Identified Risks
- [CRITICAL] `file.py:42` — Possible hardcoded credential
- [HIGH] `utils.py:17` — Bare except clause swallows all exceptions

### 💡 Improvement Suggestions
- Move secrets to environment variables or a secrets manager
- Catch specific exception types, e.g. `except ValueError:`

### 🔍 Detailed Findings
| Severity | Category       | Location      | Description              |
|----------|---------------|---------------|--------------------------|
| 🔴 CRITICAL | Security    | `config.py:5` | Possible hardcoded credential |

### ✅ Confidence: **High**
```

## GitHub Action

Add `.github/workflows/pr-review.yml` (included in this repo) to automatically
post a review comment on every PR.

```yaml
# .github/workflows/pr-review.yml  (already included)
```

Set the following repository secret:
- `ANTHROPIC_API_KEY` — optional, enables Claude-powered narrative summaries

`GITHUB_TOKEN` is provided automatically by Actions.

## Architecture

```
PR URL
  │
  ▼
GitHub API  ──── PR metadata (title, author, stats)
  │          ──── Unified diff
  │          ──── File list
  │
  ▼
Static Analysis
  ├── Security patterns  (hardcoded creds, eval, SQL injection, XSS…)
  ├── Error handling     (bare except, silent .catch…)
  └── Code quality       (TODO markers, console.log, long lines…)
  │
  ▼
Claude API (optional)
  └── Narrative summary + risks + suggestions (structured JSON)
  │
  ▼
Markdown Renderer
  └── Structured review comment
```

## Environment variables

| Variable          | Required | Description                              |
|-------------------|----------|------------------------------------------|
| `GITHUB_TOKEN`    | Yes      | GitHub personal access token (read PRs, write comments) |
| `ANTHROPIC_API_KEY` | No     | Enables Claude-powered narrative; falls back to static analysis |

## Requirements

- Python 3.9+ (zero third-party dependencies — pure stdlib)
- `gh` CLI optional (used as fallback for token retrieval)

## Sample outputs

See [`sample-outputs/`](./sample-outputs/) for real PR reviews:
- [`requests-pr-7441.md`](./sample-outputs/requests-pr-7441.md) — psf/requests PR #7441
- [`django-pr-21282.md`](./sample-outputs/django-pr-21282.md) — django/django PR #21282
