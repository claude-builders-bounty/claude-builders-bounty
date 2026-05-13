# Claude Review Agent 🤖

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-powered pull request reviewer that uses Claude to analyze GitHub PRs and provide structured, actionable feedback.

## Features

- **CLI Tool** — Review any public/private GitHub PR from your terminal
- **GitHub Action** — Automated reviews on every PR in your repo
- **Structured Output** — Summary, risks, suggestions, and confidence score
- **Flexible Formats** — Full Markdown report or compact PR comment
- **Auto-Post** — Optionally post the review directly as a PR comment

## Quick Start

### Installation

```bash
pip install -e .
```

### Usage

```bash
# Basic review
claude-review https://github.com/owner/repo/pull/123

# Short format
claude-review owner/repo#42

# Save to file
claude-review https://github.com/org/repo/pull/1 -o review.md

# Compact comment format
claude-review https://github.com/org/repo/pull/1 --format comment

# Post directly as PR comment
claude-review https://github.com/org/repo/pull/1 --post-comment
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `GITHUB_TOKEN` | No | GitHub token for private repos and posting comments |

### Options

```
Usage: claude-review [OPTIONS] PR_URL

Options:
  --model TEXT              Claude model to use  [default: claude-sonnet-4-20250514]
  --format [full|comment]  Output format  [default: full]
  -o, --output PATH        Save output to file
  --post-comment           Post review as PR comment
  --version                Show version
  --help                   Show this message
```

## GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          claude-review \
            "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --format comment \
            --post-comment
```

## Output Example

```markdown
# 🔍 PR Review: #123

> **Add user authentication** by @developer
> https://github.com/org/repo/pull/123

---

## 📋 Summary

This PR implements JWT-based authentication with login/signup endpoints.
Code quality is good with proper error handling and input validation.

## ⚠️ Identified Risks

- No rate limiting on login endpoint — vulnerable to brute force
- JWT secret is hardcoded in config file rather than environment variable

## 💡 Improvement Suggestions

- Add rate limiting middleware (e.g., express-rate-limit)
- Move JWT_SECRET to environment variable
- Add refresh token rotation for better security

## 🎯 Confidence Score: **Medium**
```

## Architecture

```
claude_review/
├── cli.py            # Click CLI entry point
├── github_client.py  # GitHub API: fetch PR metadata + diff
├── reviewer.py       # Claude API: analyze diff, parse response
└── formatter.py      # Markdown output formatting
```

**Flow:** CLI → Parse URL → Fetch PR (GitHub API) → Analyze (Claude API) → Format → Output/Post

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"
pip install pytest

# Run tests
pytest tests/ -v
```

## License

MIT
