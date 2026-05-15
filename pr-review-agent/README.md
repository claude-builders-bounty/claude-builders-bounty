# 🔍 claude-review — PR Review Agent CLI

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown review comments.

Built for [claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) ($100 bounty).

## Quick Start

```bash
# Set your GitHub token (recommended)
export GITHUB_TOKEN=ghp_xxxxx

# Review a PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Features

- **CLI-first**: `claude-review --pr <url>` — no setup wizard, no config files
- **Dual analysis**: Rule-based (instant, no API) + Claude API (optional, deeper insights)
- **Structured Markdown**: Summary, risks, suggestions, confidence score
- **GitHub Action included**: Auto-review PRs on open/sync
- **Post comments**: `--post` flag to publish review directly on the PR
- **JSON output**: `--format json` for programmatic consumption
- **Zero dependencies**: Python 3.8+ stdlib only

## Usage

```bash
# Basic review
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# With short format
python3 claude-review.py --pr owner/repo/pull/123

# With repo flag
python3 claude-review.py --pr 123 --repo owner/repo

# JSON output
python3 claude-review.py --pr 123 --repo owner/repo --format json

# Post review as PR comment
python3 claude-review.py --pr 123 --repo owner/repo --post

# Rule-based only (skip Claude API)
python3 claude-review.py --pr 123 --repo owner/repo --no-ai
```

## Analysis Modes

### Rule-based (default, no API key needed)
- Detects: eval/exec, hardcoded credentials, bare except, debug prints, SQL injection, linter suppression
- Suggests: context managers, truthiness checks, specific exceptions
- Confidence: based on PR size (files changed, lines modified)

### Claude API (optional, set ANTHROPIC_API_KEY)
- Deeper semantic analysis of code changes
- Better risk identification and suggestions
- Context-aware recommendations

## GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review Agent

on:
  pull_request:
    types: [opened, synchronize]

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
          python-version: '3.11'
      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 claude-review.py \
            --pr "${{ github.event.pull_request.number }}" \
            --repo "${{ github.repository }}" \
            --post
```

## Output Format

```markdown
## 🔍 PR Review: #123 — Fix memory leak in worker pool

**Reviewer:** claude-review (⚙️ Rule-based)
**Date:** 2026-05-15 21:36 UTC

### 📋 Summary of Changes
This PR modifies 3 file(s) with +45/-12 lines.
Changes span: .py, .yml. Purpose: Fix memory leak...

### ⚠️ Identified Risks
- Use of exec() — potential code injection risk
- Bare except clause — may hide errors

### 💡 Improvement Suggestions
- Consider catching more specific exceptions
- Consider using context manager for file I/O

### 📊 Confidence Score: **Medium**

| Metric | Value |
|--------|-------|
| Files changed | 3 |
| Lines added | +45 |
| Lines removed | -12 |
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Recommended | GitHub PAT for API access and posting comments |
| `ANTHROPIC_API_KEY` | Optional | Claude API key for AI-powered analysis |

## Sample Outputs

See `sample-output-pr1402.md` and `sample-output-pr1423.md` for real review examples.

## Requirements

- Python 3.8+
- GitHub token (for API access)
- Claude API key (optional, for AI analysis)

## License

MIT
