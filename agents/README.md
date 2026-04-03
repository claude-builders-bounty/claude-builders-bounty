# PR Review Sub-Agent

A CLI tool that reviews GitHub PRs and outputs structured analysis.

## Install

```bash
pip install pyyaml
cp agents/claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Usage

```bash
# Review a PR by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Shorthand
claude-review --pr owner/repo#123

# Markdown output
claude-review --pr owner/repo#123 --format markdown

# Local diff file
claude-review --diff ./changes.diff
```

## Output Format

```json
{
  "summary": "PR changes 3 files (+45/-12). No significant issues found.",
  "verdict": "APPROVE",
  "confidence": "High",
  "issues": [],
  "suggestions": [
    {"description": "Consider adding tests for the changed functionality"}
  ]
}
```

## GitHub Action

Included: `.github/workflows/pr-review.yml`

Automatically reviews PRs on open/sync and posts a comment.

## What It Detects

- Hardcoded secrets/credentials
- SQL injection via f-strings
- `eval()`/`exec()` usage
- `subprocess` with `shell=True`
- Debug mode in production
- Bare `except:` clauses
- Large PR warnings (>20 files)
